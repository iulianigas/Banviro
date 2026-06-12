import json
from collections.abc import AsyncIterator

import httpx

from app.ai.logging import ai_logger
from app.ai.tracing import record_io, span_kind, trace_span
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

    async def embed(self, text: str) -> list[float]:
        from openinference.semconv.trace import SpanAttributes

        payload = {
            "model": settings.ollama_embed_model,
            "input": text,
        }
        with trace_span(
            "ollama.embed",
            **span_kind("llm"),
            **{SpanAttributes.LLM_MODEL_NAME: settings.ollama_embed_model},
        ) as span:
            record_io(span, input_value=text)
            try:
                async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                    response = await client.post(f"{self.base_url}/api/embed", json=payload)
                    response.raise_for_status()
                    data = response.json()
                    embeddings = data.get("embeddings")
                    if isinstance(embeddings, list) and embeddings:
                        vector = [float(value) for value in embeddings[0]]
                        if span is not None:
                            span.set_attribute("embedding.dimensions", len(vector))
                        return vector
            except httpx.HTTPError as exc:
                ai_logger.error("ollama embed failed: %s", exc)
                raise RuntimeError(f"Eroare embedding Ollama: {exc}") from exc

            raise RuntimeError("Ollama embed response missing embeddings")

    async def generate(
        self,
        system: str,
        prompt: str,
        *,
        num_predict: int | None = None,
        temperature: float | None = None,
    ) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "keep_alive": settings.ollama_keep_alive,
            "options": {
                "num_predict": num_predict if num_predict is not None else settings.ollama_num_predict,
                "temperature": temperature if temperature is not None else settings.ollama_temperature,
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
        from openinference.semconv.trace import SpanAttributes

        with trace_span(
            "ollama.generate",
            **span_kind("llm"),
            **{SpanAttributes.LLM_MODEL_NAME: self.model},
        ) as span:
            record_io(span, input_value=f"{system}\n\n{prompt}")
            try:
                async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                    response = await client.post(f"{self.base_url}/api/chat", json=payload)
                    response.raise_for_status()
                    data = response.json()
                    reply = str(data["message"]["content"])
                    ai_logger.info("ollama generate done reply_chars=%d", len(reply))
                    record_io(span, output_value=reply)
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

    async def generate_stream(self, system: str, prompt: str) -> AsyncIterator[str]:
        payload = {
            "model": self.model,
            "stream": True,
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
            "ollama stream start model=%s prompt_chars=%d",
            self.model,
            len(prompt),
        )
        from openinference.semconv.trace import SpanAttributes

        with trace_span(
            "ollama.generate_stream",
            **span_kind("llm"),
            **{SpanAttributes.LLM_MODEL_NAME: self.model},
        ) as span:
            record_io(span, input_value=f"{system}\n\n{prompt}")
            chunks: list[str] = []
            try:
                async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/api/chat",
                        json=payload,
                    ) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if not line:
                                continue
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                text = str(content)
                                chunks.append(text)
                                yield text
                            if data.get("done"):
                                break
                record_io(span, output_value="".join(chunks))
            except httpx.TimeoutException as exc:
                ai_logger.error("ollama stream timeout after %ss", self.timeout)
                raise TimeoutError(
                    f"Ollama nu a răspuns în {self.timeout}s. "
                    "Prima încărcare a modelului pe CPU poate dura 1–3 minute."
                ) from exc
            except httpx.HTTPError as exc:
                ai_logger.error("ollama stream failed: %s", exc)
                raise RuntimeError(f"Eroare Ollama: {exc}") from exc


ollama_client = OllamaClient()
