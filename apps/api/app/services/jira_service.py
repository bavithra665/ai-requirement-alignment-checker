"""
Jira Integration Service
Wraps jira-python client with graceful degradation when credentials are absent.
"""
from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models.jira_story import JiraStory
from app.schemas.jira_story import JiraStoryCreate, JiraStoryUpdate
from app.repositories.jira_story_repository import jira_story_repo

logger = logging.getLogger(__name__)


def _get_jira_client():
    """Return a connected Jira client or raise RuntimeError if unconfigured."""
    if not all([settings.JIRA_BASE_URL, settings.JIRA_API_TOKEN, settings.JIRA_USER_EMAIL]):
        raise RuntimeError("Jira credentials are not configured.")
    from jira import JIRA
    return JIRA(
        server=settings.JIRA_BASE_URL,
        basic_auth=(settings.JIRA_USER_EMAIL, settings.JIRA_API_TOKEN),
    )


class JiraService:
    def is_configured(self) -> bool:
        return all([settings.JIRA_BASE_URL, settings.JIRA_API_TOKEN, settings.JIRA_USER_EMAIL])

    def get_status(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "configured": False,
                "message": "Jira credentials not configured. Set JIRA_BASE_URL, JIRA_API_TOKEN, JIRA_USER_EMAIL in .env",
                "setup_instructions": [
                    "1. Go to your Atlassian account settings",
                    "2. Create an API token at https://id.atlassian.com/manage-profile/security/api-tokens",
                    "3. Add JIRA_BASE_URL=https://yourcompany.atlassian.net",
                    "4. Add JIRA_USER_EMAIL=your@email.com",
                    "5. Add JIRA_API_TOKEN=your_token to .env",
                ],
            }
        try:
            client = _get_jira_client()
            server_info = client.server_info()
            return {
                "configured": True,
                "connected": True,
                "server_title": server_info.get("serverTitle", "Jira"),
                "base_url": settings.JIRA_BASE_URL,
            }
        except Exception as exc:
            return {"configured": True, "connected": False, "error": str(exc)}

    async def sync_project_stories(
        self,
        db: AsyncSession,
        *,
        project_id: UUID,
        jira_project_key: str,
        current_user_id: UUID,
    ) -> Dict[str, Any]:
        """
        Fetch all issues from Jira for a project key and upsert into the DB.
        Returns a summary dict with counts.
        """
        if not self.is_configured():
            raise RuntimeError("Jira credentials are not configured.")

        client = _get_jira_client()

        # Fetch all issues (Stories, Epics, Tasks, Bugs) with pagination
        start = 0
        page_size = 50
        all_issues = []
        while True:
            issues = client.search_issues(
                f'project = {jira_project_key} ORDER BY created ASC',
                startAt=start,
                maxResults=page_size,
                fields="summary,description,status,issuetype,assignee,priority,epic,labels,customfield_10014",
            )
            all_issues.extend(issues)
            if len(issues) < page_size:
                break
            start += page_size

        created_count = 0
        updated_count = 0

        for issue in all_issues:
            fields = issue.fields
            story_data = {
                "project_id": project_id,
                "jira_issue_key": issue.key,
                "title": fields.summary,
                "description": fields.description or None,
                "status": fields.status.name if fields.status else "Unknown",
                "story_type": fields.issuetype.name if fields.issuetype else None,
                "assignee": fields.assignee.displayName if fields.assignee else None,
                "priority": fields.priority.name if fields.priority else None,
                "external_url": f"{settings.JIRA_BASE_URL}/browse/{issue.key}",
                "labels": list(fields.labels) if fields.labels else [],
                "epic_key": getattr(fields, 'customfield_10014', None),  # Epic Link field
            }

            # Check if already exists (by jira_issue_key + project_id)
            stmt = select(JiraStory).where(
                JiraStory.jira_issue_key == issue.key,
                JiraStory.project_id == project_id,
                JiraStory.is_deleted == False,
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                update_in = JiraStoryUpdate(**{
                    k: v for k, v in story_data.items()
                    if k not in ("project_id", "jira_issue_key")
                })
                await jira_story_repo.update(
                    db=db, db_obj=existing, obj_in=update_in, updated_by_id=current_user_id
                )
                updated_count += 1
            else:
                create_in = JiraStoryCreate(**story_data)
                await jira_story_repo.create(db=db, obj_in=create_in, created_by_id=current_user_id)
                created_count += 1

        return {
            "synced": len(all_issues),
            "created": created_count,
            "updated": updated_count,
            "jira_project_key": jira_project_key,
        }

    async def get_project_stories(
        self, db: AsyncSession, *, project_id: UUID
    ) -> List[JiraStory]:
        stmt = select(JiraStory).where(
            JiraStory.project_id == project_id,
            JiraStory.is_deleted == False,
        ).order_by(JiraStory.created_at.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())


jira_service = JiraService()
