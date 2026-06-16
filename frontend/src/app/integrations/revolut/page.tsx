"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { startRevolutConnect, syncRevolutTransactions } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

export default function RevolutIntegrationPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getAccessToken()) {
      router.replace("/login");
    }
  }, [router]);

  async function handleConnect() {
    const token = getAccessToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const { connect_url } = await startRevolutConnect(token);
      window.location.href = connect_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connect failed");
      setLoading(false);
    }
  }

  async function handleSync() {
    const token = getAccessToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    setSyncing(true);
    setError(null);
    setMessage(null);

    try {
      const result = await syncRevolutTransactions(token);
      setMessage(`Importate: ${result.created}, sărite: ${result.skipped}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setSyncing(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-6 py-10">
      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-slate-900">Conectează Revolut</h1>
        <p className="mt-2 text-sm text-slate-600">
          Importă tranzacțiile din Revolut (România) prin Salt Edge Open Banking.
        </p>

        <div className="mt-6 space-y-3">
          <button
            type="button"
            onClick={handleConnect}
            disabled={loading}
            className="w-full rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {loading ? "Se deschide Salt Edge..." : "Conectează Revolut"}
          </button>

          <button
            type="button"
            onClick={handleSync}
            disabled={syncing}
            className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-60"
          >
            {syncing ? "Se sincronizează..." : "Sincronizează tranzacțiile"}
          </button>
        </div>

        {message ? <p className="mt-4 text-sm text-green-700">{message}</p> : null}
        {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}

        <p className="mt-6 text-center text-sm text-slate-600">
          <Link href="/dashboard" className="font-semibold text-brand-600 hover:text-brand-700">
            Înapoi la dashboard
          </Link>
        </p>
      </div>
    </main>
  );
}
