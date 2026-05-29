"""
app.py
------
Flask web server that serves the weather dashboard.
Exposes REST API endpoints for the frontend to fetch live data.
"""

from flask import Flask, jsonify, render_template
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)


def get_engine():
    db_user     = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "password")
    db_host     = os.getenv("DB_HOST", "localhost")
    db_port     = os.getenv("DB_PORT", "5432")
    db_name     = os.getenv("DB_NAME", "weather_db")
    url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return create_engine(url)


# ── Routes ──────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main dashboard page."""
    return render_template("index.html")


@app.route("/api/latest")
def api_latest():
    """Return today's (most recent) weather record."""
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT date, city, temp_max, temp_min, temp_avg,
                   precipitation, wind_speed_max, humidity_avg,
                   is_rainy, condition
            FROM weather
            ORDER BY date DESC
            LIMIT 1
        """)).fetchone()
    if not row:
        return jsonify({"error": "No data found"}), 404
    return jsonify({
        "date":          str(row.date),
        "city":          row.city,
        "temp_max":      row.temp_max,
        "temp_min":      row.temp_min,
        "temp_avg":      row.temp_avg,
        "precipitation": row.precipitation,
        "wind_speed":    row.wind_speed_max,
        "humidity":      row.humidity_avg,
        "is_rainy":      row.is_rainy,
        "condition":     row.condition,
    })


@app.route("/api/forecast")
def api_forecast():
    """Return all weather records (7-day forecast/history)."""
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT date, temp_max, temp_min, temp_avg,
                   precipitation, wind_speed_max, humidity_avg,
                   is_rainy, condition
            FROM weather
            ORDER BY date ASC
        """)).fetchall()
    return jsonify([{
        "date":          str(r.date),
        "temp_max":      r.temp_max,
        "temp_min":      r.temp_min,
        "temp_avg":      r.temp_avg,
        "precipitation": r.precipitation,
        "wind_speed":    r.wind_speed_max,
        "humidity":      r.humidity_avg,
        "is_rainy":      r.is_rainy,
        "condition":     r.condition,
    } for r in rows])


@app.route("/api/stats")
def api_stats():
    """Return aggregate stats for the stats cards."""
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT
                MAX(temp_max)                                        AS highest_temp,
                MIN(temp_min)                                        AS lowest_temp,
                MAX(precipitation)                                   AS max_rain,
                MAX(wind_speed_max)                                  AS max_wind,
                ROUND(AVG(humidity_avg)::numeric, 1)                 AS avg_humidity,
                COUNT(*) FILTER (WHERE is_rainy)                     AS rainy_days,
                COUNT(*)                                             AS total_days
            FROM weather
        """)).fetchone()
    return jsonify({
        "highest_temp": row.highest_temp,
        "lowest_temp":  row.lowest_temp,
        "max_rain":     row.max_rain,
        "max_wind":     row.max_wind,
        "avg_humidity": float(row.avg_humidity),
        "rainy_days":   row.rainy_days,
        "total_days":   row.total_days,
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
