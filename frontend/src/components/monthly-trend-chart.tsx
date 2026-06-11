"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { MonthlyTrend } from "@/lib/api";
import { formatMoney, formatMonthLabel } from "@/lib/format";
import { useI18n } from "@/lib/i18n/context";

type MonthlyTrendChartProps = {
  data: MonthlyTrend[];
};

export function MonthlyTrendChart({ data }: MonthlyTrendChartProps) {
  const { locale, t } = useI18n();
  const incomeLabel = t("dashboard.income");
  const expensesLabel = t("dashboard.expenses");

  const chartData = data.map((item) => ({
    month: formatMonthLabel(item.month, locale),
    [incomeLabel]: parseFloat(item.income),
    [expensesLabel]: parseFloat(item.expenses),
  }));

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">{t("dashboard.monthlyTrend")}</h2>
      <p className="mb-4 text-sm text-slate-500">{t("dashboard.last6Months")}</p>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="month" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip formatter={(value: number) => formatMoney(value, locale)} />
          <Legend />
          <Bar dataKey={incomeLabel} fill="#16a34a" radius={[4, 4, 0, 0]} />
          <Bar dataKey={expensesLabel} fill="#dc2626" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </article>
  );
}
