import { formatMoney } from "@/lib/format";
import { SummaryStats } from "@/lib/api";

type SummaryCardsProps = {
  summary: SummaryStats;
  periodLabel: string;
};

export function SummaryCards({ summary, periodLabel }: SummaryCardsProps) {
  const cards = [
    { label: "Sold total", value: summary.balance, accent: "text-slate-900" },
    { label: `Venituri · ${periodLabel}`, value: summary.month_income, accent: "text-green-600" },
    { label: `Cheltuieli · ${periodLabel}`, value: summary.month_expenses, accent: "text-red-600" },
    { label: `Economii · ${periodLabel}`, value: summary.month_savings, accent: "text-brand-600" },
  ];

  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => (
        <article
          key={card.label}
          className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <p className="text-sm text-slate-500">{card.label}</p>
          <p className={`mt-2 text-2xl font-bold ${card.accent}`}>
            {formatMoney(card.value)}
          </p>
        </article>
      ))}
    </section>
  );
}
