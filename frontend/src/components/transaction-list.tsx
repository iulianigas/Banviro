"use client";

import { Transaction, deleteTransaction } from "@/lib/api";
import { getCategoryLabel } from "@/lib/categories";
import { formatMoney } from "@/lib/format";
import { useI18n } from "@/lib/i18n/context";

type TransactionListProps = {
  accessToken: string;
  transactions: Transaction[];
  onDeleted: () => void;
};

export function TransactionList({
  accessToken,
  transactions,
  onDeleted,
}: TransactionListProps) {
  const { locale, t } = useI18n();

  async function handleDelete(id: number) {
    await deleteTransaction(accessToken, id);
    onDeleted();
  }

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">{t("dashboard.recentTransactions")}</h2>
      {transactions.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">{t("dashboard.noTransactions")}</p>
      ) : (
        <ul className="mt-4 divide-y divide-slate-100">
          {transactions.map((transaction) => (
            <li
              key={transaction.id}
              className="flex flex-wrap items-center justify-between gap-3 py-3"
            >
              <div>
                <p className="font-medium text-slate-900">
                  {transaction.description || getCategoryLabel(transaction.category, t)}
                </p>
                <p className="text-sm text-slate-500">
                  {getCategoryLabel(transaction.category, t)} · {transaction.transaction_date}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span
                  className={`font-semibold ${
                    transaction.type === "income" ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {transaction.type === "income" ? "+" : "-"}
                  {formatMoney(transaction.amount, locale)}
                </span>
                <button
                  onClick={() => handleDelete(transaction.id)}
                  className="text-sm text-slate-400 hover:text-red-600"
                  aria-label={t("dashboard.deleteTransaction")}
                >
                  {t("common.delete")}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
