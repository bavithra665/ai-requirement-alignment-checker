"""
ChromaDB Vector Service
Handles persistent storage of embeddings for Requirements, Jira Stories, PRs, and Code Artifacts.
Uses SentenceTransformers (all-MiniLM-L6-v2) for local embedding generation.
"""
from __future__ import annotations

import os
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

# Lazy load heavy AI models to optimize application boot time
_client = None
_embed_model = None


def get_chroma_client():
    global _client
    if _client is None:
        import chromadb
        # Store Chroma DB under the api workspace root
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db")
        os.makedirs(db_path, exist_ok=True)
        _client = chromadb.PersistentClient(path=db_path)
    return _client


def get_embedding_model():
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        # Download and cache all-MiniLM-L6-v2 locally (~120MB)
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embed_model


class ChromaService:
    def generate_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for a given text string using local MiniLM model."""
        if not text or not text.strip():
            # Return empty/zero vector of 384 dimensions if text is empty
            return [0.0] * 384
        model = get_embedding_model()
        # Ensure single string input and return as list of floats
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
        """
        Embed and store/update a document in a specific collection.
        This is called during artifact creation/sync to avoid regenerating embeddings every run.
        """
        try:
            client = get_chroma_client()
            collection = client.get_or_create_collection(name=collection_name)

            embedding = self.generate_embedding(text_content)

            # Combine custom metadata with core structural metadata
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
            logger.info(f"Successfully upserted entity {entity_id} to collection '{collection_name}'")
        except Exception as exc:
            logger.error(f"Failed to upsert to Chroma collection '{collection_name}': {exc}", exc_info=True)

    def delete_entity(self, collection_name: str, entity_id: UUID) -> None:
        """Remove a document from a specific collection by its UUID."""
        try:
            client = get_chroma_client()
            collection = client.get_or_create_collection(name=collection_name)
            collection.delete(ids=[str(entity_id)])
            logger.info(f"Successfully deleted entity {entity_id} from collection '{collection_name}'")
        except Exception as exc:
            logger.error(f"Failed to delete from Chroma collection '{collection_name}': {exc}")

    def query_similarity(
        self,
        collection_name: str,
        project_id: UUID,
        query_text: str,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Query Chroma DB for the most similar items in a collection for a given project.
        Uses cosine distance similarity calculation.
        """
        try:
            client = get_chroma_client()
            collection = client.get_or_create_collection(name=collection_name)

            query_embedding = self.generate_embedding(query_text)

            # Filter by project_id to keep queries scoped
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where={"project_id": str(project_id)},
            )

            # Parse results into a clean list of matches
            parsed_results = []
            if results and results.get("ids") and len(results["ids"][0]) > 0:
                ids = results["ids"][0]
                distances = results["distances"][0] if results.get("distances") else [0.0] * len(ids)
                metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(ids)
                documents = results["documents"][0] if results.get("documents") else [""] * len(ids)

                for i in range(len(ids)):
                    # Distances in Chroma are L2 / squared L2 by default, or cosine distance (1 - cosine_similarity).
                    # We assume cosine distance is configured (which is default for some setups, or can be specified).
                    # Let's convert distance to a similarity score (0 to 1.0).
                    # Chroma cosine distance = 1 - cosine_similarity. So cosine_similarity = 1 - distance.
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
            logger.error(f"Chroma query failure in '{collection_name}': {exc}", exc_info=True)
            return []


chroma_service = ChromaService()
