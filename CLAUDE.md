# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A two-module portfolio data-engineering project that fetches weather forecasts for 6 Indian cities from the Open-Meteo API, stores them in PostgreSQL (Neon cloud), and visualizes them on a live auto-refreshing web dashboard deployed to Render.com.

- **`weather_pipeline/`** — Python ETL: extract from Open-Meteo → transform with pandas → upsert to PostgreSQL → SQL insights + matplotlib charts. Runs daily at 08:00 via Render Cron Job.
- **`weather_dashboard/`** — Flask REST API + single-page Chart.js dashboard. Reads the same PostgreSQL DB. Auto-refreshes every 30s.

The two modules share **only** the `weather` table in PostgreSQL — that table is the contract between them.

Live demo: https://weather-dashboard-bnw1.onrender.com
GitHub: https://github.com/Muthu2405/Weather_Project

## Common commands

All commands assume you've `cd`'d into the relevant module folder.

### Pipeline (`weather_pipeline/`)

```bash
# Activate the existing venv (one is already committed at pipeline_env/)
pipeline_env\Scripts\activate                  # Windows
source pipeline_env/bin/activate              # Mac/Linux

# Run the full ETL once
python pipeline.py

# Run daily at a scheduled time (default 08:00)
python pipeline.py --schedule
python pipeline.py --schedule --time 07:30

# Test a single step in isolation
python extract.py      # API fetch only
python transform.py    # cleaning + enrichment only
python analyze.py      # SQL insights against existing data
python visualize.py    # regenerate the 4 PNG charts
```

> **Note:** Running `python transform.py` or `python load.py` standalone will fail with `ImportError: cannot import name 'CITY_CONFIG'`. Their `__main__` blocks reference a symbol that does not exist in `extract.py` (only `CITIES` plural is defined). Only `python pipeline.py` works end-to-end and `python extract.py` works for the extract step.

### Dashboard (`weather_dashboard/`)

```bash
dashboard_env\Scripts\activate                # Windows
source dashboard_env/bin/activate            # Mac/Linux

python app.py                                 # http://localhost:5000
```

Production uses Gunicorn per the `Procfile`: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`.

## Environment variables

Both modules read the same five vars from a local `.env` (no `.env.example` files exist — create one from the table below when setting up a new environment):

| Var | Default | Notes |
|---|---|---|
| `DB_USER` | `postgres` | |
| `DB_PASSWORD` | `password` | |
| `DB_HOST` | `localhost` | `neon.tech` / `amazonaws` hostnames auto-append `?sslmode=require` |
| `DB_PORT` | `5432` | |
| `DB_NAME` | `weather_db` | |

The dashboard additionally reads `PORT` (default `5000`) for the Flask dev server.

## Architecture

### Data flow

```
Open-Meteo API (free, no key)
    ↓ fetch_all_cities(CITIES)
extract.py
    ↓ list of (city_dict, raw_json)
transform.transform_weather → pandas DataFrame (12 columns)
    ↓
load.load_weather → UPSERT into weather table
    ↓
Neon PostgreSQL  ◄──────────  weather_dashboard/app.py
                                         ↓ JSON
                              templates/index.html (Chart.js, auto-refresh 30s)
```

### `weather_pipeline/` module map

| File | Role | Key entry points |
|---|---|---|
| `extract.py` | Open-Meteo client. Hardcodes `CITIES` list at line 17 (Chennai, Mumbai, Delhi, Bangalore, Kolkata, Madurai). | `fetch_weather(city)`, `fetch_all_cities(cities=CITIES)` |
| `transform.py` | Raw JSON → clean DataFrame. Derives `temp_avg`, `temp_range`, `humidity_avg`, `is_rainy` (>1 mm), `condition` (rule-based classifier). | `transform_weather(raw_data, city_name)`, `classify_condition(row)` |
| `load.py` | SQLAlchemy engine + per-row `INSERT … ON CONFLICT (date, city) DO UPDATE` upsert (load.py:99-122). One round-trip per row. | `get_db_engine()`, `create_table_if_not_exists(engine)`, `load_weather(df, engine)` |
| `analyze.py` | 6 SQL insight queries printed via pandas. Uses Postgres-specific `COUNT(*) FILTER (WHERE …)` and `::numeric` casts. | `analyze(engine)` |
| `visualize.py` | 4 matplotlib charts saved as PNG (committed to repo). `chart_dashboard` title uses `df['city'].iloc[0]` — misleading when DB holds 6 cities. | `visualize()` + 4 chart functions |
| `pipeline.py` | Orchestrator. `run_pipeline()` line 35 = Extract → per-city Transform+Load → Analyze → Visualize. `run_scheduled(run_time="08:00")` line 106 = once-now + 60s poll loop. Logs to stdout and `pipeline.log`. | `run_pipeline`, `run_scheduled` |

### `weather_dashboard/` module map

| File | Role | Notes |
|---|---|---|
| `app.py` | Flask app, 6 routes. Cloud-SSL detection mirrors the pipeline's (line 29). | See "API endpoints" below |
| `templates/index.html` | Single-page UI. All CSS/JS inlined — no `static/` dir, no build step. Chart.js 4.4.0 via CDN, Google Fonts (Syne + DM Mono). | `loadCities()` / `fetchAll()` / `setInterval(…, 30_000)` near line 482 |
| `Procfile` | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2` | |
| `render.yaml` | Render blueprint (web service, python env) | |

