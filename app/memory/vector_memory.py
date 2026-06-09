"""
Persistent vector memory using ChromaDB (in-memory client).
Falls back to a keyword-based dict store if chromadb is not installed.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import chromadb  # type: ignore

    _CHROMA_AVAILABLE = True
except ImportError:
    _CHROMA_AVAILABLE = False
    logger.warning("chromadb not installed — using in-memory keyword fallback.")


class VectorMemory:
    def __init__(self, collection_name: str = "enterprise_memory"):
        self._name = collection_name
        self._collection = None
        self._fallback: dict[str, dict[str, Any]] = {}
        self._init()

    def _init(self) -> None:
        if not _CHROMA_AVAILABLE:
            return
        try:
            client = chromadb.Client()
            self._collection = client.get_or_create_collection(
                name=self._name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB collection '%s' ready.", self._name)
        except Exception as exc:
            logger.warning("ChromaDB init failed (%s) — using fallback.", exc)
            self._collection = None

    def store(self, content: str, metadata: Optional[dict[str, Any]] = None) -> str:
        doc_id = str(uuid.uuid4())
        raw_meta = {k: str(v) for k, v in (metadata or {}).items()}
        # ChromaDB 1.5+ rejects empty metadata dicts — use None instead
        meta = raw_meta if raw_meta else None

        if self._collection is not None:
            add_kwargs: dict = {"documents": [content], "ids": [doc_id]}
            if meta is not None:
                add_kwargs["metadatas"] = [meta]
            self._collection.add(**add_kwargs)
        else:
            self._fallback[doc_id] = {"content": content, "metadata": meta or {}}

        logger.debug("Stored memory doc %s (%d chars)", doc_id[:8], len(content))
        return doc_id

    def retrieve(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        if self._collection is not None:
            count = self._collection.count()
            if count == 0:
                return []
            results = self._collection.query(
                query_texts=[query],
                n_results=min(n_results, count),
            )
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            return [
                {"content": d, "metadata": m, "distance": dist}
                for d, m, dist in zip(docs, metas, distances)
            ]

        # Keyword fallback
        query_words = set(query.lower().split())
        scored: list[tuple[float, dict[str, Any]]] = []
        for item in self._fallback.values():
            content_words = set(item["content"].lower().split())
            overlap = len(query_words & content_words)
            if overlap:
                scored.append((overlap, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"content": i["content"], "metadata": i["metadata"], "distance": 0.0} for _, i in scored[:n_results]]

    def count(self) -> int:
        if self._collection is not None:
            return self._collection.count()
        return len(self._fallback)

    def list_all(self) -> list[dict[str, Any]]:
        if self._collection is not None:
            result = self._collection.get()
            docs = result.get("documents") or []
            metas = result.get("metadatas") or []
            return [{"content": d, "metadata": m} for d, m in zip(docs, metas)]
        return [{"content": v["content"], "metadata": v["metadata"]} for v in self._fallback.values()]


# Module-level singleton
_memory: Optional[VectorMemory] = None


def get_memory() -> VectorMemory:
    global _memory
    if _memory is None:
        _memory = VectorMemory()
    return _memory
