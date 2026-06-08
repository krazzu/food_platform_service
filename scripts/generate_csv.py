"""
Generate realistic Russian food supplier data using a local Ollama model
and save to CSV for import via import_csv.py.

Does NOT scrape any website — generates ~200–500 unique suppliers.

Usage:
    python scripts/generate_csv.py
    python scripts/generate_csv.py --count 300 --model llama3.1 --out suppliers.csv
"""
import argparse
import csv
import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.1"

CSV_COLUMNS = [
    "name", "category_name", "description",
    "city", "region", "phone", "email", "website",
    "min_order_amount", "min_order_unit", "price_range_description",
    "has_certificates", "certificate_types",
    "delivery_conditions", "delivery_regions",
    "source_url", "source_platform", "notes",
]

CATEGORIES = [
    ("Молочная продукция", ["Москва", "Санкт-Петербург", "Вологда", "Краснодар", "Казань"]),
    ("Мясо и птица", ["Москва", "Ростов-на-Дону", "Воронеж", "Краснодар", "Белгород"]),
    ("Рыба и морепродукты", ["Мурманск", "Владивосток", "Санкт-Петербург", "Астрахань", "Новороссийск"]),
    ("Овощи и фрукты", ["Краснодар", "Волгоград", "Ставрополь", "Москва", "Ростов-на-Дону"]),
    ("Бакалея", ["Москва", "Санкт-Петербург", "Воронеж", "Новосибирск", "Екатеринбург"]),
    ("Напитки", ["Москва", "Санкт-Петербург", "Нижний Новгород", "Липецк", "Уфа"]),
    ("Специи и приправы", ["Москва", "Санкт-Петербург", "Краснодар", "Ростов-на-Дону", "Казань"]),
    ("Хлеб и выпечка", ["Москва", "Санкт-Петербург", "Тула", "Воронеж", "Самара"]),
    ("Кондитерские изделия", ["Москва", "Санкт-Петербург", "Тула", "Екатеринбург", "Пермь"]),
    ("Замороженная продукция", ["Москва", "Краснодар", "Нижний Новгород", "Новосибирск", "Екатеринбург"]),
    ("Масло и жиры", ["Краснодар", "Воронеж", "Ростов-на-Дону", "Белгород", "Екатеринбург"]),
    ("Консервы и соленья", ["Москва", "Краснодар", "Ставрополь", "Волгоград", "Нижний Новгород"]),
]


def ollama_generate(prompt: str, model: str, ollama_url: str) -> str:
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.8, "num_predict": 600},
    }).encode()
    req = urllib.request.Request(
        f"{ollama_url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read()).get("response", "").strip()


def generate_batch(category: str, city: str, count: int, model: str, ollama_url: str) -> list[dict]:
    prompt = (
        f'Придумай {count} российских B2B-поставщиков из категории "{category}" в городе {city}. '
        'Для каждого выдай JSON с полями: name (ООО/ИП/КФХ), description (2 предложения), '
        'phone (+7 формат), email, website (домен или ""), min_order_amount (число), '
        'min_order_unit (руб/кг/т), price_range_description, has_certificates (true/false), '
        'certificate_types (массив строк), delivery_conditions (1 предложение), '
        'delivery_regions (массив 2-3 региона), notes (""). '
        'Выдай ТОЛЬКО JSON-массив, без пояснений.'
    )

    raw = ollama_generate(prompt, model, ollama_url)

    # Extract JSON array — handle markdown code blocks too
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start == -1 or end == 0:
        return []

    try:
        items = json.loads(raw[start:end])
    except json.JSONDecodeError:
        return []

    rows = []
    for item in items:
        if not item.get("name"):
            continue
        certs = item.get("certificate_types", [])
        if isinstance(certs, list):
            certs_str = ", ".join(certs)
        else:
            certs_str = str(certs)

        regions = item.get("delivery_regions", [])
        if isinstance(regions, list):
            regions_str = ", ".join(regions)
        else:
            regions_str = str(regions)

        rows.append({
            "name": item.get("name", "").strip(),
            "category_name": category,
            "description": item.get("description", "").strip(),
            "city": city,
            "region": city,
            "phone": item.get("phone", ""),
            "email": item.get("email", ""),
            "website": item.get("website", ""),
            "min_order_amount": str(item.get("min_order_amount", "")),
            "min_order_unit": item.get("min_order_unit", "руб"),
            "price_range_description": item.get("price_range_description", ""),
            "has_certificates": "True" if item.get("has_certificates") else "False",
            "certificate_types": certs_str,
            "delivery_conditions": item.get("delivery_conditions", ""),
            "delivery_regions": regions_str,
            "source_url": "",
            "source_platform": "generated",
            "notes": item.get("notes", ""),
        })
    return rows


def main() -> None:
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    parser = argparse.ArgumentParser(description="Generate supplier CSV via Ollama")
    parser.add_argument("--count", type=int, default=200,
                        help="Total suppliers to generate (default: 200)")
    parser.add_argument("--batch", type=int, default=5,
                        help="Suppliers per Ollama call (default: 5)")
    parser.add_argument("--out", default=f"suppliers_generated_{ts}.csv",
                        help="Output CSV filename")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Ollama model (default: {DEFAULT_MODEL})")
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL,
                        help=f"Ollama URL (default: {DEFAULT_OLLAMA_URL})")
    args = parser.parse_args()

    out_path = Path(args.out)
    all_rows: list[dict] = []
    target = args.count
    batch = args.batch

    # Distribute evenly across categories and cities
    import itertools
    cat_city_pairs = [
        (cat, city) for cat, cities in CATEGORIES for city in cities
    ]
    cycle = itertools.cycle(cat_city_pairs)

    print(f"Generating ~{target} suppliers via {args.model} at {args.ollama_url}")

    while len(all_rows) < target:
        cat, city = next(cycle)
        remaining = target - len(all_rows)
        n = min(batch, remaining)
        print(f"  [{len(all_rows)}/{target}] {cat} / {city} ({n} suppliers)…", end=" ", flush=True)
        try:
            rows = generate_batch(cat, city, n, args.model, args.ollama_url)
            all_rows.extend(rows)
            print(f"got {len(rows)}")
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)

    all_rows = all_rows[:target]

    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nSaved {len(all_rows)} suppliers to {out_path}")
    print(f"\nNext step:")
    print(f"  python scripts/import_csv.py {out_path} --api-url http://localhost:8000")


if __name__ == "__main__":
    main()
