"use client";

import { useState } from "react";

interface Props {
  onSearch: (query: string) => void;
  loading: boolean;
}

export default function SearchBar({ onSearch, loading }: Props) {
  const [value, setValue] = useState("");

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); if (value.trim()) onSearch(value.trim()); }}
      className="flex items-center gap-3"
    >
      <div className="relative flex-1">
        <svg
          className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
          width="18" height="18" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
        >
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" />
        </svg>
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Например: «поставщик рыбы в Петербурге с сертификатами»"
          className="w-full rounded-2xl border border-slate-200 bg-white py-4 pl-11 pr-4 text-base text-slate-900 placeholder-slate-400 shadow-sm transition focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
        />
      </div>
      <button
        type="submit"
        disabled={loading || !value.trim()}
        className="rounded-2xl bg-emerald-600 px-7 py-4 text-base font-semibold text-white shadow-sm transition hover:bg-emerald-500 active:scale-95 disabled:opacity-40"
      >
        {loading ? (
          <span className="flex items-center gap-2">
            <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
            </svg>
            Ищем
          </span>
        ) : "Найти"}
      </button>
    </form>
  );
}
