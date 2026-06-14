"""
Reporting Service — Insight & Reporting Layer

Consumes AlignmentResult data (read-only) to generate mismatch reports,
project health metrics, and executive summaries.

Groq is used ONLY for narrative text generation — NEVER for scoring or status determination.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.alignment_result import AlignmentResult
from app.models.mismatch_report import MismatchReport
from app.models.project import Project
from app.models.requirement import Requirement
from app.models.requirement_version import RequirementVersion
from app.schemas.mismatch_report import MismatchReportCreate
from app.repositories.mismatch_report_repository import mismatch_report_repo

logger = logging.getLogger(__name__)


def _severity_from_score(score: int) -> str:
    """Derive severity from overall alignment score. Deterministic — no AI."""
    if score < 30:
        return "Critical"
    elif score < 50:
        return "High"
    elif score < 75:
        return "Medium"
    return "Low"


def _mismatch_type_from_scores(
    req_jira: Optional[int],
    jira_pr: Optional[int],
    pr_artifact: Optional[int],
) -> str:
    """Identify which chain link has the lowest score (biggest gap)."""
    scores = {}
    if req_jira is not None:
        scores["requirement_jira_gap"] = req_jira
    if jira_pr is not None:
        scores["jira_pr_gap"] = jira_pr
    if pr_artifact is not None:
        scores["pr_artifact_gap"] = pr_artifact

    if not scores:
        return "missing_implementation"

    return min(scores, key=scores.get)


def _auto_description(
    mismatch_type: str,
    overall_score: int,
    alignment_status: str,
    req_jira: Optional[int],
    jira_pr: Optional[int],
    pr_artifact: Optional[int],
) -> str:
    """Auto-generate a human-readable summary of the gap."""
    label_map = {
        "requirement_jira_gap": "Requirement → Jira Story",
        "jira_pr_gap": "Jira Story → Pull Request",
        "pr_artifact_gap": "Pull Request → Code Artifact",
        "missing_implementation": "Implementation chain",
    }
    link_label = label_map.get(mismatch_type, mismatch_type)

    parts = [
        f"Alignment status: {alignment_status} (overall score: {overall_score}%).",
        f"Weakest chain link: {link_label}.",
    ]
    if req_jira is not None:
        parts.append(f"Requirement→Jira: {req_jira}%.")
    if jira_pr is not None:
        parts.append(f"Jira→PR: {jira_pr}%.")
    if pr_artifact is not None:
        parts.append(f"PR→Artifact: {pr_artifact}%.")

    return " ".join(parts)


def _auto_suggested_fix(mismatch_type: str, severity: str) -> str:
    """Generate a brief recommendation based on the gap type."""
    fixes = {
        "requirement_jira_gap": "Review Jira stories to ensure they accurately reflect the approved requirements. Consider creating new stories or updating existing ones.",
        "jira_pr_gap": "Verify that pull requests address the Jira stories they are linked to. Check for missing PR descriptions or incorrect branch mappings.",
        "pr_artifact_gap": "Inspect code artifacts extracted from pull requests. Ensure functions, classes, and endpoints match the PR scope.",
        "missing_implementation": "No implementation evidence found. Create Jira stories, PRs, and code artifacts to trace back to this requirement.",
    }
    fix = fixes.get(mismatch_type, "Investigate the alignment gap and update the relevant artifacts.")

    if severity == "Critical":
        fix = f"[URGENT] {fix}"
    elif severity == "High":
        fix = f"[HIGH PRIORITY] {fix}"

    return fix


class ReportingService:
    """Read-only consumer of alignment results for insight generation."""

    # ──────────────────────────────────────────────────────────────────────
    # Generate Mismatch Reports
    # ──────────────────────────────────────────────────────────────────────

    async def generate_mismatch_reports(
        self,
        db: AsyncSession,
        project_id: UUID,
        current_user_id: UUID,
    ) -> List[MismatchReport]:
        """
        Query all AlignmentResults for the project where alignment_status != 'Aligned'.
        Create/update MismatchReport records for each.
        """
        # Fetch non-aligned results
        stmt = select(AlignmentResult).where(
            AlignmentResult.project_id == project_id,
            AlignmentResult.is_deleted == False,
            AlignmentResult.alignment_status != "Aligned",
        )
        result = await db.execute(stmt)
        misaligned_results: List[AlignmentResult] = list(result.scalars().all())

        if not misaligned_results:
            logger.info(f"No misaligned results found for project {project_id}")
            return []

        # Fetch existing mismatch reports keyed by alignment_result_id
        stmt = select(MismatchReport).where(
            MismatchReport.project_id == project_id,
            MismatchReport.is_deleted == False,
        )
        result = await db.execute(stmt)
        existing_reports = {
            r.alignment_result_id: r for r in result.scalars().all()
        }

        created_reports: List[MismatchReport] = []

        for ar in misaligned_results:
            mismatch_type = _mismatch_type_from_scores(
                ar.requirement_jira_score,
                ar.jira_pr_score,
                ar.pr_artifact_score,
            )
            severity = _severity_from_score(ar.overall_alignment_score)
            description = _auto_description(
                mismatch_type,
                ar.overall_alignment_score,
                ar.alignment_status,
                ar.requirement_jira_score,
                ar.jira_pr_score,
                ar.pr_artifact_score,
            )
            suggested_fix = _auto_suggested_fix(mismatch_type, severity)

            if ar.id in existing_reports:
                # Update existing report
                existing = existing_reports[ar.id]
                existing.mismatch_type = mismatch_type
                existing.description = description
                existing.suggested_fix = suggested_fix
                existing.severity = severity
                existing.updated_by_id = current_user_id
                db.add(existing)
                created_reports.append(existing)
            else:
                # Create new report
                report_in = MismatchReportCreate(
                    project_id=project_id,
                    alignment_result_id=ar.id,
                    mismatch_type=mismatch_type,
                    description=description,
                    suggested_fix=suggested_fix,
                    status="Open",
                    severity=severity,
                )
                report = await mismatch_report_repo.create(
                    db=db, obj_in=report_in, created_by_id=current_user_id
                )
                created_reports.append(report)

        await db.commit()
        logger.info(f"Generated {len(created_reports)} mismatch reports for project {project_id}")
        return created_reports

    # ──────────────────────────────────────────────────────────────────────
    # Project Health Score
    # ──────────────────────────────────────────────────────────────────────

    async def get_project_health(
        self,
        db: AsyncSession,
        project_id: UUID,
    ) -> Dict[str, Any]:
        """
        Returns a project health dict with weighted health score.
        All scoring is deterministic — Groq is NOT used here.
        """
        # Alignment results
        stmt = select(AlignmentResult).where(
            AlignmentResult.project_id == project_id,
            AlignmentResult.is_deleted == False,
        )
        result = await db.execute(stmt)
        alignment_results: List[AlignmentResult] = list(result.scalars().all())

        total_alignments = len(alignment_results)
        aligned_count = sum(1 for a in alignment_results if a.alignment_status == "Aligned")
        drift_count = sum(1 for a in alignment_results if a.alignment_status == "Potential Drift")
        misaligned_count = sum(1 for a in alignment_results if a.alignment_status == "Misaligned")
        avg_alignment_score = (
            round(sum(a.overall_alignment_score for a in alignment_results) / total_alignments)
            if total_alignments > 0 else 0
        )
        drift_percentage = (
            round(((drift_count + misaligned_count) / total_alignments) * 100, 1)
            if total_alignments > 0 else 0.0
        )

        # Requirement approval ratio
        stmt = (
            select(RequirementVersion)
            .join(RequirementVersion.requirement)
            .where(
                Requirement.project_id == project_id,
                Requirement.is_deleted == False,
                RequirementVersion.is_deleted == False,
            )
        )
        result = await db.execute(stmt)
        all_versions: List[RequirementVersion] = list(result.scalars().all())
        total_requirements = len(all_versions)
        approved_requirements = sum(
            1 for v in all_versions if v.status == "Approved"
        )
        approval_ratio = (
            approved_requirements / total_requirements
            if total_requirements > 0 else 0
        )

        # Mismatch reports
        stmt = select(MismatchReport).where(
            MismatchReport.project_id == project_id,
            MismatchReport.is_deleted == False,
        )
        result = await db.execute(stmt)
        mismatch_reports: List[MismatchReport] = list(result.scalars().all())
        open_mismatches = sum(1 for m in mismatch_reports if m.status == "Open")
        resolved_mismatches = sum(1 for m in mismatch_reports if m.status == "Resolved")

        # Health score formula (0-100):
        #   alignment_scores (50%) + open_mismatches_penalty (20%) +
        #   approval_ratio (15%) + drift_penalty (15%)
        alignment_component = avg_alignment_score * 0.50

        open_mismatch_penalty = 0.0
        if total_alignments > 0:
            open_ratio = min(open_mismatches / max(total_alignments, 1), 1.0)
            open_mismatch_penalty = (1.0 - open_ratio) * 100 * 0.20
        else:
            open_mismatch_penalty = 100 * 0.20  # No alignments = no penalty

        approval_component = approval_ratio * 100 * 0.15

        drift_penalty_component = 0.0
        if total_alignments > 0:
            drift_ratio = (drift_count + misaligned_count) / total_alignments
            drift_penalty_component = (1.0 - drift_ratio) * 100 * 0.15
        else:
            drift_penalty_component = 100 * 0.15

        health_score = round(
            alignment_component + open_mismatch_penalty + approval_component + drift_penalty_component
        )
        health_score = max(0, min(100, health_score))

        if health_score >= 85:
            health_status = "Excellent"
        elif health_score >= 70:
            health_status = "Good"
        elif health_score >= 50:
            health_status = "Needs Attention"
        else:
            health_status = "Critical"

        return {
            "health_score": health_score,
            "health_status": health_status,
            "total_requirements": total_requirements,
            "approved_requirements": approved_requirements,
            "aligned_count": aligned_count,
            "drift_count": drift_count,
            "misaligned_count": misaligned_count,
            "open_mismatches": open_mismatches,
            "resolved_mismatches": resolved_mismatches,
            "avg_alignment_score": avg_alignment_score,
            "drift_percentage": drift_percentage,
        }

    # ──────────────────────────────────────────────────────────────────────
    # Executive Report
    # ──────────────────────────────────────────────────────────────────────

    async def generate_executive_report(
        self,
        db: AsyncSession,
        project_id: UUID,
    ) -> Dict[str, Any]:
        """
        Generate executive-level project report.
        Groq is used ONLY for narrative text — never for scoring.
        """
        # Project info
        stmt = select(Project).where(Project.id == project_id, Project.is_deleted == False)
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()
        if not project:
            return {"error": "Project not found"}

        project_summary = {
            "name": project.name,
            "client_name": project.client_name,
            "status": project.status,
            "created_at": str(project.created_at),
            "updated_at": str(project.updated_at),
        }

        # Alignment overview
        stmt = select(AlignmentResult).where(
            AlignmentResult.project_id == project_id,
            AlignmentResult.is_deleted == False,
        )
        result = await db.execute(stmt)
        alignment_results: List[AlignmentResult] = list(result.scalars().all())
        total = len(alignment_results)
        avg_score = (
            round(sum(a.overall_alignment_score for a in alignment_results) / total)
            if total > 0 else 0
        )

        status_distribution = {}
        for ar in alignment_results:
            status_distribution[ar.alignment_status] = status_distribution.get(ar.alignment_status, 0) + 1

        alignment_overview = {
            "total_results": total,
            "avg_alignment_score": avg_score,
            "status_distribution": status_distribution,
        }

        # Top risks — misaligned/drift items ordered by severity
        stmt = (
            select(MismatchReport)
            .where(
                MismatchReport.project_id == project_id,
                MismatchReport.is_deleted == False,
                MismatchReport.status != "Resolved",
            )
        )
        result = await db.execute(stmt)
        mismatch_reports: List[MismatchReport] = list(result.scalars().all())

        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        mismatch_reports.sort(key=lambda m: severity_order.get(m.severity, 99))

        top_risks = [
            {
                "id": str(m.id),
                "mismatch_type": m.mismatch_type,
                "severity": m.severity,
                "status": m.status,
                "description": m.description,
                "suggested_fix": m.suggested_fix,
            }
            for m in mismatch_reports[:10]  # Top 10 risks
        ]

        # Health
        health = await self.get_project_health(db, project_id)

        # Groq-generated narrative (ONLY for text, not scoring)
        narrative = await self._generate_narrative(project_summary, alignment_overview, health, top_risks)
        recommendations = await self._generate_recommendations(project_summary, health, top_risks)

        return {
            "project_summary": project_summary,
            "alignment_overview": alignment_overview,
            "top_risks": top_risks,
            "health": health,
            "narrative": narrative,
            "recommendations": recommendations,
        }

    # ──────────────────────────────────────────────────────────────────────
    # Private: Groq narrative generation (text only, no scoring)
    # ──────────────────────────────────────────────────────────────────────

    async def _generate_narrative(
        self,
        project_summary: Dict[str, Any],
        alignment_overview: Dict[str, Any],
        health: Dict[str, Any],
        top_risks: List[Dict[str, Any]],
    ) -> str:
        """Generate a management-friendly narrative summary using Groq."""
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            return (
                f"Project '{project_summary.get('name', 'N/A')}' has a health score of "
                f"{health.get('health_score', 'N/A')}% ({health.get('health_status', 'N/A')}). "
                f"There are {alignment_overview.get('total_results', 0)} alignment results with "
                f"an average score of {alignment_overview.get('avg_alignment_score', 0)}%. "
                f"{health.get('open_mismatches', 0)} open mismatches require attention. "
                f"(Enable GROQ_API_KEY for AI-generated executive narrative.)"
            )

        try:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=api_key)

            risk_summary = ""
            if top_risks:
                risk_lines = [f"- [{r['severity']}] {r['mismatch_type']}: {r['description'][:100]}" for r in top_risks[:5]]
                risk_summary = "\n".join(risk_lines)

            prompt = f"""You are a senior engineering manager writing an executive project status report.
