import httpx

from app.ai.llm.ollama import ollama_client
from app.ai.logging import ai_logger
from app.ai.tracing import record_io, span_kind, trace_span
from app.config import settings


class QdrantRetriever:
    """RAG retriever — indexes and searches transactions via Qdrant REST API."""

    def __init__(self) -> None:
        self.base_url = settings.qdrant_url.rstrip("/")
        self.collection = settings.qdrant_collection
        self.vector_size = settings.qdrant_vector_size

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/collections")
                return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def ensure_collection(self) -> bool:
        if not await self.is_available():
            return False

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/collections/{self.collection}")
            if response.status_code == 200:
                return True

            create_response = await client.put(
                f"{self.base_url}/collections/{self.collection}",
                json={
                    "vectors": {
                        "size": self.vector_size,
                        "distance": "Cosine",
                    }
                },
            )
            if create_response.status_code not in (200, 201):
                ai_logger.error(
                    "qdrant create collection failed status=%s body=%s",
                    create_response.status_code,
                    create_response.text,
                )
                return False

        ai_logger.info("qdrant collection ready name=%s", self.collection)
        return True

    async def upsert_point(
        self,
        point_id: int,
        text: str,
        user_id: int,
        transaction_id: int,
    ) -> bool:
        with trace_span(
            "qdrant.upsert",
            **span_kind("retriever"),
            user_id=user_id,
            transaction_id=transaction_id,
            collection=self.collection,
        ) as span:
            record_io(span, input_value=text)
            if not await self.ensure_collection():
                return False

            try:
                vector = await ollama_client.embed(text)
            except RuntimeError:
                return False

            if len(vector) != self.vector_size:
                ai_logger.error(
                    "embedding size mismatch expected=%d got=%d model=%s",
                    self.vector_size,
                    len(vector),
                    settings.ollama_embed_model,
                )
                return False

            payload = {
                "points": [
                    {
                        "id": point_id,
                        "vector": vector,
                        "payload": {
                            "user_id": user_id,
                            "transaction_id": transaction_id,
                            "text": text,
                        },
                    }
                ]
            }
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.put(
                        f"{self.base_url}/collections/{self.collection}/points",
                        params={"wait": "true"},
                        json=payload,
                    )
                    if response.status_code not in (200, 201):
                        ai_logger.error(
                            "qdrant upsert failed status=%s body=%s",
                            response.status_code,
                            response.text,
                        )
                        return False
            except httpx.HTTPError as exc:
                ai_logger.error("qdrant upsert failed: %s", exc)
                return False

            record_io(span, output_value=f"point_id={point_id}")
            return True

    async def delete_points(self, point_ids: list[int]) -> bool:
        if not point_ids or not await self.is_available():
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/collections/{self.collection}/points/delete",
                    params={"wait": "true"},
                    json={"points": point_ids},
                )
                return response.status_code in (200, 201)
        except httpx.HTTPError as exc:
            ai_logger.error("qdrant delete failed: %s", exc)
            return False

    async def search(self, query: str, user_id: int, limit: int = 5) -> list[str]:
        with trace_span(
            "qdrant.search",
            **span_kind("retriever"),
            user_id=user_id,
            collection=self.collection,
            limit=limit,
        ) as span:
            record_io(span, input_value=query)
            if not await self.is_available():
                return []

            try:
                vector = await ollama_client.embed(query)
            except RuntimeError:
                return []

            payload = {
                "vector": vector,
                "limit": limit,
                "with_payload": True,
                "filter": {
                    "must": [{"key": "user_id", "match": {"value": user_id}}]
                },
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{self.base_url}/collections/{self.collection}/points/search",
                        json=payload,
                    )
                    if response.status_code != 200:
                        return []
                    hits = response.json().get("result", [])
                    snippets = [
                        str(hit.get("payload", {}).get("text", ""))
                        for hit in hits
                        if hit.get("payload", {}).get("text")
                    ]
                    record_io(span, output_value="\n".join(snippets))
                    if span is not None:
                        span.set_attribute("retrieval.hits", len(snippets))
                    return snippets
            except httpx.HTTPError:
                return []


qdrant_retriever = QdrantRetriever()
