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
    db_port     = int(os.getenv("DB_PORT") or "5432")
    db_name     = os.getenv("DB_NAME", "weather_db")
    logger.info(f"Connecting → {db_user}@{db_host}:{db_port}/{db_name}")
    url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return create_engine(url)


# ── Global error handler — always return JSON, never HTML ──
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled error: {e}", exc_info=True)
    return jsonify({"error": str(e)}), 500


# ── Routes ──────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/debug")
def api_debug():
    """Diagnostic endpoint — shows what .env values are loaded."""
    return jsonify({
        "DB_USER":  os.getenv("DB_USER", "NOT SET"),
        "DB_HOST":  os.getenv("DB_HOST", "NOT SET"),
        "DB_PORT":  os.getenv("DB_PORT", "NOT SET"),
        "DB_NAME":  os.getenv("DB_NAME", "NOT SET"),
        "DB_PASSWORD": "SET" if os.getenv("DB_PASSWORD") else "NOT SET",
    })


@app.route("/api/latest")
def api_latest():
    try:
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
            return jsonify({"error": "No data found — run pipeline.py first"}), 404
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
    except Exception as e:
        logger.error(f"/api/latest error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/forecast")
def api_forecast():
    try:
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
    except Exception as e:
        logger.error(f"/api/forecast error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats")
def api_stats():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT
                    MAX(temp_max)                                    AS highest_temp,
                    MIN(temp_min)                                    AS lowest_temp,
                    MAX(precipitation)                               AS max_rain,
                    MAX(wind_speed_max)                              AS max_wind,
                    ROUND(AVG(humidity_avg)::numeric, 1)             AS avg_humidity,
                    COUNT(*) FILTER (WHERE is_rainy)                 AS rainy_days,
                    COUNT(*)                                         AS total_days
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
    except Exception as e:
        logger.error(f"/api/stats error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)