"use client";

import { useI18n } from "@/lib/i18n/context";
import type { Locale } from "@/lib/i18n/messages";

type LanguageSelectorProps = {
  className?: string;
};

const options: { value: Locale; label: string }[] = [
  { value: "ro", label: "RO" },
  { value: "en", label: "EN" },
];

export function LanguageSelector({ className = "" }: LanguageSelectorProps) {
  const { locale, setLocale, t } = useI18n();

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <span className="text-sm font-medium text-slate-600">{t("common.language")}:</span>
      <div className="inline-flex rounded-lg border border-slate-300 p-0.5">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => setLocale(option.value)}
            className={`rounded-md px-3 py-1 text-sm font-semibold transition ${
              locale === option.value
                ? "bg-brand-600 text-white"
                : "text-slate-600 hover:bg-slate-100"
            }`}
            aria-pressed={locale === option.value}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
