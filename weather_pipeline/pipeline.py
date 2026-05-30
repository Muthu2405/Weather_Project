"""
pipeline.py
-----------
Main orchestrator: runs the full ETL pipeline for ALL cities.
Extract → Transform → Load → Analyze → Visualize

Usage:
    python pipeline.py             # Run once immediately
    python pipeline.py --schedule  # Run daily at 08:00 AM
"""

import logging
import argparse
import schedule
import time
from datetime import datetime, timezone

from extract import fetch_all_cities, CITIES
from transform import transform_weather
from load import get_db_engine, create_table_if_not_exists, load_weather
from analyze import analyze
from visualize import visualize

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pipeline.log"),
    ]
)
logger = logging.getLogger(__name__)


def run_pipeline():
    """
    Execute the full ETL pipeline for all cities:
    1. Extract: Fetch data for all cities
    2. Transform + Load: Clean and insert each city
    3. Analyze: Print SQL insights
    4. Visualize: Generate charts
    """
    start_time = datetime.now(timezone.utc)
    logger.info("=" * 55)
    logger.info(f"🚀 Starting Weather Pipeline for {len(CITIES)} cities...")
    logger.info("=" * 55)

    try:
        # ── Step 1: EXTRACT all cities ──
        logger.info(f"STEP 1: Extract — Fetching data for {len(CITIES)} cities...")
        city_results = fetch_all_cities(CITIES)

        if not city_results:
            raise RuntimeError("No city data was fetched. Check your internet connection.")

        logger.info(f"✅ Extract complete — {len(city_results)} cities fetched.")

        # ── Step 2 + 3: TRANSFORM & LOAD each city ──
        logger.info("STEP 2/3: Transform & Load — Processing each city...")
        engine = get_db_engine()
        create_table_if_not_exists(engine)

        total_rows = 0
        failed_cities = []

        for city, raw_data in city_results:
            try:
                # Transform
                df = transform_weather(raw_data, city["name"])

                # Load
                rows = load_weather(df, engine)
                total_rows += rows
                logger.info(f"  ✅ {city['name']:12} → {rows} rows loaded.")

            except Exception as e:
                logger.error(f"  ❌ {city['name']} failed: {e}")
                failed_cities.append(city["name"])
                continue

        logger.info(f"✅ Load complete — {total_rows} rows total. "
                    f"({len(failed_cities)} cities failed: {failed_cities if failed_cities else 'none'})")

        # ── Step 4: ANALYZE ──
        logger.info("STEP 4: Analyze — Running SQL insights...")
        analyze(engine)
        logger.info("✅ Analysis complete.")

        # ── Step 5: VISUALIZE ──
        logger.info("STEP 5: Visualize — Generating charts...")
        visualize()
        logger.info("✅ Visualization complete.")

        # ── Summary ──
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info("=" * 55)
        logger.info(f"🎉 Pipeline done in {duration:.1f}s — "
                    f"{len(city_results)} cities, {total_rows} rows!")
        logger.info("=" * 55)

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        raise


def run_scheduled(run_time: str = "08:00"):
    """Schedule pipeline to run daily at the given time."""
    logger.info(f"⏰ Scheduling pipeline daily at {run_time}...")
    run_pipeline()
    schedule.every().day.at(run_time).do(run_pipeline)
    logger.info(f"Scheduler active. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(60)


# ── Entry Point ──
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weather Data Pipeline — Multi City")
    parser.add_argument("--schedule", action="store_true", help="Run on daily schedule")
    parser.add_argument("--time", default="08:00", help="Schedule time HH:MM (default: 08:00)")
    args = parser.parse_args()

    if args.schedule:
        run_scheduled(args.time)
    else:
        run_pipeline()