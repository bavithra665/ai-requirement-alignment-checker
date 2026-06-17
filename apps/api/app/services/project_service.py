from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.project_repository import project_repo
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.models.project import Project

from sqlalchemy import select, func
from app.models.requirement import Requirement
from app.models.requirement_version import RequirementVersion
from app.models.jira_story import JiraStory
from app.models.pull_request import PullRequest
from app.models.alignment_result import AlignmentResult
from app.models.mismatch_report import MismatchReport

class ProjectService:
    async def _calculate_project_status(self, db: AsyncSession, project_id: UUID) -> tuple[str, str]:
        # 1. Check for approved baseline requirements
        stmt_baseline = select(func.count(RequirementVersion.id)).join(Requirement).where(
            Requirement.project_id == project_id,
            RequirementVersion.is_baseline == True,
            RequirementVersion.status == "Approved"
        )
        baseline_count = (await db.execute(stmt_baseline)).scalar() or 0

        if baseline_count == 0:
            return "Draft", "Project exists but no approved baseline requirements are set."

        # 2. Check for active artifacts (Jira, PRs, Alignment Results)
        stmt_jira = select(func.count(JiraStory.id)).where(JiraStory.project_id == project_id)
        jira_count = (await db.execute(stmt_jira)).scalar() or 0

        stmt_pr = select(func.count(PullRequest.id)).where(PullRequest.project_id == project_id)
        pr_count = (await db.execute(stmt_pr)).scalar() or 0

        stmt_alignment = select(func.count(AlignmentResult.id)).where(AlignmentResult.project_id == project_id)
        alignment_count = (await db.execute(stmt_alignment)).scalar() or 0

        active_artifacts_exist = (jira_count > 0) or (pr_count > 0) or (alignment_count > 0)

        if not active_artifacts_exist:
            return "Draft", "Approved baseline exists but no implementation artifacts are active."

        # 3. Check for open mismatches
        stmt_mismatch = select(func.count(MismatchReport.id)).where(
            MismatchReport.project_id == project_id,
            MismatchReport.status == "Open"
        )
        open_mismatch_count = (await db.execute(stmt_mismatch)).scalar() or 0

        if open_mismatch_count > 0:
            return "In Progress", f"Approved baseline exists, active development artifacts are being analyzed. {open_mismatch_count} open mismatches exist."

        # If we have baseline and artifacts, and NO open mismatches, check if all requirements are aligned.
        # This means an alignment result exists, and there are no open issues.
        # Assuming if alignment_count > 0 and open_mismatch_count == 0 -> Completed.
        return "Completed", "All requirements are aligned and no open mismatches exist."

    async def _attach_status(self, db: AsyncSession, project: Project) -> Project:
        if not project:
            return project
        status, reason = await self._calculate_project_status(db, project.id)
        project.status = status
        project.status_reason = reason
        return project

    async def create_project(self, db: AsyncSession, project_in: ProjectCreate, current_user_id: UUID) -> Project:
        # Override owner_id to be the current user
        project_in.owner_id = current_user_id
        project = await project_repo.create(db=db, obj_in=project_in, created_by_id=current_user_id)
        return await self._attach_status(db, project)

    async def get_project(self, db: AsyncSession, project_id: UUID) -> Optional[Project]:
        project = await project_repo.get(db=db, id=project_id)
        return await self._attach_status(db, project)

    async def get_projects(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Project]:
        projects = await project_repo.get_multi(db=db, skip=skip, limit=limit)
        for project in projects:
            await self._attach_status(db, project)
        return projects

    async def update_project(
        self, db: AsyncSession, project_id: UUID, project_in: ProjectUpdate, current_user_id: UUID
    ) -> Optional[Project]:
        project = await project_repo.get(db=db, id=project_id)
        if not project:
            return None
        updated_project = await project_repo.update(db=db, db_obj=project, obj_in=project_in, updated_by_id=current_user_id)
        return await self._attach_status(db, updated_project)

    async def delete_project(self, db: AsyncSession, project_id: UUID, current_user_id: UUID) -> Optional[Project]:
        project = await project_repo.remove(db=db, id=project_id, updated_by_id=current_user_id)
        if project:
            project.status = "Deleted"
            project.status_reason = "Project deleted."
        return project

project_service = ProjectService()
