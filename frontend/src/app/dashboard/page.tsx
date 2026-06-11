"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { BalanceTrendChart } from "@/components/balance-trend-chart";
import { BudgetPanel } from "@/components/budget-panel";
import { MonthFilter } from "@/components/month-filter";
import { MonthlyTrendChart } from "@/components/monthly-trend-chart";
import { SpendingChart } from "@/components/spending-chart";
import { SummaryCards } from "@/components/summary-cards";
import { TransactionForm } from "@/components/transaction-form";
import { TransactionList } from "@/components/transaction-list";
import {
  BalanceTrend,
  BudgetProgress,
  CategoryBreakdown,
  getBalanceTrend,
  getBudgets,
  getCurrentUser,
  getMonthlyTrend,
  getSpendingByCategory,
  getSummary,
  getTransactions,
  MonthlyTrend,
  SummaryStats,
  Transaction,
  User,
} from "@/lib/api";
import { clearTokens, getAccessToken } from "@/lib/auth";
import { formatPeriodLabel, getCurrentPeriod, PeriodFilter } from "@/lib/period";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [summary, setSummary] = useState<SummaryStats | null>(null);
  const [spending, setSpending] = useState<CategoryBreakdown[]>([]);
  const [trend, setTrend] = useState<MonthlyTrend[]>([]);
  const [balanceTrend, setBalanceTrend] = useState<BalanceTrend[]>([]);
  const [budgets, setBudgets] = useState<BudgetProgress[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [period, setPeriod] = useState<PeriodFilter>(getCurrentPeriod);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = useCallback(async (token: string, selectedPeriod: PeriodFilter) => {
    const [
      userData,
      summaryData,
      spendingData,
      trendData,
      balanceData,
      budgetsData,
      transactionsData,
    ] = await Promise.all([
      getCurrentUser(token),
      getSummary(token, selectedPeriod),
      getSpendingByCategory(token, selectedPeriod),
      getMonthlyTrend(token, selectedPeriod),
      getBalanceTrend(token, selectedPeriod),
      getBudgets(token, selectedPeriod),
      getTransactions(token, selectedPeriod),
    ]);

    setUser(userData);
    setSummary(summaryData);
    setSpending(spendingData);
    setTrend(trendData);
    setBalanceTrend(balanceData);
    setBudgets(budgetsData);
    setTransactions(transactionsData);
    setError(null);
  }, []);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      setLoading(false);
      router.replace("/login");
      return;
    }

    loadDashboard(token, period)
      .catch((err) => {
        const message =
          err instanceof Error ? err.message : "Nu am putut încărca datele dashboard-ului";
        setError(message);
        if (message.toLowerCase().includes("authenticated") || message.includes("401")) {
          clearTokens();
          router.replace("/login");
        }
      })
      .finally(() => setLoading(false));
  }, [loadDashboard, period, router]);

  function handleLogout() {
    clearTokens();
    router.push("/login");
  }

  function handleRefresh() {
    const token = getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    loadDashboard(token, period)
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Eroare la reîncărcare");
      })
      .finally(() => setLoading(false));
  }

  const periodLabel = formatPeriodLabel(period);

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-slate-600">Se încarcă dashboard-ul...</p>
      </main>
    );
  }

  if (error || !user || !summary) {
    return (
      <main className="flex min-h-screen items-center justify-center px-6">
        <div className="max-w-md rounded-2xl border border-red-200 bg-white p-6 text-center shadow-sm">
          <h1 className="text-lg font-semibold text-slate-900">Dashboard indisponibil</h1>
          <p className="mt-2 text-sm text-slate-600">
            {error ??
              "Datele nu s-au încărcat. Verifică dacă backend-ul rulează și ai rulat migrarea DB."}
          </p>
          <div className="mt-4 flex flex-wrap justify-center gap-3">
            <button
              onClick={handleRefresh}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
            >
              Reîncearcă
            </button>
            <button
              onClick={() => router.push("/login")}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
            >
              Mergi la login
            </button>
          </div>
        </div>
      </main>
    );
  }

  const token = getAccessToken();
  if (!token) return null;

  return (
    <main className="mx-auto min-h-screen max-w-7xl px-6 py-10">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-brand-600">
            Banviro Dashboard
          </p>
          <h1 className="text-3xl font-bold text-slate-900">
            Bun venit, {user.full_name ?? user.email}
          </h1>
        </div>
        <button
          onClick={handleLogout}
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
        >
          Deconectare
        </button>
      </header>

      <div className="space-y-8">
        <MonthFilter period={period} onChange={setPeriod} />

        <SummaryCards summary={summary} periodLabel={periodLabel} />

        <section className="grid gap-6 xl:grid-cols-2">
          <BalanceTrendChart data={balanceTrend} />
          <SpendingChart data={spending} periodLabel={periodLabel} />
        </section>

        <section className="grid gap-6 xl:grid-cols-2">
          <MonthlyTrendChart data={trend} />
          <BudgetPanel
            accessToken={token}
            period={period}
            budgets={budgets}
            onChanged={handleRefresh}
          />
        </section>

        <section className="grid gap-6 xl:grid-cols-2">
          <TransactionForm accessToken={token} onCreated={handleRefresh} defaultPeriod={period} />
          <TransactionList
            accessToken={token}
            transactions={transactions}
            onDeleted={handleRefresh}
          />
        </section>
      </div>
    </main>
  );
}
