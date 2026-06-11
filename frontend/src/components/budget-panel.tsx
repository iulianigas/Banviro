"use client";

import { FormEvent, useEffect, useState } from "react";

import { BudgetProgress, Category, getCategories, upsertBudget } from "@/lib/api";
import { getCategoryLabel } from "@/lib/categories";
import { formatMoney } from "@/lib/format";
import { useI18n } from "@/lib/i18n/context";
import { PeriodFilter } from "@/lib/period";

type BudgetPanelProps = {
  accessToken: string;
  period: PeriodFilter;
  budgets: BudgetProgress[];
  onChanged: () => void;
};

export function BudgetPanel({ accessToken, period, budgets, onChanged }: BudgetPanelProps) {
  const { locale, t } = useI18n();
  const [categories, setCategories] = useState<Category[]>([]);
  const [categoryId, setCategoryId] = useState("");
  const [amount, setAmount] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCategories(accessToken, "expense")
      .then((data) => {
        setCategories(data);
        setCategoryId(data[0] ? String(data[0].id) : "");
      })
      .catch(() => setError(t("dashboard.categoriesLoadError")));
  }, [accessToken, t]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!categoryId || !amount) return;

    setLoading(true);
    setError(null);
    try {
      await upsertBudget(accessToken, {
        category_id: Number(categoryId),
        month: period.month,
        year: period.year,
        amount: Number(amount),
      });
      setAmount("");
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("dashboard.budgetSaveError"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">{t("dashboard.budgets")}</h2>
      <p className="mt-1 text-sm text-slate-500">{t("dashboard.budgetsHint")}</p>

      <form className="mt-4 grid gap-3 sm:grid-cols-[1fr_140px_auto]" onSubmit={handleSubmit}>
        <select
          value={categoryId}
          onChange={(event) => setCategoryId(event.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          required
        >
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {getCategoryLabel(category, t)}
            </option>
          ))}
        </select>
        <input
          type="number"
          min="1"
          step="0.01"
          placeholder={t("dashboard.amountRon")}
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          required
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {t("dashboard.setBudget")}
        </button>
      </form>

      {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}

      <div className="mt-6 space-y-4">
        {budgets.length === 0 ? (
          <p className="text-sm text-slate-500">{t("dashboard.noBudgets")}</p>
        ) : (
          budgets.map((budget) => {
            const percent = Math.min(parseFloat(budget.usage_percent), 100);
            const isOver = parseFloat(budget.usage_percent) > 100;
            return (
              <div key={budget.id}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="font-medium text-slate-800">
                    {getCategoryLabel(budget, t)}
                  </span>
                  <span className={isOver ? "font-semibold text-red-600" : "text-slate-600"}>
                    {formatMoney(budget.spent_amount, locale)} /{" "}
                    {formatMoney(budget.budget_amount, locale)}
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className={`h-full rounded-full ${isOver ? "bg-red-500" : "bg-brand-500"}`}
                    style={{ width: `${percent}%` }}
                  />
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  {t("dashboard.budgetUsed", {
                    percent: budget.usage_percent,
                    remaining: formatMoney(budget.remaining_amount, locale),
                  })}
                </p>
              </div>
            );
          })
        )}
      </div>
    </article>
  );
}
