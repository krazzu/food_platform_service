"use client";

import type { Category } from "@/lib/types";

interface Filters {
  category: string;
  region: string;
  maxMinOrder: string;
  hasCertificates: boolean | undefined;
  useAi: boolean;
}

interface Props {
  filters: Filters;
  categories: Category[];
  regions: string[];
  onChange: (f: Partial<Filters>) => void;
}

export default function FilterPanel({ filters, categories, regions, onChange }: Props) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {/* Category */}
      <select
        value={filters.category}
        onChange={(e) => onChange({ category: e.target.value })}
        className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
      >
        <option value="">Все категории</option>
        {categories.map((c) => (
          <option key={c.id} value={c.name}>
            {c.name}
          </option>
        ))}
      </select>

      {/* Region */}
      <select
        value={filters.region}
        onChange={(e) => onChange({ region: e.target.value })}
        className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
      >
        <option value="">Все регионы</option>
        {regions.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>

      {/* Max min order */}
      <input
        type="number"
        placeholder="Макс. мин. заказ (руб)"
        value={filters.maxMinOrder}
        onChange={(e) => onChange({ maxMinOrder: e.target.value })}
        className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
      />

      {/* Certificates + AI toggle */}
      <div className="flex flex-col gap-1">
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={filters.hasCertificates === true}
            onChange={(e) =>
              onChange({ hasCertificates: e.target.checked ? true : undefined })
            }
            className="h-4 w-4 rounded border-gray-300 text-emerald-600"
          />
          Только с сертификатами
        </label>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={filters.useAi}
            onChange={(e) => onChange({ useAi: e.target.checked })}
            className="h-4 w-4 rounded border-gray-300 text-emerald-600"
          />
          AI-рекомендации
        </label>
      </div>
    </div>
  );
}
