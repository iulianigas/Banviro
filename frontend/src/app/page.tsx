import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col items-center justify-center gap-8 px-6 py-16">
      <div className="text-center">
        <p className="mb-3 text-sm font-semibold uppercase tracking-wide text-brand-600">
          Personal Finance Tracker
        </p>
        <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
          Banviro
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-slate-600">
          Urmărește cheltuielile, vizualizează grafice și primește insight-uri
          financiare — totul într-un singur loc.
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-4">
        <Link
          href="/register"
          className="rounded-lg bg-brand-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-700"
        >
          Creează cont
        </Link>
        <Link
          href="/login"
          className="rounded-lg border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
        >
          Autentificare
        </Link>
      </div>
    </main>
  );
}
