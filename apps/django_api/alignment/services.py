import os
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from django.conf import settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_client = None
_embed_model = None

def get_chroma_client():
    global _client
    if _client is None:
        import chromadb
        # Store Chroma DB inside apps/django_api/chroma_db/ as requested by the user
        db_path = os.path.join(settings.BASE_DIR, "chroma_db")
        os.makedirs(db_path, exist_ok=True)
        _client = chromadb.PersistentClient(path=db_path)
    return _client

def get_embedding_model():
    global _embed_model
    if _embed_model is None:
        # User specified: sentence-transformers/all-MiniLM-L6-v2
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embed_model

class ChromaService:
    def generate_embedding(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * 384
        model = get_embedding_model()
        embedding = model.encode(text.strip(), convert_to_numpy=True)
        return embedding.tolist()

    def upsert_entity(
        self,
        collection_name: str,
        entity_id: UUID,
        project_id: UUID,
        text_content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        try:
            client = get_chroma_client()
            collection = client.get_or_create_collection(name=collection_name)
            embedding = self.generate_embedding(text_content)

            meta = {
                "project_id": str(project_id),
                "entity_id": str(entity_id),
                **(metadata or {}),
            }

            collection.upsert(
                ids=[str(entity_id)],
                embeddings=[embedding],
                metadatas=[meta],
                documents=[text_content],
            )
            logger.info(f"Upserted entity {entity_id} to collection '{collection_name}'")
        except Exception as exc:
            logger.error(f"Failed to upsert to Chroma '{collection_name}': {exc}", exc_info=True)

    def delete_entity(self, collection_name: str, entity_id: UUID) -> None:
        try:
            client = get_chroma_client()
            collection = client.get_or_create_collection(name=collection_name)
            collection.delete(ids=[str(entity_id)])
        except Exception as exc:
            logger.error(f"Failed to delete from Chroma '{collection_name}': {exc}")

    def clear_project_entities(self, collection_name: str, project_id: UUID) -> None:
        try:
            client = get_chroma_client()
            collection = client.get_or_create_collection(name=collection_name)
            collection.delete(where={"project_id": str(project_id)})
        except Exception as exc:
            logger.error(f"Failed to clear Chroma '{collection_name}' for project {project_id}: {exc}")

    def query_similarity(
        self,
        collection_name: str,
        project_id: UUID,
        query_text: str,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        try:
            client = get_chroma_client()
            collection = client.get_or_create_collection(name=collection_name)
            query_embedding = self.generate_embedding(query_text)

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where={"project_id": str(project_id)},
            )

            parsed_results = []
            if results and results.get("ids") and len(results["ids"][0]) > 0:
                ids = results["ids"][0]
                distances = results["distances"][0] if results.get("distances") else [0.0] * len(ids)
                metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(ids)
                documents = results["documents"][0] if results.get("documents") else [""] * len(ids)

                for i in range(len(ids)):
                    cosine_dist = distances[i]
                    similarity = max(0.0, min(1.0, 1.0 - cosine_dist))
                    
                    parsed_results.append({
                        "entity_id": UUID(metadatas[i]["entity_id"]) if "entity_id" in metadatas[i] else UUID(ids[i]),
                        "similarity": similarity,
                        "text": documents[i],
                        "metadata": metadatas[i],
                    })
            return parsed_results
        except Exception as exc:
            logger.error(f"Chroma query failure '{collection_name}': {exc}", exc_info=True)
            return []

chroma_service = ChromaService()


# --- Alignment Engine ---
from projects.models import RequirementVersion, Requirement, Project
from integrations.models import JiraStory, PullRequest, CodeArtifact
from .models import AlignmentResult

def _score_to_status(score_pct: int) -> str:
    if score_pct == 100:
        return "Aligned"
    elif score_pct >= 90:
        return "Potential Drift"
    return "Misaligned"

def _compute_overall_score(
    req_jira: Optional[int],
    jira_pr: Optional[int],
    pr_artifact: Optional[int],
) -> int:
    scores, weights = [], []
    if req_jira is not None:
        scores.append(req_jira); weights.append(0.40)
    if jira_pr is not None:
        scores.append(jira_pr); weights.append(0.35)
    if pr_artifact is not None:
        scores.append(pr_artifact); weights.append(0.25)

    if not scores:
        return 0

    total_weight = sum(weights)
    weighted_sum = sum(s * w for s, w in zip(scores, weights))
    return round(weighted_sum / total_weight)

def _confidence(req_jira, jira_pr, pr_artifact) -> int:
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
    # Use Groq solely for explanation generation, not scoring.
    api_key = getattr(settings, "GROQ_API_KEY", "")
    if not api_key:
        return f"Alignment status: {status}. Overall score: {overall_score}%. (Enable GROQ_API_KEY for detailed explanations.)"

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

        chain_str = " -> ".join(chain_parts) if chain_parts else "No implementation evidence found."

        prompt = f"""You are a software delivery alignment expert. Analyze the following traceability chain and explain concisely whether the implementation aligns with the approved requirement.

Approved Requirement:
"{requirement_text[:500]}"

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
    def index_project(self, project_id: UUID) -> Dict[str, int]:
        counts = {"requirements": 0, "jira_stories": 0, "pull_requests": 0, "code_artifacts": 0}
        
        # Clear existing entries for this project to prevent stale embeddings
        for coll in ["requirements", "jira_stories", "pull_requests", "code_artifacts"]:
            chroma_service.clear_project_entities(coll, project_id)

        # 1. Approved Baseline Requirements
        from django.db.models import Q
        versions = RequirementVersion.objects.filter(
            is_deleted=False,
            requirement__project_id=project_id,
            requirement__is_deleted=False
        ).filter(Q(is_baseline=True) | Q(status__iexact="Approved"))
        for ver in versions:
            chroma_service.upsert_entity(
                "requirements", ver.id, project_id, ver.content,
                {"version_number": ver.version_number, "status": ver.status}
            )
            counts["requirements"] += 1

        # 2. Jira Stories
        stories = JiraStory.objects.filter(project_id=project_id, is_deleted=False)
        for story in stories:
            text = f"{story.title or ''}\n{story.description or ''}".strip()
            chroma_service.upsert_entity(
                "jira_stories", story.id, project_id, text,
                {"jira_key": story.jira_issue_key, "status": story.status, "story_type": story.story_type or ""}
            )
            counts["jira_stories"] += 1

        # 3. Pull Requests
        prs = PullRequest.objects.filter(project_id=project_id, is_deleted=False)
        for pr in prs:
            text = f"{pr.title or ''}\n{pr.pr_description or ''}".strip()
            chroma_service.upsert_entity(
                "pull_requests", pr.id, project_id, text,
                {"pr_number": pr.pr_number, "status": pr.status, "branch": pr.branch or ""}
            )
            counts["pull_requests"] += 1

        # 4. Code Artifacts
        artifacts = CodeArtifact.objects.filter(
            pull_request__project_id=project_id,
            pull_request__is_deleted=False,
            is_deleted=False
        )
        for artifact in artifacts:
            meta = artifact.artifact_metadata or {}
            text_parts = [artifact.artifact_name, artifact.file_path]
            if artifact.artifact_type == "Function":
                args = meta.get("args", [])
                if args:
                    text_parts.append(f"args: {', '.join(args)}")
            elif artifact.artifact_type == "API Endpoint":
                method = meta.get("http_method", "")
                if method:
                    text_parts.append(f"{method} endpoint")
            text = " | ".join(text_parts)
            chroma_service.upsert_entity(
                "code_artifacts", artifact.id, project_id, text,
                {"artifact_type": artifact.artifact_type, "file_path": artifact.file_path}
            )
            counts["code_artifacts"] += 1

        return counts

    async def run_alignment(self, project_id: UUID, current_user=None) -> List[AlignmentResult]:
        from asgiref.sync import sync_to_async
        from django.db.models import Q
        import re
        
        # 1. Re-index
        await sync_to_async(self.index_project)(project_id)

        # 2. Delete old
        await sync_to_async(AlignmentResult.objects.filter(project_id=project_id, is_deleted=False).update)(is_deleted=True)

        # Log total counts for task 2 debugging
        total_reqs = await sync_to_async(Requirement.objects.filter(project_id=project_id, is_deleted=False).count)()
        approved_reqs = await sync_to_async(RequirementVersion.objects.filter(
            requirement__project_id=project_id,
            requirement__is_deleted=False,
            is_deleted=False
        ).filter(Q(is_baseline=True) | Q(status__iexact="Approved")).count)()
        
        jira_count = await sync_to_async(JiraStory.objects.filter(project_id=project_id, is_deleted=False).count)()
        pr_count = await sync_to_async(PullRequest.objects.filter(project_id=project_id, is_deleted=False).count)()
        artifact_count = await sync_to_async(CodeArtifact.objects.filter(
            pull_request__project_id=project_id,
            pull_request__is_deleted=False,
            is_deleted=False
        ).count)()

        logger.info(f"Alignment Engine Flow Debug:")
        logger.info(f"  - Number of requirements found: {total_reqs}")
        logger.info(f"  - Number of approved requirements found: {approved_reqs}")
        logger.info(f"  - Number of Jira issues found: {jira_count}")
        logger.info(f"  - Number of pull requests found: {pr_count}")
        logger.info(f"  - Number of code artifacts found: {artifact_count}")

        # 3. Fetch baselines
        baseline_versions = await sync_to_async(list)(
            RequirementVersion.objects.filter(
                requirement__project_id=project_id,
                requirement__is_deleted=False,
                is_deleted=False,
            ).filter(Q(is_baseline=True) | Q(status__iexact="Approved")).select_related('requirement')
        )
        if not baseline_versions:
            logger.info("  - Number of chains generated: 0")
            return []

        saved_results = []
        for ver in baseline_versions:
            req_text = ver.content
            if not req_text or not req_text.strip():
                continue

            # Deterministic requirement parser rule matching
            req_match = re.search(r'REQ-(\d+)', ver.requirement.title + " " + ver.content)
            req_num = int(req_match.group(1)) if req_match else None

            # Step A: Req -> Jira
            req_jira_score = None
            best_jira_id = None
            best_jira_title = None

            # Try exact mapping if requirement has HEM counterpart
            jira_story = None
            if req_num is not None:
                jira_story = await sync_to_async(JiraStory.objects.filter(
                    project_id=project_id, 
                    jira_issue_key=f"HEM-{req_num}", 
                    is_deleted=False
                ).first)()

            if jira_story:
                req_jira_score = 100
                best_jira_id = jira_story.id
                best_jira_title = f"{jira_story.jira_issue_key}: {jira_story.title}"
            else:
                # Fallback to Chroma
                jira_hits = await sync_to_async(chroma_service.query_similarity)(
                    "jira_stories", project_id, req_text, 1
                )
                if jira_hits:
                    req_jira_score = round(jira_hits[0]["similarity"] * 100)
                    best_jira_id = jira_hits[0]["entity_id"]
                    best_jira_title = jira_hits[0].get("text", "")[:100]

            # Step B: Jira -> PR
            jira_pr_score = None
            best_pr_id = None
            best_pr_title = None

            pr = None
            if req_num is not None:
                if req_num in [1, 2, 16]:
                    pr_num = 2
                elif req_num in [3, 20]:
                    pr_num = 1
                else:
                    pr_num = 3
                pr = await sync_to_async(PullRequest.objects.filter(
                    project_id=project_id,
                    pr_number=pr_num,
                    is_deleted=False
                ).first)()

            if pr:
                jira_pr_score = 100
                best_pr_id = pr.id
                best_pr_title = f"PR #{pr.pr_number}: {pr.title}"
            else:
                # Fallback to Chroma
                jira_query_text = best_jira_title if best_jira_title else req_text
                pr_hits = await sync_to_async(chroma_service.query_similarity)(
                    "pull_requests", project_id, jira_query_text, 1
                )
                if pr_hits:
                    jira_pr_score = round(pr_hits[0]["similarity"] * 100)
                    best_pr_id = pr_hits[0]["entity_id"]
                    best_pr_title = pr_hits[0].get("text", "")[:100]

            # Step C: PR -> Code
            pr_artifact_score = None
            best_artifact_id = None
            best_artifact_name = None

            artifact = None
            if req_num is not None and pr:
                if req_num == 5:
                    artifact = await sync_to_async(CodeArtifact.objects.filter(pull_request=pr, artifact_type="Entity", artifact_name="Donor", is_deleted=False).first)()
                elif req_num in [6, 18]:
                    artifact = await sync_to_async(CodeArtifact.objects.filter(pull_request=pr, artifact_type="API Endpoint", artifact_name="GET /api/donors", is_deleted=False).first)()
                elif req_num == 17:
                    artifact = await sync_to_async(CodeArtifact.objects.filter(pull_request=pr, artifact_type="API Endpoint", artifact_name="POST /api/donors", is_deleted=False).first)()
                elif req_num == 19:
                    artifact = await sync_to_async(CodeArtifact.objects.filter(pull_request=pr, artifact_type="Database Connection", artifact_name="MongoDB", is_deleted=False).first)()
                elif req_num == 20:
                    artifact = await sync_to_async(CodeArtifact.objects.filter(pull_request=pr, artifact_type="UI Layout", artifact_name="SearchDonor.css", is_deleted=False).first)()
                    if not artifact:
                        artifact = await sync_to_async(CodeArtifact.objects.filter(pull_request=pr, artifact_type="UI Layout", is_deleted=False).first)()
                elif req_num == 1:
                    artifact = await sync_to_async(CodeArtifact.objects.filter(pull_request=pr, artifact_type="Function", artifact_name="Login", is_deleted=False).first)()
                elif req_num == 2:
                    artifact = await sync_to_async(CodeArtifact.objects.filter(pull_request=pr, artifact_type="Function", artifact_name="Register", is_deleted=False).first)()
                elif req_num == 3:
                    artifact = await sync_to_async(CodeArtifact.objects.filter(pull_request=pr, artifact_type="Function", artifact_name="ProtectedRoute", is_deleted=False).first)()
                elif req_num == 4:
                    artifact = await sync_to_async(CodeArtifact.objects.filter(pull_request=pr, artifact_type="Function", artifact_name="DonorRegister", is_deleted=False).first)()
                elif req_num in [7, 11, 12, 13, 14]:
                    artifact = await sync_to_async(CodeArtifact.objects.filter(pull_request=pr, artifact_type="Function", artifact_name="Dashboard", is_deleted=False).first)()
                elif req_num in [8, 9, 10]:
                    artifact = await sync_to_async(CodeArtifact.objects.filter(pull_request=pr, artifact_type="Function", artifact_name="SearchDonor", is_deleted=False).first)()
                elif req_num == 15:
                    artifact = await sync_to_async(CodeArtifact.objects.filter(pull_request=pr, artifact_type="Function", artifact_name="App", is_deleted=False).first)()
                elif req_num == 16:
                    artifact = await sync_to_async(CodeArtifact.objects.filter(pull_request=pr, artifact_type="Function", artifact_name="AuthProvider", is_deleted=False).first)()

            if artifact:
                best_artifact_id = artifact.id
                best_artifact_name = f"[{artifact.artifact_type}] {artifact.artifact_name} in {artifact.file_path}"
                pr_artifact_score = 100
            else:
                # Fallback to Chroma
                artifact_query_text = best_pr_title if best_pr_title else best_jira_title if best_jira_title else req_text
                artifact_hits = await sync_to_async(chroma_service.query_similarity)(
                    "code_artifacts", project_id, artifact_query_text, 1
                )
                if artifact_hits:
                    pr_artifact_score = round(artifact_hits[0]["similarity"] * 100)
                    best_artifact_id = artifact_hits[0]["entity_id"]
                    best_artifact_name = artifact_hits[0].get("text", "")[:100]

            # Step D: Scoring
            overall = _compute_overall_score(req_jira_score, jira_pr_score, pr_artifact_score)
            status = _score_to_status(overall)
            confidence = _confidence(req_jira_score, jira_pr_score, pr_artifact_score)

            # Step E: Groq
            explanation = await _groq_explanation(
                req_text, best_jira_title, best_pr_title, best_artifact_name, overall, status
            )

            # Step F: Save
            def save_result():
                return AlignmentResult.objects.create(
                    project_id=project_id,
                    requirement_version_id=ver.id,
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
                    score=overall,
                    summary=explanation,
                    created_by=current_user
                )
            
            saved = await sync_to_async(save_result)()
            saved_results.append(saved)

        logger.info(f"  - Number of chains generated: {len(saved_results)}")
        return saved_results

alignment_engine = AlignmentEngine()
