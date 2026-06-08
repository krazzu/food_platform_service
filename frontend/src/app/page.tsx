"use client";

import { useEffect, useRef, useState } from "react";
import SearchBar from "@/components/SearchBar";
import SupplierCard from "@/components/SupplierCard";
import { searchSuppliers, getCategories, getRegions } from "@/lib/api";
import type { Category, SearchResponse } from "@/lib/types";

type Mode = "search" | "filters";

interface FilterState {
  category: string;
  region: string;
  maxMinOrder: string;
  hasCertificates: boolean | undefined;
}

const EMPTY_FILTERS: FilterState = {
  category: "",
  region: "",
  maxMinOrder: "",
  hasCertificates: undefined,
};

const SELECT_CLS =
  "rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 transition";

export default function Home() {
  const [mode, setMode] = useState<Mode>("search");
  const [categories, setCategories] = useState<Category[]>([]);
  const [regions, setRegions] = useState<string[]>([]);
  const [filters, setFilters] = useState<FilterState>(EMPTY_FILTERS);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    Promise.all([getCategories(), getRegions()])
      .then(([cats, regs]) => { setCategories(cats); setRegions(regs); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (mode !== "filters") return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => runSearch(""), 300);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, mode]);

  async function runSearch(query: string) {
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const res = await searchSuppliers({
        query,
        category: filters.category || undefined,
        region: filters.region || undefined,
        max_min_order: filters.maxMinOrder ? Number(filters.maxMinOrder) : undefined,
        has_certificates: filters.hasCertificates,
        use_ai: false,
        limit: 20,
      });
      setResponse(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка запроса");
    } finally {
      setLoading(false);
    }
  }

  function switchMode(next: Mode) {
    setMode(next);
    setResponse(null);
    setError(null);
    setFilters(EMPTY_FILTERS);
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <header className="bg-slate-900 px-6 py-5">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500 text-lg font-black text-white">
              П
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">
                Поиск поставщиков
              </h1>
              <p className="text-xs text-slate-400">
                продукты питания · семантический поиск · AI
              </p>
            </div>
          </div>
          <span className="hidden sm:inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            B2B платформа
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-8">
        {/* ── Mode tabs ───────────────────────────────────────────────────── */}
        <div className="mb-6 inline-flex rounded-xl border border-slate-200 bg-white p-1 shadow-sm">
          <TabBtn active={mode === "search"} onClick={() => switchMode("search")}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
            </svg>
            Поиск
          </TabBtn>
          <TabBtn active={mode === "filters"} onClick={() => switchMode("filters")}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="4" y1="6" x2="20" y2="6" /><line x1="8" y1="12" x2="16" y2="12" /><line x1="11" y1="18" x2="13" y2="18" />
            </svg>
            Фильтры
          </TabBtn>
        </div>

        {/* ── Search mode ─────────────────────────────────────────────────── */}
        {mode === "search" && (
          <div className="mb-6 flex flex-col gap-4">
            <SearchBar onSearch={runSearch} loading={loading} />
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <select
                aria-label="Категория"
                value={filters.category}
                onChange={(e) => setFilters((f) => ({ ...f, category: e.target.value }))}
                className={SELECT_CLS}
              >
                <option value="">Все категории</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.name}>{c.name}</option>
                ))}
              </select>
              <select
                aria-label="Регион"
                value={filters.region}
                onChange={(e) => setFilters((f) => ({ ...f, region: e.target.value }))}
                className={SELECT_CLS}
              >
                <option value="">Все регионы</option>
                {regions.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
          </div>
        )}

        {/* ── Filter mode ─────────────────────────────────────────────────── */}
        {mode === "filters" && (
          <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <p className="mb-5 text-xs font-semibold uppercase tracking-widest text-slate-400">
              Параметры поиска
            </p>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-medium text-slate-500">Категория</span>
                <select
                  value={filters.category}
                  onChange={(e) => setFilters((f) => ({ ...f, category: e.target.value }))}
                  className={SELECT_CLS}
                >
                  <option value="">Все категории</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.name}>{c.name}</option>
                  ))}
                </select>
              </label>

              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-medium text-slate-500">Регион</span>
                <select
                  value={filters.region}
                  onChange={(e) => setFilters((f) => ({ ...f, region: e.target.value }))}
                  className={SELECT_CLS}
                >
                  <option value="">Все регионы</option>
                  {regions.map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
              </label>

              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-medium text-slate-500">Макс. мин. заказ, руб</span>
                <input
                  type="number"
                  placeholder="Например: 50 000"
                  value={filters.maxMinOrder}
                  onChange={(e) => setFilters((f) => ({ ...f, maxMinOrder: e.target.value }))}
                  className={SELECT_CLS}
                />
              </label>

              <label className="flex cursor-pointer items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  checked={filters.hasCertificates === true}
                  onChange={(e) =>
                    setFilters((f) => ({ ...f, hasCertificates: e.target.checked ? true : undefined }))
                  }
                  className="h-4 w-4 rounded border-slate-300 accent-emerald-600"
                />
                <span className="text-sm text-slate-700">Только с сертификатами</span>
              </label>
            </div>
          </div>
        )}

        {/* ── Error ───────────────────────────────────────────────────────── */}
        {error && (
          <div className="mb-4 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <svg className="mt-0.5 shrink-0" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {error}
          </div>
        )}

        {/* ── Results ─────────────────────────────────────────────────────── */}
        {response && (
          <div>
            <div className="mb-4 flex items-center justify-between">
              <p className="text-sm text-slate-500">
                Найдено{" "}
                <strong className="text-slate-800">{response.total}</strong>{" "}
                поставщиков
                {response.query && <> по запросу <em>«{response.query}»</em></>}
              </p>
            </div>
            {response.results.length === 0 ? (
              <p className="py-12 text-center text-slate-400">
                Ничего не найдено — попробуйте изменить запрос или фильтры.
              </p>
            ) : (
              <div className="flex flex-col gap-3">
                {response.results.map((r, i) => (
                  <SupplierCard key={r.supplier.id} result={r} rank={i + 1} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Empty state ─────────────────────────────────────────────────── */}
        {!response && !loading && mode === "search" && (
          <div className="flex flex-col items-center gap-5 py-20 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-100">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-slate-400">
                <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
              </svg>
            </div>
            <div>
              <p className="mb-1 font-medium text-slate-600">Введите поисковый запрос</p>
              <p className="text-sm text-slate-400">
                Например,{" "}
                <button
                  type="button"
                  onClick={() => runSearch("поставщик рыбы в Петербурге")}
                  className="text-emerald-600 hover:underline"
                >
                  поставщик рыбы в Петербурге
                </button>
                {" "}или{" "}
                <button
                  type="button"
                  onClick={() => runSearch("органические специи с сертификатами")}
                  className="text-emerald-600 hover:underline"
                >
                  органические специи с сертификатами
                </button>
              </p>
            </div>
          </div>
        )}

        {/* ── Loading skeleton ────────────────────────────────────────────── */}
        {loading && (
          <div className="flex flex-col gap-3">
            {[1, 2, 3].map((n) => (
              <div key={n} className="h-36 animate-pulse rounded-2xl bg-slate-200" />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

function TabBtn({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-medium transition ${
        active
          ? "bg-slate-900 text-white shadow-sm"
          : "text-slate-500 hover:text-slate-800"
      }`}
    >
      {children}
    </button>
  );
}
