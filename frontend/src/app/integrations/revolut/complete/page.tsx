"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { completeRevolutConnect, syncRevolutTransactions } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

export default function RevolutCompletePage() {
  const router = useRouter();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [detail, setDetail] = useState<string>("Se finalizează conexiunea...");

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    async function finalize() {
      try {
        await completeRevolutConnect(token);
        const result = await syncRevolutTransactions(token);
        setStatus("success");
        setDetail(`Revolut conectat. Importate ${result.created} tranzacții (${result.skipped} sărite).`);
      } catch (err) {
        setStatus("error");
        setDetail(err instanceof Error ? err.message : "Nu am putut finaliza conexiunea");
      }
    }

    void finalize();
  }, [router]);

  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-6 py-10">
      <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <h1 className="text-2xl font-bold text-slate-900">Revolut</h1>
        <p
          className={`mt-4 text-sm ${
            status === "error" ? "text-red-600" : status === "success" ? "text-green-700" : "text-slate-600"
          }`}
        >
          {detail}
        </p>

        {status !== "loading" ? (
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Link
              href="/dashboard"
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
            >
              Mergi la dashboard
            </Link>
            <Link
              href="/integrations/revolut"
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
            >
              Setări Revolut
            </Link>
          </div>
        ) : null}
      </div>
    </main>
  );
}
