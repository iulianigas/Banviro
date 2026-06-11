"use client";

import Link from "next/link";

import { LanguageSelector } from "@/components/language-selector";

type AuthShellProps = {
  title: string;
  subtitle: string;
  children: React.ReactNode;
};

export function AuthShell({ title, subtitle, children }: AuthShellProps) {
  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-12">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-6 flex justify-end">
          <LanguageSelector />
        </div>
        <div className="mb-8 text-center">
          <Link href="/" className="text-sm font-semibold text-brand-600">
            Banviro
          </Link>
          <h1 className="mt-3 text-2xl font-bold text-slate-900">{title}</h1>
          <p className="mt-2 text-sm text-slate-600">{subtitle}</p>
        </div>
        {children}
      </div>
    </main>
  );
}
