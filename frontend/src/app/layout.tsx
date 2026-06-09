import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin", "latin-ext"],
  variable: "--font-jakarta",
  display: "swap",
  weight: ["400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "Suppliers.work — Поиск поставщиков продуктов питания",
  description:
    "B2B-платформа поиска поставщиков продуктов питания: 232+ компании, 26 категорий, 40+ регионов России. Семантический поиск с фильтрацией.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className={`${jakarta.variable} h-full`}>
      <body className="min-h-full antialiased">{children}</body>
    </html>
  );
}
