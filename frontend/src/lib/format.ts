import type { Locale } from "@/lib/i18n/messages";

function intlLocale(locale: Locale): string {
  return locale === "en" ? "en-GB" : "ro-RO";
}

export function formatMoney(value: string | number, locale: Locale = "ro"): string {
  const amount = typeof value === "string" ? parseFloat(value) : value;
  return new Intl.NumberFormat(intlLocale(locale), {
    style: "currency",
    currency: "RON",
    minimumFractionDigits: 2,
  }).format(amount || 0);
}

export function formatMonthLabel(monthKey: string, locale: Locale = "ro"): string {
  const [year, month] = monthKey.split("-");
  const date = new Date(Number(year), Number(month) - 1, 1);
  return date.toLocaleDateString(intlLocale(locale), { month: "short", year: "2-digit" });
}
