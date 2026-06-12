"""Phoenix OpenTelemetry setup and span helpers for the AI layer."""

from __future__ import annotations

import logging
from contextlib import AbstractContextManager, ExitStack, asynccontextmanager, contextmanager
from typing import Any, AsyncIterator, Iterator

from app.config import settings

logger = logging.getLogger("banviro.ai")

_initialized = False


def setup_phoenix_tracing() -> bool:
    """Register the Phoenix tracer provider and LangChain/LangGraph auto-instrumentation."""
    global _initialized

    if _initialized:
        return True

    if not settings.phoenix_enabled:
        logger.info("Phoenix tracing disabled via configuration")
        return False

    try:
        from phoenix.otel import register

        register(
            project_name=settings.phoenix_project_name,
            endpoint=settings.phoenix_collector_endpoint,
            protocol=settings.phoenix_collector_protocol,
            auto_instrument=True,
            batch=True,
        )
        _initialized = True
        logger.info(
            "Phoenix tracing enabled project=%s endpoint=%s protocol=%s",
            settings.phoenix_project_name,
            settings.phoenix_collector_endpoint,
            settings.phoenix_collector_protocol,
        )
        return True
    except Exception as exc:
        logger.warning("Phoenix tracing setup failed: %s", exc)
        return False


def is_tracing_enabled() -> bool:
    return _initialized


def get_tracer(name: str = "banviro.ai"):
    from opentelemetry import trace

    return trace.get_tracer(name)


def _safe_attr(value: Any) -> str | int | float | bool:
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _set_span_attributes(span: Any, attributes: dict[str, Any]) -> None:
    for key, value in attributes.items():
        if value is not None:
            span.set_attribute(key, _safe_attr(value))


@contextmanager
def trace_span(name: str, /, **attributes: Any) -> Iterator[Any]:
    if not _initialized:
        yield None
        return

    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        _set_span_attributes(span, attributes)
        yield span


@asynccontextmanager
async def trace_span_async(name: str, /, **attributes: Any) -> AsyncIterator[Any]:
    with trace_span(name, **attributes) as span:
        yield span


@contextmanager
def chat_trace_context(
    user_id: int,
    locale: str,
    message: str,
) -> Iterator[None]:
    """Attach session, user, and request metadata to the active trace."""
    if not _initialized:
        yield
        return

    from phoenix.otel import using_metadata, using_session, using_user

    with ExitStack() as stack:
        stack.enter_context(using_session(f"user-{user_id}"))
        stack.enter_context(using_user(str(user_id)))
        stack.enter_context(
            using_metadata(
                {
                    "locale": locale,
                    "message_chars": len(message),
                }
            )
        )
        yield


def span_kind(kind: str) -> dict[str, str]:
    from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

    values = {
        "agent": OpenInferenceSpanKindValues.AGENT.value,
        "chain": OpenInferenceSpanKindValues.CHAIN.value,
        "llm": OpenInferenceSpanKindValues.LLM.value,
        "retriever": OpenInferenceSpanKindValues.RETRIEVER.value,
        "tool": OpenInferenceSpanKindValues.TOOL.value,
    }
    return {SpanAttributes.OPENINFERENCE_SPAN_KIND: values.get(kind, kind)}


def record_io(span: Any, *, input_value: str | None = None, output_value: str | None = None) -> None:
    if span is None:
        return

    from openinference.semconv.trace import SpanAttributes

    if input_value is not None:
        span.set_attribute(SpanAttributes.INPUT_VALUE, input_value[:4000])
    if output_value is not None:
        span.set_attribute(SpanAttributes.OUTPUT_VALUE, output_value[:4000])


def noop_context() -> AbstractContextManager[None]:
    from contextlib import nullcontext

    return nullcontext()
