# 🌤️ Weather Data Pipeline

A beginner-friendly ETL pipeline that fetches daily weather data for Chennai, stores it in PostgreSQL, and generates SQL insights + visualizations.

---

## 📁 Project Structure

```
weather_pipeline/
├── extract.py        # Fetch weather data from Open-Meteo API
├── transform.py      # Clean and enrich raw data
├── load.py           # Insert data into PostgreSQL
├── analyze.py        # SQL insight queries
├── visualize.py      # Generate charts
├── pipeline.py       # Full ETL orchestrator + scheduler
├── .env              # Your DB credentials (not committed to Git)
├── .env.example      # Template for .env
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

---

## ⚙️ Setup Instructions

### 1. Clone the project
```bash
git clone https://github.com/yourusername/weather_pipeline.git
cd weather_pipeline
```

### 2. Create and activate virtual environment
```bash
python -m venv weather_env
source weather_env/bin/activate      # Mac/Linux
weather_env\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up PostgreSQL
```sql
CREATE DATABASE weather_db;
```

### 5. Configure environment variables
```bash
cp .env.example .env
# Open .env and fill in your PostgreSQL credentials
```

---

## 🚀 Running the Pipeline

### Run once (manually)
```bash
python pipeline.py
```

### Run on daily schedule (8:00 AM)
```bash
python pipeline.py --schedule
```

### Run at a custom time
```bash
python pipeline.py --schedule --time 07:30
```

### Test individual steps
```bash
python extract.py      # Test API fetch
python transform.py    # Test data cleaning
python load.py         # Test DB insert
python analyze.py      # Run SQL insights
python visualize.py    # Generate charts
```

---

## 📊 What It Does

| Step | File | Description |
|------|------|-------------|
| Extract | `extract.py` | Calls Open-Meteo API for 7-day weather |
| Transform | `transform.py` | Cleans data, adds derived columns |
| Load | `load.py` | Upserts into PostgreSQL (no duplicates) |
| Analyze | `analyze.py` | Runs 6 SQL insight queries |
| Visualize | `visualize.py` | Generates 4 charts |

---

## 🗄️ Database Schema

```sql
CREATE TABLE weather (
    id              SERIAL PRIMARY KEY,
    date            DATE,
    city            TEXT,
    temp_max        FLOAT,
    temp_min        FLOAT,
    temp_avg        FLOAT,
    temp_range      FLOAT,
    precipitation   FLOAT,
    wind_speed_max  FLOAT,
    humidity_avg    FLOAT,
    is_rainy        BOOLEAN,
    condition       TEXT,
    loaded_at       TIMESTAMP,
    UNIQUE (date, city)
);
```

---

## 📈 Charts Generated

- 🌡️ Temperature trend (Max / Avg / Min)
- 🌧️ Daily precipitation bar chart
- 💨 Wind speed & humidity dual-axis chart
- 📊 Full weather dashboard (2×2 grid)

---

## 🛠️ Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.10+ |
| API | Open-Meteo (free, no key needed) |
| Data Processing | Pandas |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Scheduling | schedule |
| Charts | Matplotlib |

---

## 👤 Author

Built as a beginner data engineering portfolio project.
