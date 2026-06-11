import type { Locale } from "./messages";

const LOCALE_KEY = "banviro_locale";

export function getStoredLocale(): Locale {
  if (typeof window === "undefined") return "ro";
  const stored = localStorage.getItem(LOCALE_KEY);
  return stored === "en" ? "en" : "ro";
}

export function setStoredLocale(locale: Locale): void {
  localStorage.setItem(LOCALE_KEY, locale);
}
