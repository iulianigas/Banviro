import httpx

from app.config import settings


class QdrantRetriever:
    """Lightweight RAG retriever — indexes/searches via Qdrant REST API."""

    def __init__(self) -> None:
        self.base_url = settings.qdrant_url.rstrip("/")
        self.collection = settings.qdrant_collection

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/collections")
                return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def search(self, query: str, limit: int = 5) -> list[str]:
        if not await self.is_available():
            return []

        payload = {
            "vector": await self._embed_query(query),
            "limit": limit,
            "with_payload": True,
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
                return [
                    str(hit.get("payload", {}).get("text", ""))
                    for hit in hits
                    if hit.get("payload", {}).get("text")
                ]
        except httpx.HTTPError:
            return []

    async def _embed_query(self, query: str) -> list[float]:
        """Placeholder — replace with Ollama embeddings when collection is populated."""
        _ = query
        return [0.0] * 384


qdrant_retriever = QdrantRetriever()
