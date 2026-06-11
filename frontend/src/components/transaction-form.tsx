"use client";

import { FormEvent, useEffect, useState } from "react";

import { Category, createTransaction } from "@/lib/api";
import { getCategoryLabel } from "@/lib/categories";
import { useI18n } from "@/lib/i18n/context";
import { PeriodFilter } from "@/lib/period";

type TransactionFormProps = {
  accessToken: string;
  onCreated: () => void;
  defaultPeriod?: PeriodFilter;
};

function defaultDateForPeriod(period?: PeriodFilter): string {
  if (!period) return new Date().toISOString().slice(0, 10);
  const today = new Date();
  if (today.getFullYear() === period.year && today.getMonth() + 1 === period.month) {
    return today.toISOString().slice(0, 10);
  }
  return `${period.year}-${String(period.month).padStart(2, "0")}-01`;
}

export function TransactionForm({
  accessToken,
  onCreated,
  defaultPeriod,
}: TransactionFormProps) {
  const { t } = useI18n();
  const [categories, setCategories] = useState<Category[]>([]);
  const [type, setType] = useState<"income" | "expense">("expense");
  const [categoryId, setCategoryId] = useState("");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [transactionDate, setTransactionDate] = useState(defaultDateForPeriod(defaultPeriod));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setTransactionDate(defaultDateForPeriod(defaultPeriod));
  }, [defaultPeriod]);

  useEffect(() => {
    async function loadCategories() {
      const { getCategories } = await import("@/lib/api");
      const data = await getCategories(accessToken, type);
      setCategories(data);
      setCategoryId(data[0] ? String(data[0].id) : "");
    }

    loadCategories().catch(() => setError(t("dashboard.categoriesLoadError")));
  }, [accessToken, type, t]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!categoryId) return;

    setLoading(true);
    setError(null);

    try {
      await createTransaction(accessToken, {
        category_id: Number(categoryId),
        amount: Number(amount),
        type,
        description: description || undefined,
        transaction_date: transactionDate,
      });
      setAmount("");
      setDescription("");
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("dashboard.saveError"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">{t("dashboard.addTransaction")}</h2>
      <form className="mt-4 space-y-4" onSubmit={handleSubmit}>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              {t("dashboard.type")}
            </label>
            <select
              value={type}
              onChange={(event) => setType(event.target.value as "income" | "expense")}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            >
              <option value="expense">{t("dashboard.expenseType")}</option>
              <option value="income">{t("dashboard.incomeType")}</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              {t("dashboard.category")}
            </label>
            <select
              value={categoryId}
              onChange={(event) => setCategoryId(event.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              required
            >
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {getCategoryLabel(category, t)}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              {t("dashboard.amount")}
            </label>
            <input
              type="number"
              min="0.01"
              step="0.01"
              required
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              {t("dashboard.date")}
            </label>
            <input
              type="date"
              required
              value={transactionDate}
              onChange={(event) => setTransactionDate(event.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">
            {t("dashboard.description")}
          </label>
          <input
            type="text"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder={t("dashboard.descriptionPlaceholder")}
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </div>

        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {loading ? t("dashboard.saving") : t("dashboard.saveTransaction")}
        </button>
      </form>
    </article>
  );
}
