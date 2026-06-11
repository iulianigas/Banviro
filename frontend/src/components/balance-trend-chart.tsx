"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { BalanceTrend } from "@/lib/api";
import { formatMoney, formatMonthLabel } from "@/lib/format";

type BalanceTrendChartProps = {
  data: BalanceTrend[];
};

export function BalanceTrendChart({ data }: BalanceTrendChartProps) {
  const chartData = data.map((item) => ({
    month: formatMonthLabel(item.month),
    Sold: parseFloat(item.balance),
  }));

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Evoluție sold</h2>
      <p className="mb-4 text-sm text-slate-500">Sold cumulativ, ultimele 6 luni</p>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="month" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip formatter={(value: number) => formatMoney(value)} />
          <Legend />
          <Line
            type="monotone"
            dataKey="Sold"
            stroke="#15803d"
            strokeWidth={3}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </article>
  );
}
