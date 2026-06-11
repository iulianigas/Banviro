"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { Category, createCategory, deleteCategory, getCategories } from "@/lib/api";
import { CATEGORY_COLOR_OPTIONS, getCategoryLabel, isCustomCategory } from "@/lib/categories";
import { useI18n } from "@/lib/i18n/context";

type CategoryPanelProps = {
  accessToken: string;
  onChanged: () => void;
};

export function CategoryPanel({ accessToken, onChanged }: CategoryPanelProps) {
  const { t } = useI18n();
  const [categories, setCategories] = useState<Category[]>([]);
  const [name, setName] = useState("");
  const [type, setType] = useState<"income" | "expense">("expense");
  const [color, setColor] = useState(CATEGORY_COLOR_OPTIONS[0]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadCategories = useCallback(async () => {
    const [expense, income] = await Promise.all([
      getCategories(accessToken, "expense"),
      getCategories(accessToken, "income"),
    ]);
    setCategories([...expense, ...income]);
  }, [accessToken]);

  useEffect(() => {
    loadCategories().catch(() => setError(t("dashboard.categoriesLoadError")));
  }, [loadCategories, t]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    try {
      await createCategory(accessToken, { name: trimmed, type, color });
      setName("");
      await loadCategories();
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("categoryPanel.addError"));
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(categoryId: number) {
    setError(null);
    try {
      await deleteCategory(accessToken, categoryId);
      await loadCategories();
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("categoryPanel.deleteError"));
    }
  }

  const customCategories = categories.filter(isCustomCategory);
  const defaultCategories = categories.filter((category) => !isCustomCategory(category));

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">{t("categoryPanel.title")}</h2>
      <p className="mt-1 text-sm text-slate-500">{t("categoryPanel.subtitle")}</p>

      <form className="mt-4 grid gap-3 lg:grid-cols-[1fr_140px_120px_auto]" onSubmit={handleSubmit}>
        <input
          type="text"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder={t("categoryPanel.name")}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          required
          maxLength={100}
        />
        <select
          value={type}
          onChange={(event) => setType(event.target.value as "income" | "expense")}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="expense">{t("dashboard.expenseType")}</option>
          <option value="income">{t("dashboard.incomeType")}</option>
        </select>
        <select
          value={color}
          onChange={(event) => setColor(event.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          {CATEGORY_COLOR_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {loading ? t("categoryPanel.adding") : t("categoryPanel.add")}
        </button>
      </form>

      {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}

      <div className="mt-6 space-y-5">
        <section>
          <h3 className="text-sm font-semibold text-slate-800">{t("categoryPanel.custom")}</h3>
          {customCategories.length === 0 ? (
            <p className="mt-2 text-sm text-slate-500">{t("categoryPanel.noCustom")}</p>
          ) : (
            <ul className="mt-2 space-y-2">
              {customCategories.map((category) => (
                <li
                  key={category.id}
                  className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2"
                >
                  <div className="flex items-center gap-2 text-sm">
                    <span
                      className="h-3 w-3 rounded-full"
                      style={{ backgroundColor: category.color }}
                    />
                    <span className="font-medium text-slate-800">{category.name}</span>
                    <span className="rounded-full bg-brand-50 px-2 py-0.5 text-xs text-brand-700">
                      {t("categoryPanel.customBadge")}
                    </span>
                    <span className="text-slate-400">
                      {category.type === "income"
                        ? t("dashboard.incomeType")
                        : t("dashboard.expenseType")}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => void handleDelete(category.id)}
                    className="text-sm text-slate-400 hover:text-red-600"
                  >
                    {t("common.delete")}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section>
          <h3 className="text-sm font-semibold text-slate-800">{t("categoryPanel.default")}</h3>
          <div className="mt-2 flex flex-wrap gap-2">
            {defaultCategories.map((category) => (
              <span
                key={category.id}
                className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-700"
              >
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: category.color }}
                />
                {getCategoryLabel(category, t)}
              </span>
            ))}
          </div>
        </section>
      </div>
    </article>
  );
}
