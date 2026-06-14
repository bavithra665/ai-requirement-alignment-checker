"""
AI Alignment Engine — Core Intelligence Module

Implements relationship-aware traceability alignment:
  Approved Requirement ➔ Jira Story ➔ Pull Request ➔ Code Artifact

Scoring uses Cosine Similarity via Chroma + SentenceTransformers.
Groq is used ONLY for human-readable explanation generation (no scoring).

Thresholds:
  >= 75%  →  Aligned
  50-74%  →  Potential Drift
  < 50%   →  Misaligned
"""
from __future__ import annotations

import logging
import os
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.requirement_version import RequirementVersion
from app.models.requirement import Requirement
from app.models.jira_story import JiraStory
from app.models.pull_request import PullRequest
from app.models.code_artifact import CodeArtifact, ArtifactType
from app.models.alignment_result import AlignmentResult
from app.schemas.alignment_result import AlignmentResultCreate
from app.repositories.alignment_result_repository import alignment_result_repo
from app.services.chroma_service import chroma_service

logger = logging.getLogger(__name__)

# ─── Score Thresholds ─────────────────────────────────────────────────────────
THRESHOLD_ALIGNED = 75
THRESHOLD_DRIFT = 50


def _score_to_status(score_pct: int) -> str:
    if score_pct >= THRESHOLD_ALIGNED:
        return "Aligned"
    elif score_pct >= THRESHOLD_DRIFT:
        return "Potential Drift"
    return "Misaligned"


def _compute_overall_score(
    req_jira: Optional[int],
    jira_pr: Optional[int],
    pr_artifact: Optional[int],
) -> int:
    """
    Weighted average of available chain scores.
    Weights: req→jira 40%, jira→pr 35%, pr→artifact 25%.
    Falls back gracefully if some chain links don't exist for a project.
    """
    scores, weights = [], []
    if req_jira is not None:
        scores.append(req_jira); weights.append(0.40)
    if jira_pr is not None:
        scores.append(jira_pr);  weights.append(0.35)
    if pr_artifact is not None:
        scores.append(pr_artifact); weights.append(0.25)

    if not scores:
        return 0

    total_weight = sum(weights)
    weighted_sum = sum(s * w for s, w in zip(scores, weights))
    return round(weighted_sum / total_weight)


def _confidence(req_jira, jira_pr, pr_artifact) -> int:
    """Confidence reflects how many chain links are available (max 100)."""
    available = sum(1 for x in [req_jira, jira_pr, pr_artifact] if x is not None)
    return round((available / 3) * 100)


async def _groq_explanation(
    requirement_text: str,
    jira_title: Optional[str],
    pr_title: Optional[str],
    artifact_name: Optional[str],
    overall_score: int,
    status: str,
) -> str:
    """
    Uses Groq Llama3 to generate a concise, human-readable alignment explanation.
    Falls back gracefully if Groq key is missing.
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return (
            f"Alignment status: {status}. Overall score: {overall_score}%. "
            "(Enable GROQ_API_KEY for detailed AI explanations.)"
        )

    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=api_key)

        chain_parts = []
        if jira_title:
            chain_parts.append(f"Jira Story: \"{jira_title}\"")
        if pr_title:
            chain_parts.append(f"Pull Request: \"{pr_title}\"")
        if artifact_name:
            chain_parts.append(f"Code Artifact: \"{artifact_name}\"")

        chain_str = " → ".join(chain_parts) if chain_parts else "No implementation evidence found."

        prompt = f"""You are a software delivery alignment expert. Analyze the following traceability chain and explain concisely whether the implementation aligns with the approved requirement.

Approved Requirement:
\"{requirement_text[:500]}\"

Implementation Chain:
{chain_str}

Overall Alignment Score: {overall_score}%
Alignment Status: {status}

