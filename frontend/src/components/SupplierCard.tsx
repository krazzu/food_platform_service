import type { SupplierSearchResult } from "@/lib/types";

interface Props {
  result: SupplierSearchResult;
  rank: number;
}

function Badge({ text, variant = "gray" }: { text: string; variant?: "gray" | "green" | "blue" | "amber" }) {
  const cls = {
    gray: "bg-slate-100 text-slate-600",
    green: "bg-emerald-100 text-emerald-700",
    blue: "bg-blue-100 text-blue-700",
    amber: "bg-amber-100 text-amber-700",
  }[variant];
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}>
      {text}
    </span>
  );
}

export default function SupplierCard({ result, rank }: Props) {
  const { supplier: s, score } = result;

  return (
    <div className="group relative flex gap-0 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:border-slate-300 hover:shadow-md">
      {/* left accent stripe */}
      <div className="w-1 shrink-0 bg-emerald-500 opacity-70 group-hover:opacity-100 transition" />

      <div className="flex flex-1 flex-col gap-3 p-5">
        {/* Header row */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex flex-col gap-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-bold text-slate-500">
                {rank}
              </span>
              <h3 className="text-base font-semibold text-slate-900">{s.name}</h3>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {s.category && <Badge text={s.category.name} variant="blue" />}
              {(s.city || s.region) && (
                <Badge text={[s.city, s.region].filter(Boolean).join(", ")} />
              )}
              {s.has_certificates && <Badge text="сертификаты" variant="green" />}
              {s.is_stale && <Badge text="устаревшие данные" variant="amber" />}
            </div>
          </div>
          <span className="shrink-0 rounded-lg bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-400 border border-slate-200">
            {(score * 100).toFixed(0)}%
          </span>
        </div>

        {/* Description */}
        {s.description && (
          <p className="text-sm text-slate-600 line-clamp-2 leading-relaxed">{s.description}</p>
        )}

        {/* Details row */}
        <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
          {s.min_order_amount !== null && (
            <span className="text-slate-500">
              Мин. заказ: <strong className="text-slate-700">{s.min_order_amount.toLocaleString("ru")} {s.min_order_unit ?? "руб"}</strong>
            </span>
          )}
          {s.price_range_description && (
            <span className="text-slate-500">
              Цены: <strong className="text-slate-700">{s.price_range_description}</strong>
            </span>
          )}
          {s.delivery_conditions && (
            <span className="text-slate-500">
              Доставка: <strong className="text-slate-700">{s.delivery_conditions}</strong>
            </span>
          )}
          {s.certificate_types && s.certificate_types.length > 0 && (
            <span className="text-slate-500">
              Сертификаты: <strong className="text-slate-700">{s.certificate_types.join(", ")}</strong>
            </span>
          )}
        </div>

        {/* Contacts */}
        {(s.phone || s.email || s.website) && (
          <div className="flex flex-wrap items-center gap-4 border-t border-slate-100 pt-3 text-sm">
            {s.phone && (
              <a href={`tel:${s.phone}`} className="flex items-center gap-1.5 text-slate-500 hover:text-emerald-600 transition">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07A19.5 19.5 0 013.07 9.81a19.79 19.79 0 01-3.07-8.67A2 2 0 012 1h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L6.09 8.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z" />
                </svg>
                {s.phone}
              </a>
            )}
            {s.email && (
              <a href={`mailto:${s.email}`} className="flex items-center gap-1.5 text-slate-500 hover:text-emerald-600 transition">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="4" width="20" height="16" rx="2" />
                  <path d="m22 7-8.97 5.7a1.94 1.94 0 01-2.06 0L2 7" />
                </svg>
                {s.email}
              </a>
            )}
            {s.website && (
              <a
                href={s.website.startsWith("http") ? s.website : `https://${s.website}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-slate-500 hover:text-blue-600 transition"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M2 12h20M12 2a15.3 15.3 0 010 20M12 2a15.3 15.3 0 000 20" />
                </svg>
                {s.website}
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
