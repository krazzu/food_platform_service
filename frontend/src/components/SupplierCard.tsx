import type { SupplierSearchResult } from "@/lib/types";

interface Props {
  result: SupplierSearchResult;
  rank: number;
}

function Badge({
  text,
  variant = "gray",
}: {
  text: string;
  variant?: "gray" | "green" | "blue" | "amber" | "violet";
}) {
  const cls: Record<string, string> = {
    gray: "bg-slate-100 text-slate-600",
    green: "bg-emerald-100 text-emerald-700",
    blue: "bg-blue-100 text-blue-700",
    amber: "bg-amber-100 text-amber-700",
    violet: "bg-violet-100 text-violet-700",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${cls[variant]}`}
    >
      {text}
    </span>
  );
}

function StarRating({ rating }: { rating: number }) {
  const full = Math.floor(rating);
  const half = rating - full >= 0.5;
  return (
    <span className="flex items-center gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <svg
          key={i}
          width="11"
          height="11"
          viewBox="0 0 24 24"
          fill={i < full ? "#F59E0B" : i === full && half ? "url(#half)" : "none"}
          stroke={i < full || (i === full && half) ? "#F59E0B" : "#CBD5E1"}
          strokeWidth="2"
        >
          <defs>
            <linearGradient id="half">
              <stop offset="50%" stopColor="#F59E0B" />
              <stop offset="50%" stopColor="transparent" />
            </linearGradient>
          </defs>
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
        </svg>
      ))}
      <span className="ml-1 text-xs font-medium text-amber-600">{rating.toFixed(1)}</span>
    </span>
  );
}

export default function SupplierCard({ result, rank }: Props) {
  const { supplier: s, score } = result;

  return (
    <div className="group relative flex overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:border-blue-200 hover:shadow-md">
      {/* Rank + accent strip */}
      <div className="flex w-12 shrink-0 flex-col items-center gap-2 border-r border-slate-100 bg-slate-50 py-5 px-2">
        <span className="text-xs font-bold text-slate-400">#{rank}</span>
        <div
          className={`w-1 flex-1 rounded-full opacity-60 group-hover:opacity-100 transition ${
            score > 0.7 ? "bg-emerald-500" : score > 0.4 ? "bg-blue-700" : "bg-slate-400"
          }`}
        />
      </div>

      <div className="flex flex-1 flex-col gap-3 p-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="mb-1.5 flex flex-wrap items-center gap-2">
              <h3 className="text-base font-semibold text-slate-900 leading-snug">{s.name}</h3>
              {s.verified && (
                <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-[11px] font-semibold text-blue-600 border border-blue-100">
                  <svg width="9" height="9" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Проверен
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-1.5">
              {s.category && <Badge text={s.category.name} variant="blue" />}
              {(s.city || s.region) && (
                <Badge text={[s.city, s.region].filter(Boolean).join(", ")} />
              )}
              {s.has_certificates && <Badge text="Сертификаты" variant="green" />}
              {s.works_with_nds && <Badge text="НДС" variant="violet" />}
              {s.is_stale && <Badge text="Устаревшие данные" variant="amber" />}
            </div>
          </div>

          <div className="flex shrink-0 flex-col items-end gap-1.5">
            <span className="rounded-lg bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-400 border border-slate-200">
              {(score * 100).toFixed(0)}%
            </span>
            {s.rating && <StarRating rating={s.rating} />}
          </div>
        </div>

        {/* Description */}
        {s.description && (
          <p className="text-sm text-slate-600 line-clamp-2 leading-relaxed">{s.description}</p>
        )}

        {/* Key metrics */}
        <div className="flex flex-wrap gap-x-5 gap-y-1 text-sm">
          {s.min_order_amount !== null && (
            <span className="text-slate-500">
              Мин. заказ:{" "}
              <strong className="text-slate-700">
                {s.min_order_amount.toLocaleString("ru")} {s.min_order_unit ?? "₽"}
              </strong>
            </span>
          )}
          {s.price_range_description && (
            <span className="text-slate-500">
              Цены: <strong className="text-slate-700">{s.price_range_description}</strong>
            </span>
          )}
          {s.payment_terms && (
            <span className="text-slate-500">
              Оплата: <strong className="text-slate-700">{s.payment_terms}</strong>
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
              <a
                href={`tel:${s.phone}`}
                className="flex items-center gap-1.5 text-slate-500 hover:text-blue-600 transition"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07A19.5 19.5 0 013.07 9.81a19.79 19.79 0 01-3.07-8.67A2 2 0 012 1h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L6.09 8.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z" />
                </svg>
                {s.phone}
              </a>
            )}
            {s.email && (
              <a
                href={`mailto:${s.email}`}
                className="flex items-center gap-1.5 text-slate-500 hover:text-blue-600 transition"
              >
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
                Сайт
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
