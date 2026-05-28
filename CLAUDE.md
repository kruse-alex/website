# alexknowsdata.com — Portfolio Site

Personal portfolio for **Alex Held**, Lead Data Science at Der Spiegel, Hamburg.

## Repo & Deployment

- **Live site:** https://www.alexknowsdata.com
- **GitHub:** https://github.com/alexknowsdata/website (account: `alexknowsdata`)
- **Netlify:** auto-deploys on every push to `master`, no build step
- **Deploy:** `git add`, `git commit`, `git push origin master`

## Stack

Plain HTML/CSS/JS — no framework, no build tool. Everything lives in `index.html` with styles inline. Do not introduce Hugo, npm, or any build step.

## File Structure

```
index.html              — entire site (nav, hero, Work, About)
posts/*.html            — 20 subpages (old blog posts + bird viz)
public/post/*/          — images used by subpages
akr.jpg                 — profile photo (About section)
netlify.toml            — publish = ".", command = "" (no build)
```

## Design

- Dark terminal aesthetic: base `#0d1117`, accent `#58a6ff`
- Fonts: JetBrains Mono (mono/headings) + Inter (body)
- Nav brand: `alex@held:~$` — typewriter animation + blinking cursor on page load
- All content uses `.list-block` / `.list-item` rows (no cards)

## Site Sections

**Work** (`#work`)
- Towards Data Science (2 articles, 2024)
- The Audiencers (3 articles, 2023/2024/2025)
- Talks & Webinars (3 talks, 2023)
- Medium (3 visible + 5 in toggle)
- Data Viz (birds 2024, marathon, finedust, stadtrad, ddj, generative art, attribution)
- More older work (collapsible archive)
- Hackathons & competitions (3 visible + 2 in toggle)

**About** (`#about`)
- Bio text (2 paragraphs)
- Profile photo: `akr.jpg` (circular)
- Timeline: Lead DS @ Der Spiegel → Data Analyst @ ZEIT Online → Data Journalist @ Spiegel Online (Google News Fellowship) → Data Analyst @ etracker → M.Sc. Business Analytics @ Uni Duisburg-Essen
- LinkedIn + Medium links at bottom of page

## Key Decisions

- No footer — page ends after About
- No skill tags in About (removed)
- Sub-headings in Work are short publication/venue names, not verbose descriptions
- Old blog post subpages all use `alex@held:~$` nav brand and `← alex held` footer link
- OG/Twitter card meta tags point to `https://www.alexknowsdata.com/akr.jpg`
- Name is **Alex Held** everywhere (not Alexander)

---

## Spiegel Corpus Tool — `/spiegel-corpus`

An interactive word-frequency explorer for Der Spiegel's 80th anniversary (2027). Lives at `alexknowsdata.com/spiegel-corpus`. The tool is a **separate Svelte app** — do NOT apply the "plain HTML/no build step" rule to it.

### Source project
`/Users/helda/Users/helda/word-explorer/` — Svelte 4 + Vite 5 (Node 20.18.2 is incompatible with Vite 7, do not upgrade).

### Deploy workflow
The Svelte app builds to static files and gets copied here as a pre-built subfolder:
```bash
cd /Users/helda/Users/helda/word-explorer
bash deploy.sh
# builds, copies dist/ → alexknowsdata/spiegel-corpus/, commits & pushes
```
Never edit files inside `spiegel-corpus/` directly — they are generated. Edit the source in `word-explorer/` and redeploy.

### What's built
A dark-themed scrollable data journalism article with three interactive chart sections:

**Chart 1 — Multi-term word explorer** (main tool)
- Multi-tag combobox: type a term → autocomplete dropdown with counts → adds colored chip + matching line
- Up to 8 terms simultaneously, each gets next color from palette
- Color palette (in order): `hsla(184,100%,50%)` cyan → `hsla(30,100%,50%)` orange → `hsla(327,100%,50%)` pink → `hsla(144,100%,45%)` green → ...
- Clicking a preset adds/removes that term; active presets show their term's color
- Toggle: "je 100.000" (normalized) vs "Anzahl" (raw count)
- Clear all button (×), per-chip remove (×)

**Chart 2 — Group breakdown**
Single term, 6 Ressort lines: Politik, Wirtschaft, Gesellschaft (panorama slug), Kultur, Sport, Wissenschaft.

**Chart 3 — Binary comparison**
Single term, 2 lines: Autorinnen (female authors) vs. Autoren (male authors). Gender resolved via author UUID → spiegel.de scrape → `gender_guesser`.

**Scrollytelling section**
5 hardcoded narrative steps in `App.svelte` (`scrollySteps` array) — still placeholder text. Replace with real Spiegel findings once full corpus is processed.

### Key source files
- `src/App.svelte` — article layout, prose text, scrollySteps array, all global styles
- `src/lib/WordExplorer.svelte` — multi-term explorer (Chart 1)
- `src/lib/GroupExplorer.svelte` — group breakdown (Chart 2)
- `src/lib/BinaryExplorer.svelte` — binary comparison (Chart 3)
- `src/lib/LineChart.svelte` — reusable D3 SVG chart (dark theme, right-aligned Y-axis, hover tooltip)
- `src/lib/Scrolly.svelte` — IntersectionObserver scrollytelling
- `src/lib/data.js` — API client; auto-switches between `localhost:8000` (dev) and `spiegel-corpus-api.fly.dev` (prod)

