from typing import Dict, Any, List
from uuid import UUID
from django.db.models import Avg, Count
from projects.models import Project, Requirement
from integrations.models import JiraStory, PullRequest, CodeArtifact
from alignment.models import AlignmentResult
from .models import MismatchReport

class ReportingService:
    def get_executive_summary(self, project_id: UUID) -> Dict[str, Any]:
        project = Project.objects.get(id=project_id)
        
        # Alignment Results
        results = AlignmentResult.objects.filter(project_id=project_id, is_deleted=False)
        total_results = results.count()
        
        aligned = results.filter(alignment_status="Aligned").count()
        drift = results.filter(alignment_status="Potential Drift").count()
        misaligned = results.filter(alignment_status="Misaligned").count()
        
        avg_score = results.aggregate(Avg('overall_alignment_score'))['overall_alignment_score__avg'] or 0
        
        return {
            "project_summary": {
                "name": project.name,
                "client_name": getattr(project, 'client_name', 'Unknown'),
                "status": getattr(project, 'status', 'Unknown'),
                "created_at": project.created_at.isoformat(),
            },
            "alignment_overview": {
                "total": total_results,
                "aligned": aligned,
                "drift": drift,
                "misaligned": misaligned,
                "avg_score": round(avg_score),
            },
            "top_risks": [
                {
                    "mismatch_type": r.mismatch_type,
                    "description": r.description,
                    "severity": r.severity,
                    "status": r.status
                }
                for r in MismatchReport.objects.filter(project_id=project_id, status="Open").order_by('-created_at')[:5]
            ]
        }

    def get_risk_dashboard(self, project_id: UUID) -> Dict[str, Any]:
        # 1. Requirements without Jira stories
        # Here we just look at alignment results
        results = AlignmentResult.objects.filter(project_id=project_id, is_deleted=False)
        reqs_without_jira = results.filter(jira_story__isnull=True).count()
        
        # 2. Jira stories without PRs
        jira_without_prs = results.filter(jira_story__isnull=False, pull_request__isnull=True).count()
        
        # 3. PRs without code artifacts
        prs_without_code = results.filter(pull_request__isnull=False, code_artifact__isnull=True).count()
        
        # 4. Misaligned implementations
        misaligned = results.filter(alignment_status="Misaligned").count()
        
        total_reqs = results.count()
        
        return {
            "health_score": round(results.aggregate(Avg('overall_alignment_score'))['overall_alignment_score__avg'] or 0),
            "total_requirements": total_reqs,
            "risks": {
                "requirements_without_jira": reqs_without_jira,
                "jira_without_prs": jira_without_prs,
                "prs_without_code": prs_without_code,
                "misaligned_implementations": misaligned
            }
        }

    def generate_mismatch_reports(self, project_id: UUID, current_user=None) -> int:
        # Find results that are Misaligned or Potential Drift
        risky_results = AlignmentResult.objects.filter(
            project_id=project_id,
            is_deleted=False,
            alignment_status__in=["Misaligned", "Potential Drift"]
        )
        
        generated_count = 0
        for result in risky_results:
            # Check if a mismatch report already exists for this result
            if MismatchReport.objects.filter(alignment_result=result, is_deleted=False).exists():
                continue
            
            mismatch_type = "Missing Implementation" if result.alignment_status == "Misaligned" else "Implementation Drift"
            severity = "High" if result.alignment_status == "Misaligned" else "Medium"
            
            MismatchReport.objects.create(
                project_id=project_id,
                alignment_result=result,
                mismatch_type=mismatch_type,
                description=result.explanation or "AI detected drift or missing implementation.",
                suggested_fix="Review the traceability chain and update the implementation or requirement.",
                severity=severity,
                status="Open",
                created_by=current_user
            )
            generated_count += 1
            
        return generated_count

reporting_service = ReportingService()
