"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import SupplierCard from "@/components/SupplierCard";
import { searchSuppliers, getCategories, getRegions } from "@/lib/api";
import type { Category, SearchResponse } from "@/lib/types";

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

const POPULAR_QUERIES = [
  "рыба и морепродукты",
  "молочная продукция",
  "мясо оптом",
  "овощи и фрукты",
  "зерно и крупы",
  "специи и приправы",
  "кондитерские изделия",
  "масло растительное",
];

const STATS = [
  { value: "232+", label: "поставщика в базе" },
  { value: "26", label: "категорий товаров" },
  { value: "40+", label: "регионов России" },
  { value: "100%", label: "бесплатный доступ" },
];

const HOW_IT_WORKS = [
  {
    step: "01",
    title: "Введите запрос",
    desc: "Пишите как есть — умный поиск поймёт «рыба оптом Питер» и расширит запрос синонимами.",
    color: "bg-blue-500",
  },
  {
    step: "02",
    title: "Примените фильтры",
    desc: "Уточните регион, категорию, минимальный заказ и наличие сертификатов.",
    color: "bg-emerald-500",
  },
  {
    step: "03",
    title: "Свяжитесь напрямую",
    desc: "В карточке поставщика — телефон, email и сайт. Без посредников.",
    color: "bg-violet-500",
  },
];

const SELECT_CLS =
  "w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition cursor-pointer";

