def _needs_rag(message: str) -> bool:
    keywords = (
        "de ce",
        "why",
        "explic",
        "explain",
        "analiz",
        "analy",
        "compar",
        "tendin",
        "trend",
        "pattern",
        "sfat",
        "advice",
    )
    lowered = message.lower()
    return any(word in lowered for word in keywords)


def should_use_rag(message: str) -> bool:
    return _needs_rag(message)