Write a 2-3 paragraph management summary for the following project alignment data.

Project: {project_summary.get('name', 'N/A')} (Client: {project_summary.get('client_name', 'N/A')})
Health Score: {health.get('health_score')}% ({health.get('health_status')})
Alignment Results: {alignment_overview.get('total_results', 0)} total, avg score {alignment_overview.get('avg_alignment_score', 0)}%
Distribution: {alignment_overview.get('status_distribution', {})}
Open Mismatches: {health.get('open_mismatches', 0)}
Resolved Mismatches: {health.get('resolved_mismatches', 0)}
Requirements: {health.get('total_requirements', 0)} total, {health.get('approved_requirements', 0)} approved

Top Risks:
{risk_summary if risk_summary else 'No critical risks identified.'}

Write professionally. Focus on impact, trends, and actionable insights. Do NOT invent scores or metrics — only reference the data above."""

            response = await client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-70b-8192",
                temperature=0.3,
                max_tokens=500,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            logger.warning(f"Groq narrative generation failed: {exc}")
            return (
                f"Project '{project_summary.get('name', 'N/A')}' health: "
                f"{health.get('health_score', 'N/A')}% ({health.get('health_status', 'N/A')}). "
                f"(AI narrative unavailable.)"
            )

    async def _generate_recommendations(
        self,
        project_summary: Dict[str, Any],
        health: Dict[str, Any],
        top_risks: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate actionable recommendations using Groq."""
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            # Deterministic fallback recommendations
            recommendations = []
            if health.get("open_mismatches", 0) > 0:
                recommendations.append(f"Review and resolve {health['open_mismatches']} open mismatch reports.")
            if health.get("health_score", 100) < 70:
                recommendations.append("Conduct a team alignment review to address drift in implementation traceability.")
            if health.get("drift_percentage", 0) > 25:
                recommendations.append("Prioritize re-alignment of drifted requirements with their implementation artifacts.")
            if health.get("approved_requirements", 0) < health.get("total_requirements", 0):
                unapproved = health.get("total_requirements", 0) - health.get("approved_requirements", 0)
                recommendations.append(f"Expedite approval for {unapproved} pending requirement versions.")
            if not recommendations:
                recommendations.append("Project is in good health. Continue monitoring alignment metrics.")
            return recommendations

        try:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=api_key)

            risk_summary = ""
            if top_risks:
                risk_lines = [f"- [{r['severity']}] {r['mismatch_type']}: {r['description'][:80]}" for r in top_risks[:5]]
                risk_summary = "\n".join(risk_lines)

            prompt = f"""Based on this project alignment data, provide 3-5 specific, actionable recommendations for the engineering team.

Project: {project_summary.get('name', 'N/A')}
Health Score: {health.get('health_score')}% ({health.get('health_status')})
Open Mismatches: {health.get('open_mismatches', 0)}
Drift Percentage: {health.get('drift_percentage', 0)}%
Requirements: {health.get('total_requirements', 0)} total, {health.get('approved_requirements', 0)} approved

Top Risks:
{risk_summary if risk_summary else 'None identified.'}

Return each recommendation on its own line, starting with a number and period (e.g., "1. Do X").
Be specific and actionable. Do NOT invent data not provided above."""

            response = await client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-70b-8192",
                temperature=0.3,
                max_tokens=400,
            )
            raw = response.choices[0].message.content.strip()
            lines = [line.strip() for line in raw.split("\n") if line.strip()]
            # Clean up numbered prefixes
            cleaned = []
            for line in lines:
                # Remove leading "1. ", "2. " etc.
                if len(line) > 2 and line[0].isdigit() and line[1] == '.':
                    cleaned.append(line[2:].strip())
                elif len(line) > 3 and line[:2].isdigit() and line[2] == '.':
                    cleaned.append(line[3:].strip())
                else:
                    cleaned.append(line)
            return cleaned if cleaned else ["No specific recommendations generated."]
        except Exception as exc:
            logger.warning(f"Groq recommendations generation failed: {exc}")
            return ["Review open mismatch reports and address critical alignment gaps. (AI recommendations unavailable.)"]


reporting_service = ReportingService()
