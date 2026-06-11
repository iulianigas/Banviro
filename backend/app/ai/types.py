from dataclasses import dataclass, field


@dataclass
class ChatContext:
    user_id: int
    user_email: str
    summary_text: str = ""
    recent_transactions: str = ""
    rag_snippets: list[str] = field(default_factory=list)


@dataclass
class ChatResult:
    reply: str
    used_tools: list[str] = field(default_factory=list)
    used_rag: bool = False
    model: str = ""
