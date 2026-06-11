"use client";

import Link from "next/link";

import { LanguageSelector } from "@/components/language-selector";
import { useI18n } from "@/lib/i18n/context";

export default function HomePage() {
  const { t } = useI18n();

  return (
    <main className="relative mx-auto flex min-h-screen max-w-5xl flex-col items-center justify-center gap-8 px-6 py-16">
      <div className="absolute right-6 top-6">
        <LanguageSelector />
      </div>

      <div className="text-center">
        <p className="mb-3 text-sm font-semibold uppercase tracking-wide text-brand-600">
          {t("home.tagline")}
        </p>
        <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">Banviro</h1>
        <p className="mt-4 max-w-2xl text-lg text-slate-600">{t("home.description")}</p>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-4">
        <Link
          href="/register"
          className="rounded-lg bg-brand-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-700"
        >
          {t("home.createAccount")}
        </Link>
        <Link
          href="/login"
          className="rounded-lg border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
        >
          {t("home.signIn")}
        </Link>
      </div>
    </main>
  );
}