### Database schema (the contract between the two modules)

```sql
CREATE TABLE weather (
    id              SERIAL PRIMARY KEY,
    date            DATE,
    city            TEXT,
    temp_max        FLOAT,
    temp_min        FLOAT,
    temp_avg        FLOAT,    -- derived in transform
    temp_range      FLOAT,    -- derived in transform
    precipitation   FLOAT,
    wind_speed_max  FLOAT,
    humidity_avg    FLOAT,    -- derived in transform
    is_rainy        BOOLEAN,  -- derived: precipitation > 1 mm
    condition       TEXT,     -- derived classifier output
    loaded_at       TIMESTAMP,
    UNIQUE (date, city)       -- enables the upsert in load.py:99-122
);
```

### API endpoints (dashboard)

| Method | Path | Behavior |
|---|---|---|
| `GET` | `/` | Renders `templates/index.html` |
| `GET` | `/api/cities` | Distinct city names, sorted ASC |
| `GET` | `/api/latest?city=…` | Most recent row for a city (404 if none) |
| `GET` | `/api/forecast?city=…` | All rows for a city ASC by date. **No `LIMIT` when `city` is omitted** — pulls the whole table. |
| `GET` | `/api/stats?city=…` | Aggregates (`MAX`, `MIN`, `AVG`, `COUNT(*) FILTER (WHERE is_rainy)`). Will throw on empty table at `float(row.avg_humidity)`. |
| `GET` | `/api/debug` | Echoes which `DB_*` env vars are set (password masked). Public — consider gating. |

A global `@app.errorhandler(Exception)` returns JSON `{"error": "..."}` with HTTP 500.

## Things to know before editing

- **Adding/removing a city:** edit the `CITIES` list in `extract.py:17` only. The dashboard auto-discovers cities via `/api/cities`.
- **The city list is the schema's partition key.** Every query in both modules includes `city` either in the WHERE clause or as a required column. Don't add a city-aware query that doesn't filter on `city` — `/api/forecast` without `?city=` is a known footgun.
- **`pipeline.log` is committed (currently empty).** `pipeline.py` configures a `FileHandler` with no `mode="w"`, so it should accumulate; an empty file means the pipeline hasn't been run since clone.
- **Generated `chart_*.png` files are committed** in `weather_pipeline/`. They regenerate every time `pipeline.py` runs.
- **`.env` files contain real Neon credentials and are tracked in git history.** Treat the credentials as compromised (rotate if needed) and avoid committing any new `.env` changes.
- **`plotly` is in `weather_pipeline/requirements.txt` but never imported.** Safe to remove.
- **No top-level `.gitignore`.** `pipeline_env/`, `dashboard_env/`, `__pycache__/`, `pipeline.log`, and `chart_*.png` are all tracked. Don't add new venv or `.env` files without expecting them to be tracked.
- **The standalone-module `__main__` blocks in `transform.py:112` and `load.py:148` are broken** (reference nonexistent `CITY_CONFIG`). The README's "test individual steps" instructions are aspirational for those two. Fix only if needed — `python pipeline.py` covers the happy path.
- **Cloud SSL detection is brittle:** only `neon.tech` and `amazonaws` substrings trigger `?sslmode=require`. Supabase, Render Postgres, and Azure hosts will not get SSL appended and may fail to connect.

## Deployment

Production runs on Render.com:
- **Dashboard** = Web Service, root dir `weather_dashboard/`, start command from `Procfile`, env vars set in Render dashboard.
- **Pipeline** = Cron Job, root dir `weather_pipeline/`, start command `python pipeline.py`, schedule `0 8 * * *`.

Both services share the same five `DB_*` env vars pointing at a single Neon PostgreSQL instance.
