interface Props {
  text: string;
}

export default function AiRecommendation({ text }: Props) {
  return (
    <div className="rounded-2xl border border-emerald-200 bg-linear-to-br from-emerald-50 to-teal-50 p-5">
      <div className="mb-2.5 flex items-center gap-2">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-600 text-xs text-white font-bold">
          AI
        </span>
        <span className="text-sm font-semibold text-emerald-800">
          Рекомендация
        </span>
      </div>
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">{text}</p>
    </div>
  );
}
