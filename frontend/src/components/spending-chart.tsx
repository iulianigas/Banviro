"use client";

import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import { CategoryBreakdown } from "@/lib/api";
import { getCategoryLabel } from "@/lib/categories";
import { formatMoney } from "@/lib/format";
import { useI18n } from "@/lib/i18n/context";

type SpendingChartProps = {
  data: CategoryBreakdown[];
  periodLabel: string;
};

export function SpendingChart({ data, periodLabel }: SpendingChartProps) {
  const { locale, t } = useI18n();

  if (data.length === 0) {
    return (
      <div className="flex h-72 items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-500">
        {t("dashboard.spendingEmpty")}
      </div>
    );
  }

  const chartData = data.map((item) => ({
    name: getCategoryLabel(item, t),
    value: parseFloat(item.amount),
    color: item.color,
  }));

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">{t("dashboard.spendingByCategory")}</h2>
      <p className="mb-4 text-sm text-slate-500">{periodLabel}</p>
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={2}
          >
            {chartData.map((entry) => (
              <Cell key={entry.name} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip formatter={(value: number) => formatMoney(value, locale)} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </article>
  );
}
