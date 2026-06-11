import type { Locale } from "@/lib/i18n/messages";

export type PeriodFilter = {
  month: number;
  year: number;
};

export function getCurrentPeriod(): PeriodFilter {
  const now = new Date();
  return { month: now.getMonth() + 1, year: now.getFullYear() };
}

export function shiftPeriod(period: PeriodFilter, delta: number): PeriodFilter {
  const date = new Date(period.year, period.month - 1 + delta, 1);
  return { month: date.getMonth() + 1, year: date.getFullYear() };
}

export function formatPeriodLabel(period: PeriodFilter, locale: Locale = "ro"): string {
  const date = new Date(period.year, period.month - 1, 1);
  const intlLocale = locale === "en" ? "en-GB" : "ro-RO";
  return date.toLocaleDateString(intlLocale, { month: "long", year: "numeric" });
}

export function periodQuery(period: PeriodFilter): string {
  return `month=${period.month}&year=${period.year}`;
}
