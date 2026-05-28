#!/usr/bin/env python3
"""
Build SQLite word-frequency corpus from Spiegel article CSV(s).

Handles two CSV formats:
  Old: plain_text + year columns
  New: body (JSON blocks) + _publish_year_cest columns

Schema:
  word_counts(word, year, channel, count)
  year_totals(year, channel, total_words)
  gender_counts(word, year, gender, count)   -- female / male / unknown
  gender_totals(year, gender, total_words)
  vocab(word, total_count)                   -- for autocomplete

Methodology (ZEIT Bundestag reference):
  - lowercase, raw word forms (no stemming)
  - min 5 total occurrences to enter vocab
  - normalize: count / total_words * 100_000

Usage:
  python3 pipeline/build_corpus.py                    # uses DATA_DIR defaults
  python3 pipeline/build_corpus.py path/to/file.csv   # single file
"""

import csv
import json
import re
import ast
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import gender_guesser.detector as gender_lib

DATA_DIR  = Path(__file__).parent.parent / "data"
DB_PATH   = DATA_DIR / "corpus.db"
MIN_COUNT = 5

# All CSV files to include — add more as the full corpus arrives
DEFAULT_CSVS = [
    DATA_DIR / "spon_articles_with_body_and_plain_text.csv",
    DATA_DIR / "Article_Metadata_Yearly_Sample_SPON_Paid (1).csv",
]

AUTHOR_GENDER_PATH = DATA_DIR / "author_gender.json"

csv.field_size_limit(10_000_000)
_gender_detector = gender_lib.Detector()

# Loaded at build time from scraped spiegel.de author pages
_author_gender: dict = {}
if AUTHOR_GENDER_PATH.exists():
    _author_gender = {k: v["gender"] for k, v in json.load(open(AUTHOR_GENDER_PATH)).items()}


# ── Text extraction ────────────────────────────────────────────────────────────

def extract_plain_text(row: dict) -> str:
    """Return plain text from either format."""
    # Old format: dedicated plain_text column
    if row.get("plain_text", "").strip():
        return row["plain_text"]
    # New format: body is a JSON array of content blocks
    body = row.get("body", "")
    if not body or body.strip() in ("", "[]", "null"):
        return ""
    try:
        blocks = json.loads(body)
        parts = []
        for block in blocks:
            if isinstance(block, dict) and "text" in block:
                text = re.sub(r"<[^>]+>", " ", block["text"])
                text = re.sub(r"\s+", " ", text).strip()
                if text:
                    parts.append(text)
        return " ".join(parts)
    except Exception:
        return ""


def extract_year(row: dict) -> int | None:
    """Return publication year from either format."""
    for col in ("year", "_publish_year_cest"):
        val = row.get(col, "").strip()
        if val:
            try:
                yr = int(val)
                if 1945 <= yr <= 2030:
                    return yr
            except ValueError:
                pass
    # fallback: parse publish_date
    date = row.get("publish_date", "")
    if date and len(date) >= 4:
        try:
            return int(date[:4])
        except ValueError:
            pass
    return None


def extract_channel(row: dict) -> str:
    try:
        return ast.literal_eval(row["channel"]).get("slug", "unknown")
    except Exception:
        pass
    try:
        return json.loads(row["channel"]).get("slug", "unknown")
    except Exception:
        return "unknown"


# ── Gender detection ───────────────────────────────────────────────────────────

def detect_gender_from_authors(authors_raw: str) -> str:
    """Resolve gender from authors field (handles JSON and Python-dict string formats)."""
    if not authors_raw or authors_raw.strip() in ("", "[]", "null"):
        return "unknown"
    authors = None
    try:
        authors = json.loads(authors_raw) or []
    except Exception:
        pass
    if authors is None:
        try:
            authors = ast.literal_eval(authors_raw) or []
        except Exception:
            return "unknown"
    if not authors:
        return "unknown"
    genders = set()
    for a in authors:
        aid = a.get("reference", {}).get("id", "")
        g = _author_gender.get(aid, "unknown")
        if g != "unknown":
            genders.add(g)
    if len(genders) == 1:
        return genders.pop()
    return "unknown"  # mixed or all-unknown


# ── Tokenizer ─────────────────────────────────────────────────────────────────

def tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"-\n", "", text)
    return re.findall(r"[a-zäöüß]+", text)