export default function Home() {
  const [query, setQuery] = useState("");
  const [categories, setCategories] = useState<Category[]>([]);
  const [regions, setRegions] = useState<string[]>([]);
  const [filters, setFilters] = useState<FilterState>(EMPTY_FILTERS);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    Promise.all([getCategories(), getRegions()])
      .then(([cats, regs]) => { setCategories(cats); setRegions(regs); })
      .catch(() => {});
  }, []);

  const runSearch = useCallback(
    async (q: string, f: FilterState = filters) => {
      setLoading(true);
      setError(null);
      try {
        const res = await searchSuppliers({
          query: q,
          category: f.category || undefined,
          region: f.region || undefined,
          max_min_order: f.maxMinOrder ? Number(f.maxMinOrder) : undefined,
          has_certificates: f.hasCertificates,
          use_ai: false,
          limit: 20,
        });
        setResponse(res);
        // Scroll to results after first load
        setTimeout(() => {
          resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
        }, 100);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Ошибка запроса");
      } finally {
        setLoading(false);
      }
    },
    [filters]
  );

  // Auto-search when query changes (debounced)
  function handleQueryChange(val: string) {
    setQuery(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (val.trim().length < 2 && !hasActiveFilters(filters)) {
      if (!val.trim()) { setResponse(null); setError(null); }
      return;
    }
    debounceRef.current = setTimeout(() => runSearch(val, filters), 500);
  }

  // Auto-search when filters change
  useEffect(() => {
    if (!hasActiveFilters(filters) && !query.trim()) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => runSearch(query, filters), 350);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  function handleChipClick(chip: string) {
    setQuery(chip);
    runSearch(chip, filters);
    inputRef.current?.focus();
  }

  function handleFilterChange(patch: Partial<FilterState>) {
    setFilters((f) => ({ ...f, ...patch }));
  }

  function clearAll() {
    setQuery("");
    setFilters(EMPTY_FILTERS);
    setResponse(null);
    setError(null);
  }

  const hasResults = response !== null;
  const activeFilterCount = [
    filters.category,
    filters.region,
    filters.maxMinOrder,
    filters.hasCertificates === true,
  ].filter(Boolean).length;

  return (
    <div className="min-h-screen bg-slate-50">

      {/* ── Navbar ──────────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-50 border-b border-white/10 bg-slate-900/95 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3.5">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-sm font-black text-white tracking-tight">
              S
            </div>
            <span className="text-sm font-semibold text-white">
              suppliers<span className="text-blue-400">.work</span>
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              232+ поставщика
            </span>
            <span className="rounded-full border border-slate-700 px-3 py-1 text-xs font-medium text-slate-400">
              B2B платформа
            </span>
          </div>
        </div>
      </nav>

      {/* ── Hero ────────────────────────────────────────────────────── */}
      <section className="hero-bg relative overflow-hidden py-20 sm:py-28">
        {/* Glow blobs */}
        <div className="pointer-events-none absolute left-1/4 top-1/2 h-72 w-72 -translate-y-1/2 rounded-full bg-blue-600/15 blur-3xl" />
        <div className="pointer-events-none absolute right-1/4 top-10 h-48 w-48 rounded-full bg-emerald-500/10 blur-3xl" />

        <div className="relative mx-auto max-w-3xl px-6 text-center">
          {/* Badge */}
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-500/25 bg-blue-500/10 px-4 py-1.5 text-sm font-medium text-blue-300">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
            </svg>
            Семантический поиск поставщиков
          </div>

          {/* Headline */}
          <h1 className="mb-4 text-4xl font-extrabold leading-tight tracking-tight text-white sm:text-5xl lg:text-[3.5rem]">
            Найдите надёжного<br />
            <span className="text-blue-400">поставщика продуктов</span>
          </h1>

          {/* Subtitle */}
          <p className="mb-10 text-base text-slate-400 sm:text-lg">
            232+ проверенных компании · 26 категорий · 40+ регионов России
          </p>

          {/* Search bar */}
          <div className="search-glow mb-5 flex gap-3 rounded-2xl border border-white/10 bg-white/8 p-1.5 backdrop-blur-sm transition">
            <div className="relative flex-1">
              <svg
                className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-500"
                width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
              >
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => handleQueryChange(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && query.trim() && runSearch(query, filters)}
                placeholder="Рыба оптом, молочная продукция Москва..."
                className="w-full rounded-xl bg-transparent py-3.5 pl-11 pr-4 text-base text-white placeholder:text-slate-500 focus:outline-none"
                autoComplete="off"
              />
            </div>
            <button
              type="button"
              onClick={() => query.trim() && runSearch(query, filters)}
              disabled={loading}
              className="shrink-0 rounded-xl bg-blue-600 px-7 py-3.5 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:opacity-60 cursor-pointer"
            >
              {loading ? (
                <svg className="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12a9 9 0 11-6.219-8.56" />
                </svg>
              ) : "Найти"}
            </button>
          </div>

          {/* Category chips */}
          <div className="flex flex-wrap justify-center gap-2">
            {POPULAR_QUERIES.map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => handleChipClick(q)}
                className="rounded-full border border-white/10 bg-white/5 px-3.5 py-1.5 text-sm text-slate-400 transition hover:border-blue-400/30 hover:bg-blue-400/10 hover:text-blue-300 cursor-pointer"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ── Stats strip ─────────────────────────────────────────────── */}
      {!hasResults && !loading && (
        <section className="border-b border-slate-200 bg-white">
          <div className="mx-auto grid max-w-4xl grid-cols-2 divide-x divide-slate-100 sm:grid-cols-4">
            {STATS.map((s) => (
              <div key={s.label} className="flex flex-col items-center py-8 px-4 text-center">
                <span className="text-3xl font-extrabold text-slate-900">{s.value}</span>
                <span className="mt-1 text-xs font-medium text-slate-500 uppercase tracking-wider">{s.label}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── How it works ────────────────────────────────────────────── */}
      {!hasResults && !loading && (
        <section className="py-16 sm:py-20">
          <div className="mx-auto max-w-5xl px-6">
            <div className="mb-12 text-center">
              <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-blue-600">Как это работает</p>
              <h2 className="text-2xl font-bold text-slate-900 sm:text-3xl">Три шага до нужного поставщика</h2>
            </div>
            <div className="grid gap-6 sm:grid-cols-3">
              {HOW_IT_WORKS.map((step) => (
                <div key={step.step} className="group relative rounded-2xl border border-slate-200 bg-white p-7 shadow-sm transition hover:shadow-md">
                  <div className={`mb-5 inline-flex h-10 w-10 items-center justify-center rounded-xl ${step.color} text-sm font-black text-white`}>
                    {step.step}
                  </div>
                  <h3 className="mb-2 text-base font-semibold text-slate-900">{step.title}</h3>
                  <p className="text-sm leading-relaxed text-slate-500">{step.desc}</p>
                </div>
              ))}
            </div>

            {/* CTA block */}
            <div className="mt-12 overflow-hidden rounded-2xl bg-slate-900">
              <div className="flex flex-col items-center gap-4 px-8 py-10 text-center sm:flex-row sm:text-left">
                <div className="flex-1">
                  <h3 className="mb-1 text-lg font-bold text-white">Готовы найти поставщика?</h3>
                  <p className="text-sm text-slate-400">Введите запрос выше или выберите категорию — результаты появятся мгновенно.</p>
                </div>
                <button
                  type="button"
                  onClick={() => inputRef.current?.focus()}
                  className="shrink-0 rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 cursor-pointer"
                >
                  Начать поиск
                </button>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* ── Results section ─────────────────────────────────────────── */}
      <div ref={resultsRef}>
        {(hasResults || loading) && (
          <section className="mx-auto max-w-5xl px-6 py-8">

            {/* Results header */}
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
              <div>
                {response && (
                  <p className="text-sm text-slate-500">
                    Найдено{" "}
                    <strong className="text-slate-800">{response.total}</strong>{" "}
                    поставщиков
                    {response.query && (
                      <> по запросу <em className="text-slate-700">«{response.query}»</em></>
                    )}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setFiltersOpen((o) => !o)}
                  className={`flex items-center gap-2 rounded-xl border px-4 py-2 text-sm font-medium transition cursor-pointer ${
                    filtersOpen || activeFilterCount > 0
                      ? "border-blue-500 bg-blue-50 text-blue-700"
                      : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                  }`}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="4" y1="6" x2="20" y2="6" />
                    <line x1="8" y1="12" x2="16" y2="12" />
                    <line x1="11" y1="18" x2="13" y2="18" />
                  </svg>
                  Фильтры
                  {activeFilterCount > 0 && (
                    <span className="flex h-4 w-4 items-center justify-center rounded-full bg-blue-600 text-[10px] font-bold text-white">
                      {activeFilterCount}
                    </span>
                  )}
                </button>
                {(query || activeFilterCount > 0) && (
                  <button
                    type="button"
                    onClick={clearAll}
                    className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-500 transition hover:border-red-200 hover:text-red-500 cursor-pointer"
                  >
                    Сбросить
                  </button>
                )}
              </div>
            </div>

            {/* Filter panel */}
            {filtersOpen && (
              <div className="mb-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <label className="flex flex-col gap-1.5">
                    <span className="text-xs font-medium text-slate-500">Категория</span>
                    <select
                      value={filters.category}
                      onChange={(e) => handleFilterChange({ category: e.target.value })}
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
                      onChange={(e) => handleFilterChange({ region: e.target.value })}
                      className={SELECT_CLS}
                    >
                      <option value="">Все регионы</option>
                      {regions.map((r) => <option key={r} value={r}>{r}</option>)}
                    </select>
                  </label>

                  <label className="flex flex-col gap-1.5">
                    <span className="text-xs font-medium text-slate-500">Макс. мин. заказ, ₽</span>
                    <input
                      type="number"
                      placeholder="50 000"
                      value={filters.maxMinOrder}
                      onChange={(e) => handleFilterChange({ maxMinOrder: e.target.value })}
                      className={SELECT_CLS}
                    />
                  </label>

                  <label className="flex cursor-pointer items-center gap-2.5 pt-5">
                    <input
                      type="checkbox"
                      checked={filters.hasCertificates === true}
                      onChange={(e) =>
                        handleFilterChange({ hasCertificates: e.target.checked ? true : undefined })
                      }
                      className="h-4 w-4 rounded border-slate-300 accent-blue-600"
                    />
                    <span className="text-sm text-slate-700">Только с сертификатами</span>
                  </label>
                </div>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="mb-4 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                <svg className="mt-0.5 shrink-0" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                {error}
              </div>
            )}

            {/* Loading skeleton */}
            {loading && (
              <div className="flex flex-col gap-3">
                {[1, 2, 3].map((n) => (
                  <div key={n} className="h-40 animate-pulse rounded-2xl bg-slate-200" />
                ))}
              </div>
            )}

            {/* Results */}
            {!loading && response && (
              response.results.length === 0 ? (
                <div className="flex flex-col items-center gap-4 py-16 text-center">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-slate-400">
                      <circle cx="11" cy="11" r="8" />
                      <path d="m21 21-4.35-4.35" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-slate-700">Ничего не найдено</p>
                    <p className="mt-1 text-sm text-slate-400">Попробуйте изменить запрос или убрать фильтры.</p>
                  </div>
                  <button type="button" onClick={clearAll} className="text-sm text-blue-600 hover:underline cursor-pointer">
                    Сбросить фильтры
                  </button>
                </div>
              ) : (
                <div className="flex flex-col gap-3">
                  {response.results.map((r, i) => (
                    <SupplierCard key={r.supplier.id} result={r} rank={i + 1} />
                  ))}
                </div>
              )
            )}
          </section>
        )}
      </div>
    </div>
  );
}

function hasActiveFilters(f: FilterState) {
  return !!(f.category || f.region || f.maxMinOrder || f.hasCertificates === true);
}
