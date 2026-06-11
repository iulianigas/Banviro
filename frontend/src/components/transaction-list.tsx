"use client";

import { Transaction, deleteTransaction } from "@/lib/api";
import { formatMoney } from "@/lib/format";

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
  async function handleDelete(id: number) {
    await deleteTransaction(accessToken, id);
    onDeleted();
  }

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Tranzacții recente</h2>
      {transactions.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">Nu ai tranzacții încă.</p>
      ) : (
        <ul className="mt-4 divide-y divide-slate-100">
          {transactions.map((transaction) => (
            <li
              key={transaction.id}
              className="flex flex-wrap items-center justify-between gap-3 py-3"
            >
              <div>
                <p className="font-medium text-slate-900">
                  {transaction.description || transaction.category.name}
                </p>
                <p className="text-sm text-slate-500">
                  {transaction.category.name} · {transaction.transaction_date}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span
                  className={`font-semibold ${
                    transaction.type === "income" ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {transaction.type === "income" ? "+" : "-"}
                  {formatMoney(transaction.amount)}
                </span>
                <button
                  onClick={() => handleDelete(transaction.id)}
                  className="text-sm text-slate-400 hover:text-red-600"
                  aria-label="Șterge tranzacția"
                >
                  Șterge
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