# ── Pipeline ──────────────────────────────────────────────────────────────────

def build(csv_paths: list[Path], db_path: Path) -> None:
    word_counts:   Counter = Counter()
    year_totals:   Counter = Counter()
    gender_counts: Counter = Counter()
    gender_totals: Counter = Counter()
    skipped = 0

    for csv_path in csv_paths:
        if not csv_path.exists():
            print(f"  Skipping (not found): {csv_path.name}")
            continue
        print(f"Reading {csv_path.name} …")
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=",")
            # detect delimiter: old files use semicolons
            sample = csv_path.read_text(encoding="utf-8")[:2000]
            delim = ";" if sample.count(";") > sample.count(",") else ","

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=delim)
            for i, row in enumerate(reader):
                if i % 500 == 0:
                    print(f"  {i} rows …", end="\r")

                year = extract_year(row)
                if year is None:
                    skipped += 1
                    continue

                text = extract_plain_text(row)
                if not text.strip():
                    skipped += 1
                    continue

                channel = extract_channel(row)
                gender  = detect_gender_from_authors(row.get("authors", "[]"))
                tokens  = tokenize(text)

                for tok in tokens:
                    word_counts[(tok, year, channel)] += 1
                    gender_counts[(tok, year, gender)] += 1
                year_totals[(year, channel)] += len(tokens)
                gender_totals[(year, gender)] += len(tokens)

        print(f"  Done: {csv_path.name}")

    print(f"\nSkipped rows (no year or no text): {skipped}")
    print(f"Unique (word,year,channel) combos: {len(word_counts)}")

    vocab: Counter = Counter()
    for (word, _, _), cnt in word_counts.items():
        vocab[word] += cnt

    print(f"Unique words before filter: {len(vocab)}")
    keep = {w for w, c in vocab.items() if c >= MIN_COUNT}
    print(f"Unique words after min={MIN_COUNT} filter: {len(keep)}")

    print(f"Writing {db_path} …")
    db_path.unlink(missing_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript("""
        CREATE TABLE word_counts (
            word TEXT NOT NULL, year INTEGER NOT NULL,
            channel TEXT NOT NULL, count INTEGER NOT NULL
        );
        CREATE TABLE year_totals (
            year INTEGER NOT NULL, channel TEXT NOT NULL,
            total_words INTEGER NOT NULL
        );
        CREATE TABLE gender_counts (
            word TEXT NOT NULL, year INTEGER NOT NULL,
            gender TEXT NOT NULL, count INTEGER NOT NULL
        );
        CREATE TABLE gender_totals (
            year INTEGER NOT NULL, gender TEXT NOT NULL,
            total_words INTEGER NOT NULL
        );
        CREATE TABLE vocab (
            word TEXT PRIMARY KEY, total_count INTEGER NOT NULL
        );
    """)
    con.executemany("INSERT INTO word_counts VALUES (?,?,?,?)",
        ((w, y, ch, c) for (w, y, ch), c in word_counts.items() if w in keep))
    con.executemany("INSERT INTO year_totals VALUES (?,?,?)",
        ((y, ch, t) for (y, ch), t in year_totals.items()))
    con.executemany("INSERT INTO gender_counts VALUES (?,?,?,?)",
        ((w, y, g, c) for (w, y, g), c in gender_counts.items() if w in keep))
    con.executemany("INSERT INTO gender_totals VALUES (?,?,?)",
        ((y, g, t) for (y, g), t in gender_totals.items()))
    con.executemany("INSERT INTO vocab VALUES (?,?)",
        ((w, c) for w, c in vocab.items() if w in keep))
    con.executescript("""
        CREATE INDEX idx_wc_word_year ON word_counts(word, year);
        CREATE INDEX idx_wc_word_ch   ON word_counts(word, channel);
        CREATE INDEX idx_gc_word_year ON gender_counts(word, year);
        CREATE INDEX idx_gc_word_gen  ON gender_counts(word, gender);
        CREATE INDEX idx_vocab_word   ON vocab(word);
    """)
    con.commit()
    con.close()
    print("Done.")


if __name__ == "__main__":
    paths = [Path(p) for p in sys.argv[1:]] if len(sys.argv) > 1 else DEFAULT_CSVS
    build([p for p in paths if p.exists()], DB_PATH)
