from unittest.mock import patch

from app.ai.tracing import is_tracing_enabled, setup_phoenix_tracing, trace_span


def test_setup_phoenix_tracing_disabled() -> None:
    with patch("app.ai.tracing.settings.phoenix_enabled", False):
        from app.ai import tracing

        tracing._initialized = False
        assert setup_phoenix_tracing() is False
        assert is_tracing_enabled() is False


def test_trace_span_noop_when_tracing_disabled() -> None:
    from app.ai import tracing

    tracing._initialized = False
    with trace_span("test.span", sample="value") as span:
        assert span is None
