"""
Import suppliers from a CSV file and push to the server via POST /api/suppliers/bulk.

Optionally enrich empty descriptions using a local Ollama model before uploading.

Usage:
    python scripts/import_csv.py suppliers.csv
    python scripts/import_csv.py suppliers.csv --enrich
    python scripts/import_csv.py suppliers.csv --enrich --ollama-model llama3.1
    python scripts/import_csv.py suppliers.csv --api-url http://my-server:8000

CSV columns (all optional except `name`):
    name, category_name, description, city, region, phone, email, website,
    min_order_amount, min_order_unit, price_range_description,
    has_certificates, certificate_types, delivery_conditions,
    delivery_regions, source_url, source_platform, notes
"""
import argparse
import csv
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.1"
BATCH_SIZE = 50


def enrich_description(row: dict, ollama_url: str, model: str) -> str:
    name = row.get("name", "")
    category = row.get("category_name", "")
    city = row.get("city", "")
    region = row.get("region", "")
    certs = row.get("certificate_types", "")
    min_order = row.get("min_order_amount", "")

    prompt = (
        f"Напиши краткое описание (2–3 предложения) для российского B2B-поставщика продуктов питания.\n"
        f"Название: {name}\n"
        f"Категория: {category or 'не указана'}\n"
        f"Город: {city or region or 'не указан'}\n"
        f"Сертификаты: {certs or 'нет данных'}\n"
        f"Мин. заказ: {min_order or 'не указан'} руб\n\n"
        "Пиши только описание, без заголовков и лишнего текста. На русском языке."
    )

    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        f"{ollama_url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            return result.get("response", "").strip()
    except Exception as exc:
        print(f"  ⚠ Ollama error for '{name}': {exc}", file=sys.stderr)
        return ""


def parse_bool(val: str) -> bool:
    return val.strip().lower() in ("1", "true", "yes", "да", "y")


def parse_list(val: str) -> list[str]:
    return [v.strip() for v in val.split(",") if v.strip()] if val.strip() else []


def row_to_supplier(row: dict) -> dict:
    supplier: dict = {}
    for field in ("name", "description", "city", "region", "phone", "email",
                  "website", "min_order_unit", "price_range_description",
                  "delivery_conditions", "source_url", "source_platform", "notes",
                  "category_name"):
        val = row.get(field, "").strip()
        if val:
            supplier[field] = val

    raw_amount = row.get("min_order_amount", "").strip()
    if raw_amount:
        try:
            supplier["min_order_amount"] = float(raw_amount)
        except ValueError:
            pass

    raw_certs = row.get("has_certificates", "").strip()
    if raw_certs:
        supplier["has_certificates"] = parse_bool(raw_certs)

    certs_list = parse_list(row.get("certificate_types", ""))
    if certs_list:
        supplier["certificate_types"] = certs_list

    regions_list = parse_list(row.get("delivery_regions", ""))
    if regions_list:
        supplier["delivery_regions"] = regions_list

    return supplier


def bulk_upload(suppliers: list[dict], api_url: str) -> tuple[int, int]:
    payload = json.dumps({"suppliers": suppliers}).encode()
    req = urllib.request.Request(
        f"{api_url}/api/suppliers/bulk",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())
    return result["created"], result["updated"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Import suppliers from CSV")
    parser.add_argument("csv_file", help="Path to CSV file")
    parser.add_argument("--enrich", action="store_true",
                        help="Use Ollama to generate missing descriptions")
    parser.add_argument("--api-url", default=DEFAULT_API_URL,
                        help=f"Backend API URL (default: {DEFAULT_API_URL})")
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL,
                        help=f"Ollama URL (default: {DEFAULT_OLLAMA_URL})")
    parser.add_argument("--ollama-model", default=DEFAULT_OLLAMA_MODEL,
                        help=f"Ollama model (default: {DEFAULT_OLLAMA_MODEL})")
    args = parser.parse_args()

    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"File not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    with csv_path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    print(f"Loaded {len(rows)} rows from {csv_path.name}")

    suppliers = []
    for i, row in enumerate(rows, 1):
        s = row_to_supplier(row)
        if not s.get("name"):
            print(f"  Row {i}: skipped (no name)")
            continue

        if args.enrich and not s.get("description"):
            print(f"  [{i}/{len(rows)}] Enriching '{s['name']}'…")
            desc = enrich_description(row, args.ollama_url, args.ollama_model)
            if desc:
                s["description"] = desc

        suppliers.append(s)

    if not suppliers:
        print("Nothing to upload.")
        return

    total_created = total_updated = 0
    for start in range(0, len(suppliers), BATCH_SIZE):
        batch = suppliers[start:start + BATCH_SIZE]
        print(f"Uploading rows {start + 1}–{start + len(batch)}…")
        try:
            created, updated = bulk_upload(batch, args.api_url)
            total_created += created
            total_updated += updated
        except urllib.error.URLError as exc:
            print(f"Upload failed: {exc}", file=sys.stderr)
            sys.exit(1)

    print(f"\nDone. Created: {total_created}, updated: {total_updated}")


if __name__ == "__main__":
    main()
