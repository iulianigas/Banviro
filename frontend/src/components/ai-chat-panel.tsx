"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { ChatResponse, getAiStatus, sendAiChat } from "@/lib/api";
import { useI18n } from "@/lib/i18n/context";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  meta?: Pick<ChatResponse, "model" | "used_tools" | "used_rag">;
};

type AiChatPanelProps = {
  accessToken: string;
  periodLabel: string;
};

function createId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function AiChatPanel({ accessToken, periodLabel }: AiChatPanelProps) {
  const { locale, t } = useI18n();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiReady, setAiReady] = useState<boolean | null>(null);
  const [model, setModel] = useState<string>("");
  const [loadingSeconds, setLoadingSeconds] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const prompts = useMemo(
    () => [
      t("ai.promptFinance", { period: periodLabel }),
      t("ai.promptCategory"),
      t("ai.promptBudget"),
      t("ai.promptTrend"),
    ],
    [periodLabel, t]
  );

  useEffect(() => {
    getAiStatus()
      .then((status) => {
        setAiReady(status.ai_enabled && status.ollama_available);
        setModel(status.model);
      })
      .catch(() => setAiReady(false));
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (!loading) {
      setLoadingSeconds(0);
      return;
    }

    setLoadingSeconds(0);
    const interval = window.setInterval(() => {
      setLoadingSeconds((seconds) => seconds + 1);
    }, 1000);

    return () => window.clearInterval(interval);
  }, [loading]);

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setError(null);
    setInput("");
    setMessages((prev) => [...prev, { id: createId(), role: "user", content: trimmed }]);
    setLoading(true);

    try {
      const response = await sendAiChat(accessToken, trimmed, locale);
      setMessages((prev) => [
        ...prev,
        {
          id: createId(),
          role: "assistant",
          content: response.reply,
          meta: {
            model: response.model,
            used_tools: response.used_tools,
            used_rag: response.used_rag,
          },
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("ai.sendError"));
    } finally {
      setLoading(false);
      textareaRef.current?.focus();
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void sendMessage(input);
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void sendMessage(input);
    }
  }

  const disabled = loading || aiReady === false;

  return (
    <article className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <header className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 px-6 py-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{t("ai.title")}</h2>
          <p className="mt-1 text-sm text-slate-500">{t("ai.subtitle")}</p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 font-medium ${
              aiReady ? "bg-green-50 text-green-700" : "bg-amber-50 text-amber-700"
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${aiReady ? "bg-green-500" : "bg-amber-500"}`}
            />
            {aiReady === null
              ? t("ai.checking")
              : aiReady
                ? `Ollama · ${model}`
                : t("ai.offline")}
          </span>
        </div>
      </header>

      <div className="flex h-[420px] flex-col">
        <div className="flex-1 space-y-4 overflow-y-auto px-6 py-4">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col justify-center">
              <p className="text-center text-sm text-slate-500">{t("ai.emptyHint")}</p>
              <div className="mt-4 flex flex-wrap justify-center gap-2">
                {prompts.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    disabled={disabled}
                    onClick={() => void sendMessage(prompt)}
                    className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-left text-xs text-slate-700 transition hover:border-brand-300 hover:bg-brand-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    message.role === "user"
                      ? "bg-brand-600 text-white"
                      : "bg-slate-100 text-slate-800"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  {message.role === "assistant" && message.meta ? (
                    <div className="mt-2 flex flex-wrap gap-1.5 border-t border-slate-200/80 pt-2">
                      {message.meta.model ? (
                        <span className="rounded bg-white/70 px-1.5 py-0.5 text-[10px] text-slate-500">
                          {message.meta.model}
                        </span>
                      ) : null}
                      {message.meta.used_tools?.map((tool) => (
                        <span
                          key={tool}
                          className="rounded bg-white/70 px-1.5 py-0.5 text-[10px] text-slate-500"
                        >
                          {tool}
                        </span>
                      ))}
                      {message.meta.used_rag ? (
                        <span className="rounded bg-white/70 px-1.5 py-0.5 text-[10px] text-slate-500">
                          RAG
                        </span>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              </div>
            ))
          )}

          {loading ? (
            <div className="flex justify-start">
              <div className="rounded-2xl bg-slate-100 px-4 py-3 text-sm text-slate-500">
                <span className="inline-flex items-center gap-2">
                  <span className="flex gap-1">
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.2s]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.1s]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" />
                  </span>
                  {t("ai.generating", { seconds: loadingSeconds })}
                </span>
                {loadingSeconds >= 10 ? (
                  <p className="mt-2 text-xs text-slate-400">{t("ai.slowHint")}</p>
                ) : null}
              </div>
            </div>
          ) : null}

          <div ref={messagesEndRef} />
        </div>

        {error ? <p className="px-6 pb-2 text-sm text-red-600">{error}</p> : null}

        {aiReady === false ? (
          <p className="px-6 pb-2 text-xs text-amber-700">{t("ai.ollamaOffline")}</p>
        ) : null}

        <form
          onSubmit={handleSubmit}
          className="border-t border-slate-100 px-4 py-4 sm:px-6"
        >
          <div className="flex gap-2">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t("ai.placeholder")}
              rows={2}
              disabled={disabled}
              className="min-h-[44px] flex-1 resize-none rounded-xl border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100 disabled:bg-slate-50 disabled:text-slate-400"
            />
            <button
              type="submit"
              disabled={disabled || !input.trim()}
              className="self-end rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {t("ai.send")}
            </button>
          </div>
          <p className="mt-2 text-xs text-slate-400">{t("ai.inputHint")}</p>
        </form>
      </div>
    </article>
  );
}
