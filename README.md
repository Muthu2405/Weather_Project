# 🌤️ Weather Data Pipeline & Live Dashboard

> A production-grade ETL pipeline that collects real-time weather data for 6 Indian cities, stores it in a cloud PostgreSQL database, and visualizes it on a live auto-refreshing web dashboard.

🔗 **Live Demo:** [weather-dashboard-bnw1.onrender.com](https://weather-dashboard-bnw1.onrender.com)

---

## 📸 Dashboard Preview

```
┌─────────────────────────────────────────────────────┐
│  Weather Live          ● Auto-refresh 30s           │
├─────────────────────────────────────────────────────┤
│  [Chennai] [Mumbai] [Delhi] [Bangalore] [Kolkata].. │
├─────────────────────────────────────────────────────┤
│                                                     │
│  CHENNAI              ☀️                            │
│  33.2°C    Hot        Today, 29 May                │
│  High 39°  Low 27°  Rain 0mm  Wind 15km/h          │
├─────────────────────────────────────────────────────┤
│  Today  Fri   Sat   Sun   Mon   Tue   Wed           │
│  ☀️     🌦️   ☀️    ☀️   🌦️   ☀️   ☀️             │
│  39°    37°   38°   37°   36°   37°   38°           │
├──────────────────┬──────────────────────────────────┤
│  Temperature     │  Precipitation                   │
│  [Line Chart]    │  [Bar Chart]                     │
├──────────────────┴──────────────────────────────────┤
│  Wind & Humidity [Dual Axis Chart]                  │
└─────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    DATA FLOW                            │
│                                                         │
│  Open-Meteo API (free, no key needed)                  │
│         │                                               │
│         ▼                                               │
│  extract.py   → fetch 6 cities × 7 days               │
│         │                                               │
│         ▼                                               │
│  transform.py → clean, enrich, classify               │
│         │                                               │
│         ▼                                               │
│  load.py      → upsert into PostgreSQL                 │
│         │                                               │
│         ▼                                               │
│  Neon PostgreSQL (cloud)                               │
│         │                                               │
│         ▼                                               │
│  Flask REST API  →  Live Dashboard                     │
│                      (Render.com)                       │
└─────────────────────────────────────────────────────────┘

SCHEDULE:  Render Cron Job runs pipeline daily at 8:00 AM
HOSTING:   Render Web Service (dashboard, always on)
DATABASE:  Neon PostgreSQL (cloud, free tier)
```

---

## 📁 Project Structure

```
weather-project/
│
├── weather_pipeline/              # ETL Pipeline
│   ├── extract.py                 # Fetch data from Open-Meteo API (6 cities)
│   ├── transform.py               # Clean, enrich, classify weather data
│   ├── load.py                    # Upsert into PostgreSQL (no duplicates)
│   ├── analyze.py                 # SQL insight queries
│   ├── visualize.py               # Generate matplotlib charts
│   ├── pipeline.py                # Orchestrator — runs all steps + scheduler
│   ├── requirements.txt
│   └── .env.example
│
└── weather_dashboard/             # Web Dashboard
    ├── app.py                     # Flask REST API (4 endpoints)
    ├── templates/
    │   └── index.html             # Dashboard UI (Chart.js + Vanilla JS)
    ├── requirements.txt
    ├── Procfile                   # Render/Railway deployment
    ├── render.yaml                # One-click Render config
    └── .env.example
```

---

## ✨ Features

### Pipeline
- Fetches weather for **6 Indian cities** in one run
- Fully automated — runs **daily at 8:00 AM** via Render Cron Job
- Graceful error handling — failed cities are skipped, not crashed
- **Upsert logic** — no duplicate records ever inserted
- Derives enriched fields: `temp_avg`, `temp_range`, `is_rainy`, `condition`
- Logs every step to terminal + `pipeline.log` file

### Dashboard
- **City selector** — switch between all 6 cities with one click
- **Auto-refreshes every 30 seconds** — no page reload needed
- 7-day forecast cards with weather condition icons
- 3 interactive charts (temperature, precipitation, wind & humidity)
- 6 stat cards — records and averages per city
- Fully responsive — works on mobile and desktop

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| API | Open-Meteo (free, no key) |
| Data Processing | Pandas |
| Database | PostgreSQL (Neon cloud) |
| ORM | SQLAlchemy |
| Web Framework | Flask |
| Charts | Chart.js |
| Scheduling | schedule / Render Cron Job |
| Hosting | Render.com (free tier) |
| Version Control | Git + GitHub |

---

## 🗄️ Database Schema

```sql
CREATE TABLE weather (
    id              SERIAL PRIMARY KEY,
    date            DATE,
    city            TEXT,
    temp_max        FLOAT,       -- Max temperature °C
    temp_min        FLOAT,       -- Min temperature °C
    temp_avg        FLOAT,       -- Avg temperature °C
    temp_range      FLOAT,       -- Daily temperature swing
    precipitation   FLOAT,       -- Rainfall in mm
    wind_speed_max  FLOAT,       -- Max wind speed km/h
    humidity_avg    FLOAT,       -- Average humidity %
    is_rainy        BOOLEAN,     -- True if rain > 1mm
    condition       TEXT,        -- Clear / Hot / Light Rain / etc.
    loaded_at       TIMESTAMP,
    UNIQUE (date, city)          -- Prevents duplicates
);
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Dashboard UI |
| GET | `/api/cities` | List all available cities |
| GET | `/api/latest?city=Chennai` | Latest weather for a city |
| GET | `/api/forecast?city=Chennai` | 7-day forecast for a city |
| GET | `/api/stats?city=Chennai` | Aggregate stats for a city |

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.11+
- PostgreSQL (local) or Neon account (free cloud)
- Git

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/weather-project.git
cd weather-project
```

### 2. Set up the pipeline
```bash
cd weather_pipeline
python -m venv pipeline_env
pipeline_env\Scripts\activate      # Windows
source pipeline_env/bin/activate   # Mac/Linux

pip install -r requirements.txt
cp .env.example .env
# Fill in your DB credentials in .env
```

### 3. Run the pipeline
```bash
python pipeline.py              # Run once
python pipeline.py --schedule   # Run daily at 8:00 AM
```

### 4. Set up the dashboard
```bash
cd ../weather_dashboard
python -m venv dashboard_env
dashboard_env\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
# Same DB credentials as pipeline
python app.py
```

Open **http://localhost:5000**

---

## 🚀 Deploy to Render (Free)

### Dashboard (Web Service)
| Setting | Value |
|---|---|
| Root Directory | `weather_dashboard` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2` |

### Pipeline (Cron Job)
| Setting | Value |
|---|---|
| Root Directory | `weather_pipeline` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python pipeline.py` |
| Schedule | `0 8 * * *` (daily at 8 AM) |

**Environment Variables (both services):**
```
DB_USER     = your_neon_user
DB_PASSWORD = your_neon_password
DB_HOST     = your_neon_host.neon.tech
DB_PORT     = 5432
DB_NAME     = neondb
```

---

## 🌆 Cities Tracked

| City | Latitude | Longitude |
|---|---|---|
| Chennai | 13.0827 | 80.2707 |
| Mumbai | 19.0760 | 72.8777 |
| Delhi | 28.6139 | 77.2090 |
| Bangalore | 12.9716 | 77.5946 |
| Kolkata | 22.5726 | 88.3639 |
| Madurai | 9.9252 | 78.1198 |

> Add more cities by editing the `CITIES` list in `weather_pipeline/extract.py`

---

## 💡 What I Learned

- Building a real **ETL pipeline** from scratch (Extract → Transform → Load)
- Calling and parsing **REST APIs** with Python
- **Data cleaning** and enrichment with Pandas
- Designing a **PostgreSQL schema** with upsert logic
- Building a **Flask REST API** with multiple endpoints
- Creating an **interactive dashboard** with Chart.js
- Deploying a **full-stack app** to production for free
- Using **environment variables** to manage secrets safely
- **Scheduling** automated jobs with cron expressions

---

## 🔮 Future Improvements

- [ ] Add historical data beyond 7 days
- [ ] Email/SMS alerts when heavy rain is forecast
- [ ] Compare cities side by side in one chart
- [ ] Add Apache Airflow for professional orchestration
- [ ] Dockerize the entire project
- [ ] Add more Indian cities

---

## 👤 Author

Muthukumar

Ramya

Built as a portfolio project to learn data engineering fundamentals.

---

## 📄 License

MIT License — feel free to fork and build on top of this!