Write a single paragraph explanation (2-4 sentences) that:
- States clearly whether implementation aligns
- Identifies specific drift or gaps if any (be concrete, name the entities)
- Avoids generic filler language
- Uses professional, enterprise reporting tone"""

        response = await client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-70b-8192",
            temperature=0.2,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.warning(f"Groq explanation generation failed: {exc}")
        return f"Alignment status: {status}. Score: {overall_score}%. (AI explanation unavailable.)"


class AlignmentEngine:

    # ──────────────────────────────────────────────────────────────────────────
    # Public: Index project artifacts into ChromaDB
    # ──────────────────────────────────────────────────────────────────────────

    async def index_project(self, db: AsyncSession, project_id: UUID) -> Dict[str, int]:
        """
        Index all eligible project artifacts (requirements, jira, PRs, code artifacts)
        into ChromaDB for vector similarity search. Called after sync/approval events
        to keep embeddings current without re-generating them at alignment runtime.
        """
        counts = {
            "requirements": 0,
            "jira_stories": 0,
            "pull_requests": 0,
            "code_artifacts": 0,
        }

        # 1. Approved Baseline Requirement Versions
        stmt = select(RequirementVersion).where(
            RequirementVersion.is_deleted == False,
            RequirementVersion.is_baseline == True,
        ).join(RequirementVersion.requirement).where(
            Requirement.project_id == project_id,
            Requirement.is_deleted == False,
        )
        result = await db.execute(stmt)
        versions: List[RequirementVersion] = list(result.scalars().all())
        for ver in versions:
            chroma_service.upsert_entity(
                collection_name="requirements",
                entity_id=ver.id,
                project_id=project_id,
                text_content=ver.content,
                metadata={"version_number": ver.version_number, "status": ver.status},
            )
            counts["requirements"] += 1

        # 2. Jira Stories
        stmt = select(JiraStory).where(
            JiraStory.project_id == project_id,
            JiraStory.is_deleted == False,
        )
        result = await db.execute(stmt)
        stories: List[JiraStory] = list(result.scalars().all())
        for story in stories:
            text = f"{story.title or ''}\n{story.description or ''}".strip()
            chroma_service.upsert_entity(
                collection_name="jira_stories",
                entity_id=story.id,
                project_id=project_id,
                text_content=text,
                metadata={"jira_key": story.jira_issue_key, "status": story.status, "story_type": story.story_type or ""},
            )
            counts["jira_stories"] += 1

        # 3. Pull Requests
        stmt = select(PullRequest).where(
            PullRequest.project_id == project_id,
            PullRequest.is_deleted == False,
        )
        result = await db.execute(stmt)
        prs: List[PullRequest] = list(result.scalars().all())
        for pr in prs:
            text = f"{pr.title or ''}\n{pr.pr_description or ''}".strip()
            chroma_service.upsert_entity(
                collection_name="pull_requests",
                entity_id=pr.id,
                project_id=project_id,
                text_content=text,
                metadata={"pr_number": pr.pr_number, "status": pr.status, "branch": pr.branch or ""},
            )
            counts["pull_requests"] += 1

        # 4. Code Artifacts (functions, classes, API endpoints)
        # Join through pull_requests to scope by project_id
        stmt = (
            select(CodeArtifact)
            .join(CodeArtifact.pull_request)
            .where(
                PullRequest.project_id == project_id,
                PullRequest.is_deleted == False,
                CodeArtifact.is_deleted == False,
            )
        )
        result = await db.execute(stmt)
        artifacts: List[CodeArtifact] = list(result.scalars().all())
        for artifact in artifacts:
            meta = artifact.artifact_metadata or {}
            text_parts = [artifact.artifact_name, artifact.file_path]
            if artifact.artifact_type == ArtifactType.FUNCTION:
                args = meta.get("args", [])
                if args:
                    text_parts.append(f"args: {', '.join(args)}")
            elif artifact.artifact_type == ArtifactType.API_ENDPOINT:
                method = meta.get("http_method", "")
                if method:
                    text_parts.append(f"{method} endpoint")
            text = " | ".join(text_parts)
            chroma_service.upsert_entity(
                collection_name="code_artifacts",
                entity_id=artifact.id,
                project_id=project_id,
                text_content=text,
                metadata={"artifact_type": artifact.artifact_type.value, "file_path": artifact.file_path},
            )
            counts["code_artifacts"] += 1

        logger.info(f"Project {project_id} indexed: {counts}")
        return counts

    # ──────────────────────────────────────────────────────────────────────────
    # Public: Run alignment analysis for a project
    # ──────────────────────────────────────────────────────────────────────────

    async def run_alignment(
        self, db: AsyncSession, project_id: UUID, current_user_id: UUID
    ) -> List[AlignmentResult]:
        """
        Execute the full relationship-aware alignment pipeline:
          Requirement ➔ Jira ➔ PR ➔ Code Artifact
        Generates and persists AlignmentResult records.
        """
        # Step 1: Re-index all project artifacts (embeddings cached in Chroma)
        await self.index_project(db, project_id)

        # Step 2: Delete previous alignment results for clean run
        stmt = select(AlignmentResult).where(
            AlignmentResult.project_id == project_id,
            AlignmentResult.is_deleted == False,
        )
        result = await db.execute(stmt)
        old_results = list(result.scalars().all())
        for old in old_results:
            old.is_deleted = True
        if old_results:
            await db.commit()

        # Step 3: Fetch all approved baseline requirement versions for this project
        stmt = (
            select(RequirementVersion)
            .join(RequirementVersion.requirement)
            .where(
                Requirement.project_id == project_id,
                Requirement.is_deleted == False,
                RequirementVersion.is_baseline == True,
                RequirementVersion.is_deleted == False,
            )
        )
        result = await db.execute(stmt)
        baseline_versions: List[RequirementVersion] = list(result.scalars().all())

        if not baseline_versions:
            logger.warning(f"No baseline requirements found for project {project_id}")
            return []

        # Step 4: For each baseline requirement, walk the chain
        saved_results: List[AlignmentResult] = []
        for ver in baseline_versions:
            result_obj = await self._align_requirement(
                db=db,
                project_id=project_id,
                requirement_version=ver,
                current_user_id=current_user_id,
            )
            if result_obj:
                saved_results.append(result_obj)

        logger.info(f"Alignment run complete for project {project_id}: {len(saved_results)} results saved")
        return saved_results

    # ──────────────────────────────────────────────────────────────────────────
    # Private: Align a single requirement through the chain
    # ──────────────────────────────────────────────────────────────────────────

    async def _align_requirement(
        self,
        db: AsyncSession,
        project_id: UUID,
        requirement_version: RequirementVersion,
        current_user_id: UUID,
    ) -> Optional[AlignmentResult]:
        req_text = requirement_version.content
        if not req_text or not req_text.strip():
            return None

        # ── Step A: Requirement ↔ Jira Story ─────────────────────────────────
        req_jira_score: Optional[int] = None
        best_jira_id: Optional[UUID] = None
        best_jira_title: Optional[str] = None

        jira_hits = chroma_service.query_similarity(
            collection_name="jira_stories",
            project_id=project_id,
            query_text=req_text,
            n_results=1,
        )
        if jira_hits:
            req_jira_score = round(jira_hits[0]["similarity"] * 100)
            best_jira_id = jira_hits[0]["entity_id"]
            best_jira_title = jira_hits[0].get("text", "")[:100]

        # ── Step B: Jira Story ↔ Pull Request ────────────────────────────────
        jira_pr_score: Optional[int] = None
        best_pr_id: Optional[UUID] = None
        best_pr_title: Optional[str] = None

        # Query PRs using the Jira story text (if found) or fallback to req_text
        jira_query_text = best_jira_title if best_jira_title else req_text
        pr_hits = chroma_service.query_similarity(
            collection_name="pull_requests",
            project_id=project_id,
            query_text=jira_query_text,
            n_results=1,
        )
        if pr_hits:
            jira_pr_score = round(pr_hits[0]["similarity"] * 100)
            best_pr_id = pr_hits[0]["entity_id"]
            best_pr_title = pr_hits[0].get("text", "")[:100]

        # ── Step C: Pull Request ↔ Code Artifact ─────────────────────────────
        pr_artifact_score: Optional[int] = None
        best_artifact_id: Optional[UUID] = None
        best_artifact_name: Optional[str] = None

        artifact_query_text = best_pr_title if best_pr_title else jira_query_text
        artifact_hits = chroma_service.query_similarity(
            collection_name="code_artifacts",
            project_id=project_id,
            query_text=artifact_query_text,
            n_results=1,
        )
        if artifact_hits:
            pr_artifact_score = round(artifact_hits[0]["similarity"] * 100)
            best_artifact_id = artifact_hits[0]["entity_id"]
            best_artifact_name = artifact_hits[0].get("text", "")[:100]

        # ── Step D: Compute overall score & status ────────────────────────────
        overall = _compute_overall_score(req_jira_score, jira_pr_score, pr_artifact_score)
        status = _score_to_status(overall)
        confidence = _confidence(req_jira_score, jira_pr_score, pr_artifact_score)

        # ── Step E: Groq explanation (async, non-blocking if key absent) ──────
        explanation = await _groq_explanation(
            requirement_text=req_text,
            jira_title=best_jira_title,
            pr_title=best_pr_title,
            artifact_name=best_artifact_name,
            overall_score=overall,
            status=status,
        )

        # ── Step F: Persist AlignmentResult record ────────────────────────────
        result_in = AlignmentResultCreate(
            project_id=project_id,
            requirement_version_id=requirement_version.id,
            jira_story_id=best_jira_id,
            pull_request_id=best_pr_id,
            code_artifact_id=best_artifact_id,
            requirement_jira_score=req_jira_score,
            jira_pr_score=jira_pr_score,
            pr_artifact_score=pr_artifact_score,
            overall_alignment_score=overall,
            alignment_status=status,
            confidence=confidence,
            explanation=explanation,
            # Legacy compat fields
            score=overall,
            summary=explanation,
        )

        saved = await alignment_result_repo.create(
            db=db, obj_in=result_in, created_by_id=current_user_id
        )
        return saved


alignment_engine = AlignmentEngine()
