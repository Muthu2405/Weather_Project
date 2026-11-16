"""
app.py
------
Flask web server with city selector support.
All API endpoints accept an optional ?city= query parameter.
"""

from flask import Flask, jsonify, render_template, request
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
    is_cloud = "neon.tech" in db_host or "amazonaws" in db_host
    url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    if is_cloud:
        url += "?sslmode=require"
    return create_engine(url)


@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled error: {e}", exc_info=True)
    return jsonify({"error": str(e)}), 500


# ── Routes ──────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/cities")
def api_cities():
    """Return list of all available cities in the database."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT DISTINCT city
                FROM weather
                ORDER BY city ASC
            """)).fetchall()
        return jsonify([r.city for r in rows])
    except Exception as e:
        logger.error(f"/api/cities error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/latest")
def api_latest():
    """Return most recent weather record. Filter by ?city=Chennai"""
    try:
        city = request.args.get("city", None)
        engine = get_engine()
        with engine.connect() as conn:
            if city:
                row = conn.execute(text("""
                    SELECT date, city, temp_max, temp_min, temp_avg,
                           precipitation, wind_speed_max, humidity_avg,
                           is_rainy, condition
                    FROM weather
                    WHERE city = :city
                    ORDER BY date DESC LIMIT 1
                """), {"city": city}).fetchone()
            else:
                row = conn.execute(text("""
                    SELECT date, city, temp_max, temp_min, temp_avg,
                           precipitation, wind_speed_max, humidity_avg,
                           is_rainy, condition
                    FROM weather
                    ORDER BY date DESC LIMIT 1
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
    """Return 7-day forecast. Filter by ?city=Chennai"""
    try:
        city = request.args.get("city", None)
        engine = get_engine()
        with engine.connect() as conn:
            if not city:
                first_city = conn.execute(text("SELECT city FROM weather ORDER BY date DESC, city ASC LIMIT 1")).fetchone()
                city = first_city.city if first_city else None

            if not city:
                return jsonify([])

            rows = conn.execute(text("""
                SELECT * FROM (
                    SELECT date, temp_max, temp_min, temp_avg,
                           precipitation, wind_speed_max, humidity_avg,
                           is_rainy, condition
                    FROM weather
                    WHERE city = :city
                    ORDER BY date DESC
                    LIMIT 7
                ) sub
                ORDER BY date ASC
            """), {"city": city}).fetchall()

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
    """Return aggregate stats. Filter by ?city=Chennai"""
    try:
        city = request.args.get("city", None)
        engine = get_engine()
        with engine.connect() as conn:
            if city:
                row = conn.execute(text("""
                    SELECT
                        MAX(temp_max)                                AS highest_temp,
                        MIN(temp_min)                                AS lowest_temp,
                        MAX(precipitation)                           AS max_rain,
                        MAX(wind_speed_max)                          AS max_wind,
                        ROUND(AVG(humidity_avg)::numeric, 1)         AS avg_humidity,
                        COUNT(*) FILTER (WHERE is_rainy)             AS rainy_days,
                        COUNT(*)                                     AS total_days
                    FROM weather
                    WHERE city = :city
                """), {"city": city}).fetchone()
            else:
                row = conn.execute(text("""
                    SELECT
                        MAX(temp_max)                                AS highest_temp,
                        MIN(temp_min)                                AS lowest_temp,
                        MAX(precipitation)                           AS max_rain,
                        MAX(wind_speed_max)                          AS max_wind,
                        ROUND(AVG(humidity_avg)::numeric, 1)         AS avg_humidity,
                        COUNT(*) FILTER (WHERE is_rainy)             AS rainy_days,
                        COUNT(*)                                     AS total_days
                    FROM weather
                """)).fetchone()

        avg_hum = float(row.avg_humidity) if (row and row.avg_humidity is not None) else 0.0
        rainy = row.rainy_days if (row and row.rainy_days is not None) else 0
        total = row.total_days if (row and row.total_days is not None) else 0

        return jsonify({
            "highest_temp": row.highest_temp if row else None,
            "lowest_temp":  row.lowest_temp if row else None,
            "max_rain":     row.max_rain if row else None,
            "max_wind":     row.max_wind if row else None,
            "avg_humidity": avg_hum,
            "rainy_days":   rainy,
            "total_days":   total,
        })
    except Exception as e:
        logger.error(f"/api/stats error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/debug")
def api_debug():
    return jsonify({
        "DB_USER":  os.getenv("DB_USER", "NOT SET"),
        "DB_HOST":  os.getenv("DB_HOST", "NOT SET"),
        "DB_PORT":  os.getenv("DB_PORT", "NOT SET"),
        "DB_NAME":  os.getenv("DB_NAME", "NOT SET"),
        "DB_PASSWORD": "SET" if os.getenv("DB_PASSWORD") else "NOT SET",
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)