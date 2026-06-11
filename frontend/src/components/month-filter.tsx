"use client";

import { useI18n } from "@/lib/i18n/context";
import { formatPeriodLabel, PeriodFilter, shiftPeriod } from "@/lib/period";

type MonthFilterProps = {
  period: PeriodFilter;
  onChange: (period: PeriodFilter) => void;
};

export function MonthFilter({ period, onChange }: MonthFilterProps) {
  const { locale, t } = useI18n();

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <span className="text-sm font-medium text-slate-600">{t("dashboard.period")}</span>
      <div className="flex items-center gap-2">
        <button
          onClick={() => onChange(shiftPeriod(period, -1))}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-semibold text-slate-700 hover:bg-slate-100"
          aria-label={t("dashboard.prevMonth")}
        >
          ←
        </button>
        <span className="min-w-40 text-center text-sm font-semibold capitalize text-slate-900">
          {formatPeriodLabel(period, locale)}
        </span>
        <button
          onClick={() => onChange(shiftPeriod(period, 1))}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-semibold text-slate-700 hover:bg-slate-100"
          aria-label={t("dashboard.nextMonth")}
        >
          →
        </button>
      </div>
    </div>
  );
}
