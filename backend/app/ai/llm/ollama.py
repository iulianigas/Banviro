import httpx

from app.ai.logging import ai_logger
from app.config import settings


class OllamaClient:
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout_seconds

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def generate(self, system: str, prompt: str) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "keep_alive": settings.ollama_keep_alive,
            "options": {
                "num_predict": settings.ollama_num_predict,
                "temperature": settings.ollama_temperature,
            },
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        ai_logger.info(
            "ollama generate start model=%s prompt_chars=%d timeout=%ss",
            self.model,
            len(prompt),
            self.timeout,
        )
        try:
            async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
                reply = str(data["message"]["content"])
                ai_logger.info("ollama generate done reply_chars=%d", len(reply))
                return reply
        except httpx.TimeoutException as exc:
            ai_logger.error("ollama generate timeout after %ss", self.timeout)
            raise TimeoutError(
                f"Ollama nu a răspuns în {self.timeout}s. "
                "Prima încărcare a modelului pe CPU poate dura 1–3 minute. "
                "Verifică: docker logs -f banviro-ollama"
            ) from exc
        except httpx.HTTPError as exc:
            ai_logger.error("ollama generate failed: %s", exc)
            raise RuntimeError(
                f"Eroare Ollama: {exc}. Verifică: docker logs -f banviro-ollama"
            ) from exc


ollama_client = OllamaClient()
