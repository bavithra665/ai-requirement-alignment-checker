from typing import Dict, Any, List
from uuid import UUID
from django.db.models import Avg, Count
from projects.models import Project, Requirement, RequirementVersion
from integrations.models import JiraStory, PullRequest, CodeArtifact
from alignment.models import AlignmentResult
from .models import MismatchReport

class ReportingService:
    def get_project_health(self, project_id: UUID) -> Dict[str, Any]:
        results = AlignmentResult.objects.filter(project_id=project_id, is_deleted=False)
        total_results = results.count()
        
        aligned_count = results.filter(alignment_status="Aligned").count()
        drift_count = results.filter(alignment_status="Potential Drift").count()
        misaligned_count = results.filter(alignment_status="Misaligned").count()
        
        avg_score = results.aggregate(Avg('overall_alignment_score'))['overall_alignment_score__avg'] or 0
        drift_percentage = (
            round(((drift_count + misaligned_count) / total_results) * 100, 1)
            if total_results > 0 else 0.0
        )
        
        # Requirement approval ratio
        versions = RequirementVersion.objects.filter(
            requirement__project_id=project_id,
            is_deleted=False,
            requirement__is_deleted=False
        )
        total_requirements = versions.count()
        approved_requirements = versions.filter(status="Approved").count()
        
        # Mismatch reports
        mismatch_reports = MismatchReport.objects.filter(project_id=project_id, is_deleted=False)
        open_mismatches = mismatch_reports.filter(status="Open").count()
        resolved_mismatches = mismatch_reports.filter(status="Resolved").count()
        
        # Health score formula (0-100):
        #   alignment_scores (50%) + open_mismatches_penalty (20%) +
        #   approval_ratio (15%) + drift_penalty (15%)
        alignment_component = avg_score * 0.50
        
        open_mismatch_penalty = 0.0
        if total_results > 0:
            open_ratio = min(open_mismatches / max(total_results, 1), 1.0)
            open_mismatch_penalty = (1.0 - open_ratio) * 100 * 0.20
        else:
            open_mismatch_penalty = 100 * 0.20  # No alignments = no penalty
            
        approval_ratio = approved_requirements / total_requirements if total_requirements > 0 else 0.0
        approval_component = approval_ratio * 100 * 0.15
        
        drift_penalty_component = 0.0
        if total_results > 0:
            drift_ratio = (drift_count + misaligned_count) / total_results
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
            "avg_alignment_score": round(avg_score),
            "drift_percentage": drift_percentage,
        }

    def get_risk_dashboard(self, project_id: UUID) -> Dict[str, Any]:
        # Return the full health metrics to match frontend ProjectHealth interface
        return self.get_project_health(project_id)

    def get_executive_summary(self, project_id: UUID) -> Dict[str, Any]:
        project = Project.objects.get(id=project_id)
        
        # Alignment Results
        results = AlignmentResult.objects.filter(project_id=project_id, is_deleted=False)
        total_results = results.count()
        
        aligned = results.filter(alignment_status="Aligned").count()
        drift = results.filter(alignment_status="Potential Drift").count()
        misaligned = results.filter(alignment_status="Misaligned").count()
        
        avg_score = results.aggregate(Avg('overall_alignment_score'))['overall_alignment_score__avg'] or 0
        
        project_summary = {
            "name": project.name,
            "client_name": getattr(project, 'client_name', 'Unknown'),
            "status": getattr(project, 'status', 'Unknown'),
            "created_at": project.created_at.isoformat(),
        }
        
        alignment_overview = {
            "total": total_results,
            "aligned": aligned,
            "drift": drift,
            "misaligned": misaligned,
            "avg_score": round(avg_score),
        }
        
        top_risks = [
            {
                "mismatch_type": r.mismatch_type,
                "description": r.description,
                "severity": r.severity,
                "status": r.status
            }
            for r in MismatchReport.objects.filter(project_id=project_id, status="Open").order_by('-created_at')[:5]
        ]
        
        health = self.get_project_health(project_id)
        
        # Generate narrative and recommendations using Groq (text only)
        narrative = self._generate_narrative(project_summary, alignment_overview, health, top_risks)
        recommendations = self._generate_recommendations(project_summary, health, top_risks)
        
        return {
            "project_summary": project_summary,
            "alignment_overview": alignment_overview,
            "top_risks": top_risks,
            "health": health,
            "narrative": narrative,
            "recommendations": recommendations,
        }

    def generate_mismatch_reports(self, project_id: UUID, current_user=None) -> int:
        """Generate mismatch reports for all alignment results that show risk.
        
        Severity mapping:
        - score < 50  (Misaligned)       -> Critical/High severity
        - score 50-74 (Potential Drift)  -> High/Medium severity  
        - score 75-84 (Weak Aligned)     -> Medium severity (imperfect alignment)
        - score 85-89 (Near Aligned)     -> Low severity (minor gaps)
        - score >= 90 (Well Aligned)     -> No report generated
        """
        all_results = AlignmentResult.objects.filter(
            project_id=project_id,
            is_deleted=False,
            overall_alignment_score__lt=90  # Generate for any result below 90%
        )
        
        generated_count = 0
        for result in all_results:
            # Check if a mismatch report already exists for this result
            if MismatchReport.objects.filter(alignment_result=result, is_deleted=False).exists():
                continue
            
            score = result.overall_alignment_score or 0
            status = result.alignment_status
            
            # Determine mismatch type and severity based on score and status
            if status == "Misaligned" or score < 50:
                mismatch_type = "Missing Implementation"
                severity = "Critical" if score < 30 else "High"
                suggested_fix = (
                    "Critical gap detected: The requirement has no matching implementation. "
                    "Immediately create the corresponding Jira story, pull request, and code artifact."
                )
            elif status == "Potential Drift" or score < 75:
                mismatch_type = "Implementation Drift"
                severity = "High" if score < 60 else "Medium"
                suggested_fix = (
                    "Significant drift detected between the requirement and its implementation. "
                    "Review and update the code artifact or Jira story to better match the requirement."
                )
            elif score < 85:
                mismatch_type = "Partial Coverage Gap"
                severity = "Medium"
                suggested_fix = (
                    "Partial coverage: The implementation partially addresses the requirement but has gaps. "
                    "Review the traceability chain and ensure all acceptance criteria are implemented."
                )
            else:  # score 85-89
                mismatch_type = "Minor Alignment Gap"
                severity = "Low"
                suggested_fix = (
                    "Minor alignment gap: The implementation mostly aligns but has minor deviations. "
                    "Consider reviewing edge cases and ensuring all requirement details are covered."
                )
            
            # Use explanation only if it's meaningful (not just the fallback hint)
            explanation = result.explanation or ""
            use_explanation = explanation and "GROQ_API_KEY" not in explanation and len(explanation) > 30
            
            if use_explanation:
                description = explanation
            else:
                req_jira = result.requirement_jira_score or 0
                jira_pr = result.jira_pr_score or 0
                pr_art = result.pr_artifact_score or 0
                description = (
                    f"Alignment score: {score}% — partial coverage detected in the requirement-to-implementation chain. "
                    f"Component scores: Requirement->Jira: {req_jira}%, Jira->PR: {jira_pr}%, PR->Code: {pr_art}%. "
                    f"This indicates the implementation does not fully satisfy all requirement criteria."
                )
            
            MismatchReport.objects.create(
                project_id=project_id,
                alignment_result=result,
                mismatch_type=mismatch_type,
                description=description,
                suggested_fix=suggested_fix,
                severity=severity,
                status="Open",
                created_by=current_user
            )
            generated_count += 1
            
        return generated_count

    def _generate_narrative(
        self,
        project_summary: Dict[str, Any],
        alignment_overview: Dict[str, Any],
        health: Dict[str, Any],
        top_risks: List[Dict[str, Any]],
    ) -> str:
        import os
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            return (
                f"Project '{project_summary.get('name', 'N/A')}' has a health score of "
                f"{health.get('health_score', 'N/A')}% ({health.get('health_status', 'N/A')}). "
                f"There are {alignment_overview.get('total', 0)} alignment results with "
                f"an average score of {alignment_overview.get('avg_score', 0)}%. "
                f"{health.get('open_mismatches', 0)} open mismatches require attention. "
                f"(Enable GROQ_API_KEY for AI-generated executive narrative.)"
            )

        try:
            from groq import Groq
            client = Groq(api_key=api_key)

            risk_summary = ""
            if top_risks:
                risk_lines = [f"- [{r['severity']}] {r['mismatch_type']}: {r['description'][:100]}" for r in top_risks[:5]]
                risk_summary = "\n".join(risk_lines)

            prompt = f"""You are a senior engineering manager writing an executive project status report.
Write a 2-3 paragraph management summary for the following project alignment data.

Project: {project_summary.get('name', 'N/A')} (Client: {project_summary.get('client_name', 'N/A')})
Health Score: {health.get('health_score')}% ({health.get('health_status')})
Alignment Results: {alignment_overview.get('total', 0)} total, avg score {alignment_overview.get('avg_score', 0)}%
Open Mismatches: {health.get('open_mismatches', 0)}
Resolved Mismatches: {health.get('resolved_mismatches', 0)}
Requirements: {health.get('total_requirements', 0)} total, {health.get('approved_requirements', 0)} approved

Top Risks:
{risk_summary if risk_summary else 'No critical risks identified.'}

Write professionally. Focus on impact, trends, and actionable insights. Do NOT invent scores or metrics — only reference the data above."""

            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-70b-8192",
                temperature=0.3,
                max_tokens=500,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            return (
                f"Project '{project_summary.get('name', 'N/A')}' health: "
                f"{health.get('health_score', 'N/A')}% ({health.get('health_status', 'N/A')}). "
                f"(AI narrative unavailable.)"
            )

    def _generate_recommendations(
        self,
        project_summary: Dict[str, Any],
        health: Dict[str, Any],
        top_risks: List[Dict[str, Any]],
    ) -> List[str]:
        import os
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
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
            from groq import Groq
            client = Groq(api_key=api_key)

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

            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-70b-8192",
                temperature=0.3,
                max_tokens=400,
            )
            raw = response.choices[0].message.content.strip()
            lines = [line.strip() for line in raw.split("\n") if line.strip()]
            cleaned = []
            for line in lines:
                if len(line) > 2 and line[0].isdigit() and line[1] == '.':
                    cleaned.append(line[2:].strip())
                elif len(line) > 3 and line[:2].isdigit() and line[2] == '.':
                    cleaned.append(line[3:].strip())
                else:
                    cleaned.append(line)
            return cleaned if cleaned else ["No specific recommendations generated."]
        except Exception as exc:
            return ["Review open mismatch reports and address critical alignment gaps. (AI recommendations unavailable.)"]

reporting_service = ReportingService()
