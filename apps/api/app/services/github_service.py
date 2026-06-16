"""
GitHub Integration Service
Wraps PyGithub with graceful degradation when token is absent.
"""
from __future__ import annotations

import logging
import re
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models.pull_request import PullRequest
from app.schemas.pull_request import PullRequestCreate, PullRequestUpdate
from app.repositories.pull_request_repository import pull_request_repo

logger = logging.getLogger(__name__)


def _get_github_client():
    """Return a connected Github client or raise RuntimeError if unconfigured."""
    if not settings.GITHUB_TOKEN:
        raise RuntimeError("GitHub token is not configured.")
    from github import Github
    return Github(settings.GITHUB_TOKEN)


def _parse_repo_identifier(repository_url: str) -> str:
    """
    Extract 'owner/repo' from a GitHub URL.
    Handles:  https://github.com/owner/repo  or  https://github.com/owner/repo.git
    """
    match = re.search(r"github\.com[:/](.+?)(?:\.git)?$", repository_url.rstrip("/"))
    if not match:
        raise ValueError(f"Cannot parse GitHub repo from URL: {repository_url}")
    return match.group(1)


class GitHubService:
    def is_configured(self) -> bool:
        return bool(settings.GITHUB_TOKEN)

    def get_status(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "configured": False,
                "message": "GitHub token not configured. Set GITHUB_TOKEN in .env",
                "setup_instructions": [
                    "1. Go to https://github.com/settings/tokens",
                    "2. Click 'Generate new token (classic)'",
                    "3. Select scopes: repo, read:org",
                    "4. Add GITHUB_TOKEN=your_token to .env",
                ],
            }
        try:
            client = _get_github_client()
            user = client.get_user()
            rate_limit_info = client.get_rate_limit()
            remaining = rate_limit_info.rate.remaining if hasattr(rate_limit_info, "rate") else rate_limit_info.core.remaining
            
            return {
                "configured": True,
                "connected": True,
                "github_user": user.login,
                "rate_limit_remaining": remaining,
            }
        except Exception as exc:
            return {"configured": True, "connected": False, "error": str(exc)}

    async def sync_pull_requests(
        self,
        db: AsyncSession,
        *,
        project_id: UUID,
        repository_url: str,
        current_user_id: UUID,
        state: str = "all",   # "open", "closed", "all"
    ) -> Dict[str, Any]:
        """
        Sync PRs from a GitHub repository into the DB.
        """
        if not self.is_configured():
            raise RuntimeError("GitHub token is not configured.")

        client = _get_github_client()
        repo_id = _parse_repo_identifier(repository_url)
        repo = client.get_repo(repo_id)
        pulls = list(repo.get_pulls(state=state, sort="updated", direction="desc"))

        created_count = 0
        updated_count = 0

        for pr in pulls:
            # Determine status string
            if pr.merged:
                status = "merged"
            elif pr.state == "closed":
                status = "closed"
            else:
                status = "open"

            changed_files = [f.filename for f in pr.get_files()]

            pr_data = {
                "project_id": project_id,
                "pr_number": pr.number,
                "repository_url": repository_url,
                "title": pr.title,
                "pr_description": pr.body or None,
                "status": status,
                "author": pr.user.login if pr.user else None,
                "branch": pr.head.ref if pr.head else None,
                "base_branch": pr.base.ref if pr.base else None,
                "head_sha": pr.head.sha if pr.head else None,
                "merged_at": pr.merged_at,
                "changed_files": changed_files,
                "diff_content": None,  # Omit raw diff to keep DB lean
            }

            # Upsert by pr_number + project_id
            stmt = select(PullRequest).where(
                PullRequest.pr_number == pr.number,
                PullRequest.project_id == project_id,
                PullRequest.is_deleted == False,
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                update_in = PullRequestUpdate(**{
                    k: v for k, v in pr_data.items()
                    if k not in ("project_id", "pr_number", "repository_url")
                })
                await pull_request_repo.update(
                    db=db, db_obj=existing, obj_in=update_in, updated_by_id=current_user_id
                )
                updated_count += 1
            else:
                create_in = PullRequestCreate(**pr_data)
                await pull_request_repo.create(db=db, obj_in=create_in, created_by_id=current_user_id)
                created_count += 1

        return {
            "synced": len(pulls),
            "created": created_count,
            "updated": updated_count,
            "repository": repo_id,
        }

    async def get_file_content(self, repository_url: str, file_path: str, ref: str = "main") -> Optional[str]:
        """
        Fetch the raw content of a file from a GitHub repository at a given ref.
        Returns None on failure.
        """
        if not self.is_configured():
            return None
        try:
            client = _get_github_client()
            repo_id = _parse_repo_identifier(repository_url)
            repo = client.get_repo(repo_id)
            contents = repo.get_contents(file_path, ref=ref)
            if isinstance(contents, list):
                return None  # directory, not a file
            return contents.decoded_content.decode("utf-8", errors="replace")
        except Exception as exc:
            logger.warning(f"Could not fetch {file_path} from {repository_url}: {exc}")
            return None

    async def get_project_prs(self, db: AsyncSession, *, project_id: UUID) -> List[PullRequest]:
        stmt = select(PullRequest).where(
            PullRequest.project_id == project_id,
            PullRequest.is_deleted == False,
        ).order_by(PullRequest.pr_number.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())


github_service = GitHubService()
