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

type MonthlyTrendChartProps = {
  data: MonthlyTrend[];
};

export function MonthlyTrendChart({ data }: MonthlyTrendChartProps) {
  const chartData = data.map((item) => ({
    month: formatMonthLabel(item.month),
    Venituri: parseFloat(item.income),
    Cheltuieli: parseFloat(item.expenses),
  }));

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Evoluție lunară</h2>
      <p className="mb-4 text-sm text-slate-500">Ultimele 6 luni</p>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="month" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip formatter={(value: number) => formatMoney(value)} />
          <Legend />
          <Bar dataKey="Venituri" fill="#16a34a" radius={[4, 4, 0, 0]} />
          <Bar dataKey="Cheltuieli" fill="#dc2626" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </article>
  );
}
