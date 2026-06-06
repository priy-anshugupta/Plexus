"""
Plexus Backend — Vector Service

Manages semantic code indexing and vector searches in Qdrant.  Splits files
into line-based overlapping chunks, generates embeddings (using OpenAI or
a synthetic fallback if offline), and indexes them for vector-based RAG.
"""

from __future__ import annotations

import logging
import math
import random
from uuid import UUID, uuid4, uuid5, NAMESPACE_URL

from langchain_openai import OpenAIEmbeddings
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from app.core.config import settings
from app.core.database import db_manager

logger = logging.getLogger(__name__)


class VectorService:
    """Service to chunk, embed, index, and query code files in Qdrant."""

    def __init__(self) -> None:
        # Initialise the embedding model if API key is provided
        if settings.openai_api_key:
            self._embeddings = OpenAIEmbeddings(
                openai_api_key=settings.openai_api_key,
                model="text-embedding-3-small",  # 1536 dims
            )
            logger.info("OpenAIEmbeddings initialized successfully.")
        else:
            self._embeddings = None
            logger.info("OpenAI API key missing. Vector service will use mock synthetic embeddings.")

    @property
    def is_connected(self) -> bool:
        """Checks if Qdrant backend is connected and online."""
        return db_manager.qdrant_client is not None

    # ------------------------------------------------------------------
    # Collection Setup
    # ------------------------------------------------------------------

    def initialize_collections(self) -> None:
        """Ensures the required vector collections exist in Qdrant."""
        if not self.is_connected or db_manager.qdrant_client is None:
            logger.info("Qdrant offline. Skipping initialize_collections.")
            return

        collection_name = "code_chunks"
        try:
            # Check if collection already exists
            collections = db_manager.qdrant_client.get_collections().collections
            exists = any(col.name == collection_name for col in collections)

            if not exists:
                logger.info("Creating vector collection: %s", collection_name)
                db_manager.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # text-embedding-3-small dimension
                        distance=Distance.COSINE,
                    ),
                )
                logger.info("Collection %s created successfully.", collection_name)
            else:
                logger.info("Collection %s already exists.", collection_name)
        except Exception as exc:
            logger.error("Failed to initialize Qdrant collections: %s", exc)

    # ------------------------------------------------------------------
    # Index Chunks
    # ------------------------------------------------------------------

    def upsert_file_chunks(
        self,
        repo_id: UUID,
        file_path: str,
        code_content: str,
    ) -> None:
        """Splits file code content, generates embeddings, and indexes in Qdrant.

        Args:
            repo_id: Repository UUID.
            file_path: Relative path of the file.
            code_content: Raw source code string.
        """
        if not self.is_connected or db_manager.qdrant_client is None:
            logger.info("Qdrant offline. Skipping upsert_file_chunks for %s", file_path)
            return

        # 1. Clear any old vector points for this file
        self.delete_file_chunks(repo_id, file_path)

        # 2. Chunk the file (line-based sliding window)
        chunks = self._chunk_code(code_content)
        if not chunks:
            return

        repo_id_str = str(repo_id)
        chunk_texts = [c["text"] for c in chunks]

        # 3. Generate embeddings
        try:
            embeddings_list = self._get_embeddings(chunk_texts)
        except Exception as exc:
            logger.warning("Embeddings generation failed for %s: %s. Using synthetic vectors.", file_path, exc)
            embeddings_list = [self._generate_mock_embedding() for _ in chunks]

        # 4. Construct PointStruct payloads
        points = []
        for idx, (chunk, vector) in enumerate(zip(chunks, embeddings_list)):
            # Generate a deterministic UUID for the point based on path & chunk index
            point_id = uuid5(NAMESPACE_URL, f"{repo_id_str}:{file_path}:{idx}")
            
            points.append(
                PointStruct(
                    id=str(point_id),
                    vector=vector,
                    payload={
                        "repo_id": repo_id_str,
                        "file_path": file_path,
                        "text": chunk["text"],
                        "line_start": chunk["line_start"],
                        "line_end": chunk["line_end"],
                    },
                )
            )

        # 5. Upsert to Qdrant
        try:
            db_manager.qdrant_client.upsert(
                collection_name="code_chunks",
                points=points,
            )
            logger.info("Indexed %d semantic chunks in Qdrant for: %s", len(points), file_path)
        except Exception as exc:
            logger.error("Failed to upsert vectors in Qdrant for %s: %s", file_path, exc)

    def delete_file_chunks(self, repo_id: UUID, file_path: str) -> None:
        """Deletes all indexed vector points associated with a repository file.

        Args:
            repo_id: Repository UUID.
            file_path: Relative path of the file.
        """
        if not self.is_connected or db_manager.qdrant_client is None:
            return

        try:
            db_manager.qdrant_client.delete(
                collection_name="code_chunks",
                points_selector=Filter(
                    must=[
                        FieldCondition(key="repo_id", match=MatchValue(value=str(repo_id))),
                        FieldCondition(key="file_path", match=MatchValue(value=file_path)),
                    ]
                ),
            )
        except Exception as exc:
            logger.error("Failed to delete Qdrant vectors for %s: %s", file_path, exc)

    # ------------------------------------------------------------------
    # Semantic Search
    # ------------------------------------------------------------------

    def semantic_search(
        self,
        repo_id: UUID,
        query: str,
        limit: int = 5,
    ) -> list[dict]:
        """Queries Qdrant for code chunks semantically similar to the query.

        Args:
            repo_id: Repository UUID to scope the search filter.
            query: Natural language query string.
            limit: Maximum search results.

        Returns:
            A list of matching code chunk dicts with scores:
            [{ "file_path": str, "text": str, "line_start": int, "score": float }]
        """
        if not self.is_connected or db_manager.qdrant_client is None:
            logger.info("Qdrant offline. Returning empty semantic search results.")
            return []

        # 1. Embed search query
        try:
            query_vector = self._get_embeddings([query])[0]
        except Exception as exc:
            logger.warning("Failed to embed query: %s. Using synthetic query vector.", exc)
            query_vector = self._generate_mock_embedding()

        # 2. Query Qdrant with filters
        try:
            results = db_manager.qdrant_client.search(
                collection_name="code_chunks",
                query_vector=query_vector,
                query_filter=Filter(
                    must=[
                        FieldCondition(key="repo_id", match=MatchValue(value=str(repo_id)))
                    ]
                ),
                limit=limit,
            )

            matches = []
            for hit in results:
                payload = hit.payload or {}
                matches.append({
                    "file_path": payload.get("file_path"),
                    "text": payload.get("text"),
                    "line_start": payload.get("line_start"),
                    "line_end": payload.get("line_end"),
                    "score": hit.score,
                })
            return matches
        except Exception as exc:
            logger.error("Qdrant search query failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Private Helpers: Chunking & Embedding Fallback
    # ------------------------------------------------------------------

    def _chunk_code(
        self,
        code: str,
        chunk_size_lines: int = 30,
        overlap_lines: int = 5,
    ) -> list[dict]:
        """Splits code content into overlapping line-based text chunks."""
        lines = code.splitlines()
        if not lines:
            return []

        chunks = []
        num_lines = len(lines)
        step = chunk_size_lines - overlap_lines

        # Prevent division by zero
        if step <= 0:
            step = chunk_size_lines

        for start in range(0, num_lines, step):
            end = min(start + chunk_size_lines, num_lines)
            chunk_text = "\n".join(lines[start:end])
            
            # Skip empty chunks
            if chunk_text.strip():
                chunks.append({
                    "text": chunk_text,
                    "line_start": start + 1,
                    "line_end": end,
                })
            
            if end == num_lines:
                break

        return chunks

    def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Invokes OpenAI API to generate embeddings. Falls back to mock values."""
        if self._embeddings:
            return self._embeddings.embed_documents(texts)
        raise RuntimeError("No embedding provider initialized.")

    def _generate_mock_embedding(self) -> list[float]:
        """Generates a random L2-normalised float vector of size 1536.

        L2 normalisation ensures that dot-product and cosine distance computations
        remain mathematically consistent during testing.
        """
        raw_vector = [random.uniform(-1.0, 1.0) for _ in range(1536)]
        magnitude = math.sqrt(sum(x * x for x in raw_vector))
        if magnitude == 0:
            return [0.0] * 1536
        return [x / magnitude for x in raw_vector]