### Visual style
Matches the aesthetic of the ZEIT Bundestag word-frequency article exactly — values extracted directly from that page:
- Body: `rgb(18,18,18)` bg, white text, `"Helvetica Neue", Helvetica, Arial, sans-serif`
- Article background: layered radial gradients — teal `rgba(0,136,160,...)`, orange `rgba(247,105,6,...)`, green `rgba(38,150,97,...)`
- Chart lines: neon green `hsla(144,100%,45%)` for single term
- Active chip: `rgba(255,0,140,0.3)` hot-pink bg, `border-radius: 4px`, `font-weight: 600`
- Preset buttons: `rgba(255,255,255,0.1)` bg, semi-white text, `border-radius: 4px`
- Grid lines: `rgba(255,255,255,0.12)`, axis labels `rgba(255,255,255,0.5)` at 13px

### Data pipeline (BUILT + DEPLOYED)

#### Live URLs
- **API**: `https://spiegel-corpus-api.fly.dev` (Fly.io, Frankfurt, auto-sleep)
- **Frontend**: `https://www.alexknowsdata.com/spiegel-corpus`

#### File layout
```
data/                                              — gitignored
  *.csv                                            — source articles (drop new files here)
  corpus.db                                        — SQLite output (~46MB)
  author_gender.json                               — author UUID → name + gender (739 scraped)
pipeline/
  build_corpus.py                                  — CSV(s) → corpus.db (handles old+new CSV formats)
  scrape_authors.py                                — incremental author ID scraper (spiegel.de)
  api.py                                           — FastAPI (4 endpoints)
  requirements.txt                                 — fastapi + uvicorn
Dockerfile                                         — builds API image (corpus.db baked in)
fly.toml                                           — Fly.io config (app: spiegel-corpus-api, region: fra)
.dockerignore
```

#### Full workflow when new data arrives
```bash
# 1. Drop new CSV(s) into data/
# 2. Scrape any new author IDs
python3 pipeline/scrape_authors.py
# 3. Rebuild corpus
python3 pipeline/build_corpus.py
# 4. Deploy API
flyctl deploy
# 5. Deploy frontend (if changed)
cd /Users/helda/Users/helda/word-explorer && bash deploy.sh
```

#### Local dev
```bash
python3 -m uvicorn pipeline.api:app --port 8000   # API
cd /Users/helda/Users/helda/word-explorer && npm run dev  # → localhost:5174/spiegel-corpus/
```

#### SQLite schema
```sql
word_counts(word TEXT, year INT, channel TEXT, count INT)
year_totals(year INT, channel TEXT, total_words INT)

-- author gender split (female / male / unknown)
gender_counts(word TEXT, year INT, gender TEXT, count INT)
gender_totals(year INT, gender TEXT, total_words INT)

-- autocomplete
vocab(word TEXT PRIMARY KEY, total_count INT)
```

#### API endpoints
- `GET /api/term/{word}` → `[{year, value, count}]` — per-100k + raw, all channels combined
- `GET /api/group/{word}` → `[{key, label, color, data}]` — 6 Ressort lines
- `GET /api/binary/{word}` → `[{key, label, color, data}]` — Autorinnen vs. Autoren (gender split)
- `GET /api/autocomplete?q=prefix` → `[{word, count}]`

#### Chart 2 — Ressort groups (6 lines)
Politik, Wirtschaft, Gesellschaft (panorama), Kultur, Sport, Wissenschaft

#### Chart 3 — Binary split: author gender
- Female authors (Autorinnen): color `hsla(327, 100%, 50%, 0.99)`
- Male authors (Autoren): color `hsla(184, 100%, 50%, 0.99)`
- Gender resolved from `authors` field (UUID) → `data/author_gender.json` lookup
- Lookup built by scraping `https://www.spiegel.de/impressum/autor-{id}` → extract `<h1>` name → `gender_guesser`
- 739 authors scraped, 84% classified; unknown articles excluded from binary chart
- To add new authors: run `pipeline/scrape_authors.py` (incremental, skips existing IDs)

#### Methodology (based on ZEIT Bundestag reference project)
- **Normalization**: annual count ÷ total words that year × 100,000
- **Min frequency**: only index words with total_count ≥ 5 (filters rare typos)
- **Case**: fully lowercased before counting
- **No stemming / lemmatization**: keep raw word forms — "Klimakatastrophe" and "Klimawandel" are separate entries; users combine variants via multi-term input
- **Hyphenation**: rejoin end-of-line word breaks before tokenizing
- **Tech**: SQLite + FastAPI (ZEIT used Elasticsearch in Docker — overkill for our scale)

#### TODO
- **Full multi-year corpus**: currently have 2024 (6,891 articles) + yearly sample (3/year, 1947–2026). Load full data → re-run pipeline → time-series becomes meaningful
- **Scrollytelling text**: `scrollySteps` array in `App.svelte` still has placeholder terms/prose — fill with real findings
- **Preset terms**: curate Chart 1 + 2 presets to most interesting Spiegel-specific words
- **Fly.io**: run `flyctl scale count 1` to drop to 1 machine (saves cost); prune old images with `flyctl image prune`

ZEIT reference articles:
- https://www.zeit.de/politik/deutschland/2024-09/75-jahre-bundestag-reden-sprache-parteien (user-facing methodology)
- https://blog.zeit.de/dev/reden-im-bundestag-auf-knopfdruck-skalierbar/ (tech blog)
