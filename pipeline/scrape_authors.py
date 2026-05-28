#!/usr/bin/env python3
"""
Scrape Spiegel author pages to build author_id → name/gender lookup.

Reads all CSVs in data/ for author IDs, skips already-scraped ones,
writes results to data/author_gender.json incrementally.

Usage:
  python3 pipeline/scrape_authors.py
"""

import ast
import csv
import json
import re
import time
import urllib.request
from pathlib import Path

import gender_guesser.detector as gender_lib

DATA_DIR   = Path(__file__).parent.parent / "data"
OUTPUT     = DATA_DIR / "author_gender.json"
DELAY      = 0.2   # seconds between requests

csv.field_size_limit(10_000_000)
_detector = gender_lib.Detector()


def detect_gender(first: str) -> str:
    for part in [first, first.split("-")[0]]:
        g = _detector.get_gender(part)
        if g in ("female", "mostly_female"): return "female"
        if g in ("male",   "mostly_male"):   return "male"
    return "unknown"


def collect_ids(data_dir: Path, existing: set) -> set:
    new_ids = set()
    for path in data_dir.glob("*.csv"):
        delim = ";" if ";" in path.read_text(encoding="utf-8", errors="ignore")[:2000] else ","
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter=delim):
                raw = row.get("authors", "").strip()
                if not raw or raw in ("[]", "null"):
                    continue
                try:
                    authors = json.loads(raw)
                except Exception:
                    try:
                        authors = ast.literal_eval(raw)
                    except Exception:
                        continue
                for a in (authors or []):
                    aid = a.get("reference", {}).get("id", "")
                    if aid and aid not in existing:
                        new_ids.add(aid)
    return new_ids


def scrape_author(aid: str) -> dict:
    url = f"https://www.spiegel.de/impressum/autor-{aid}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8", errors="ignore")
        m = re.search(r"<h1[^>]*>\s*(.*?)\s*</h1>", html, re.S)
        if m:
            name = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            first = name.split()[0] if name else ""
            return {"name": name, "first": first, "gender": detect_gender(first) if first else "unknown"}
    except Exception:
        pass
    return {"name": "", "first": "", "gender": "unknown"}


def main() -> None:
    existing: dict = json.loads(OUTPUT.read_text()) if OUTPUT.exists() else {}
    new_ids = collect_ids(DATA_DIR, set(existing.keys()))

    if not new_ids:
        print("No new author IDs found.")
    else:
        print(f"Scraping {len(new_ids)} new authors …")
        for i, aid in enumerate(sorted(new_ids), 1):
            result = scrape_author(aid)
            existing[aid] = result
            if i % 50 == 0 or i == len(new_ids):
                print(f"  {i}/{len(new_ids)} — {result['name']} ({result['gender']})")
            time.sleep(DELAY)
        OUTPUT.write_text(json.dumps(existing, indent=2, ensure_ascii=False))

    genders = [v["gender"] for v in existing.values()]
    print(f"\nTotal: {len(existing)} authors — female={genders.count('female')}, "
          f"male={genders.count('male')}, unknown={genders.count('unknown')}")


if __name__ == "__main__":
    main()
