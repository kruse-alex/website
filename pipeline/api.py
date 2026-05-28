#!/usr/bin/env python3
"""
Spiegel corpus word-frequency API.

Endpoints:
  GET /api/term/{word}            → [{year, value (per 100k)}]
  GET /api/group/{word}           → [{key, label, color, data:[{year,value}]}]
  GET /api/autocomplete?q=prefix  → [{word, count}]

Run locally:
  uvicorn pipeline.api:app --reload --port 8000
"""

import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

DB_PATH = Path(os.environ.get("DB_PATH", str(Path(__file__).parent.parent / "data" / "corpus.db")))

# Spiegel Ressorts for Chart 2 — key maps to channel slug in DB
GROUPS = [
    {"key": "politik",        "label": "Politik",        "color": "hsla(327, 100%, 50%, 0.99)"},
    {"key": "wirtschaft",     "label": "Wirtschaft",     "color": "rgb(55, 167, 228)"},
    {"key": "panorama",       "label": "Gesellschaft",   "color": "rgb(91, 167, 0)"},
    {"key": "kultur",         "label": "Kultur",         "color": "rgb(243, 212, 59)"},
    {"key": "sport",          "label": "Sport",          "color": "rgb(193, 49, 151)"},
    {"key": "wissenschaft",   "label": "Wissenschaft",   "color": "rgb(28, 227, 183)"},
]

app = FastAPI(title="Spiegel Corpus API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@contextmanager
def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
    finally:
        con.close()


@app.get("/api/term/{word}")
def term_data(word: str):
    """Return per-100k frequency and raw count per year, summed across all channels."""
    word = word.lower()
    with get_db() as db:
        rows = db.execute("""
            SELECT wc.year,
                   SUM(wc.count) AS count,
                   ROUND(SUM(wc.count) * 100000.0 / SUM(yt.total_words), 2) AS value
            FROM word_counts wc
            JOIN year_totals yt USING(year, channel)
            WHERE wc.word = ?
            GROUP BY wc.year
            ORDER BY wc.year
        """, (word,)).fetchall()
    if not rows:
        return []
    return [{"year": r["year"], "value": r["value"], "count": r["count"]} for r in rows]


@app.get("/api/group/{word}")
def group_data(word: str):
    """Return per-100k frequency and raw count per year for each Ressort."""
    word = word.lower()
    result = []
    with get_db() as db:
        for g in GROUPS:
            rows = db.execute("""
                SELECT wc.year,
                       SUM(wc.count) AS count,
                       ROUND(SUM(wc.count) * 100000.0 / SUM(yt.total_words), 2) AS value
                FROM word_counts wc
                JOIN year_totals yt USING(year, channel)
                WHERE wc.word = ? AND wc.channel = ?
                GROUP BY wc.year
                ORDER BY wc.year
            """, (word, g["key"])).fetchall()
            result.append({
                "key":   g["key"],
                "label": g["label"],
                "color": g["color"],
                "data":  [{"year": r["year"], "value": r["value"], "count": r["count"]} for r in rows],
            })
    return result


@app.get("/api/binary/{word}")
def binary_data(word: str):
    """Return per-100k frequency per year split by author gender (female / male)."""
    word = word.lower()
    GENDERS = [
        {"key": "female", "label": "Autorinnen", "color": "hsla(327, 100%, 50%, 0.99)"},
        {"key": "male",   "label": "Autoren",    "color": "hsla(184, 100%, 50%, 0.99)"},
    ]
    result = []
    with get_db() as db:
        for g in GENDERS:
            rows = db.execute("""
                SELECT gc.year,
                       SUM(gc.count) AS count,
                       ROUND(SUM(gc.count) * 100000.0 / SUM(gt.total_words), 2) AS value
                FROM gender_counts gc
                JOIN gender_totals gt USING(year, gender)
                WHERE gc.word = ? AND gc.gender = ?
                GROUP BY gc.year
                ORDER BY gc.year
            """, (word, g["key"])).fetchall()
            result.append({
                "key":   g["key"],
                "label": g["label"],
                "color": g["color"],
                "data":  [{"year": r["year"], "value": r["value"], "count": r["count"]} for r in rows],
            })
    return result


@app.get("/api/autocomplete")
def autocomplete(q: str = ""):
    """Return top matching words for autocomplete dropdown."""
    if len(q) < 2:
        return []
    with get_db() as db:
        rows = db.execute("""
            SELECT word, total_count
            FROM vocab
            WHERE word LIKE ?
            ORDER BY total_count DESC
            LIMIT 10
        """, (q.lower() + "%",)).fetchall()
    return [{"word": r["word"], "count": r["total_count"]} for r in rows]
