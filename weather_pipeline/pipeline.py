"""
pipeline.py
-----------
Main orchestrator: runs the full ETL pipeline (Extract → Transform → Load).
Also handles daily scheduling at a fixed time.

Usage:
    python pipeline.py          # Run once immediately
    python pipeline.py --schedule  # Run daily at 08:00 AM
"""

import logging
import argparse
import schedule
import time
from datetime import datetime, timezone

from extract import fetch_weather, CITY_CONFIG
from transform import transform_weather
from load import get_db_engine, create_table_if_not_exists, load_weather
from analyze import analyze
from visualize import visualize

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),                # Print to terminal
        logging.FileHandler("pipeline.log"),    # Also write to log file
    ]
)
logger = logging.getLogger(__name__)


def run_pipeline():
    """
    Execute the full ETL pipeline:
    1. Extract: Fetch raw weather data from API
    2. Transform: Clean and enrich the data
    3. Load: Insert into PostgreSQL
    4. Analyze: Print SQL insights
    5. Visualize: Generate charts
    """
    start_time = datetime.now(timezone.utc)
    logger.info("="*50)
    logger.info("🚀 Starting Weather Data Pipeline...")
    logger.info("="*50)

    try:
        # --- Step 1: EXTRACT ---
        logger.info("STEP 1/5: Extract — Fetching weather data from API...")
        raw_data = fetch_weather(CITY_CONFIG)
        logger.info("✅ Extract complete.")

        # --- Step 2: TRANSFORM ---
        logger.info("STEP 2/5: Transform — Cleaning and enriching data...")
        df = transform_weather(raw_data, CITY_CONFIG["name"])
        logger.info(f"✅ Transform complete. {len(df)} rows ready.")

        # --- Step 3: LOAD ---
        logger.info("STEP 3/5: Load — Inserting data into PostgreSQL...")
        engine = get_db_engine()
        create_table_if_not_exists(engine)
        rows_loaded = load_weather(df, engine)
        logger.info(f"✅ Load complete. {rows_loaded} rows inserted/updated.")

        # --- Step 4: ANALYZE ---
        logger.info("STEP 4/5: Analyze — Running SQL insights...")
        analyze(engine)
        logger.info("✅ Analysis complete.")

        # --- Step 5: VISUALIZE ---
        logger.info("STEP 5/5: Visualize — Generating charts...")
        visualize()
        logger.info("✅ Visualization complete.")

        # --- Summary ---
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info("="*50)
        logger.info(f"🎉 Pipeline completed successfully in {duration:.1f} seconds!")
        logger.info("="*50)

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        logger.error("Check the error above and fix before re-running.")
        raise


def run_scheduled(run_time: str = "08:00"):
    """
    Schedule the pipeline to run daily at the specified time.

    Args:
        run_time (str): Time in "HH:MM" format (default: "08:00")
    """
    logger.info(f"⏰ Scheduling pipeline to run daily at {run_time}...")

    # Run once immediately on startup
    run_pipeline()

    # Then schedule for every day at the given time
    schedule.every().day.at(run_time).do(run_pipeline)

    logger.info(f"✅ Scheduler running. Next run at {run_time} daily. Press Ctrl+C to stop.")

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


# --- Entry Point ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weather Data Pipeline")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run pipeline on a daily schedule (default: run once)"
    )
    parser.add_argument(
        "--time",
        default="08:00",
        help="Time to run the daily schedule in HH:MM format (default: 08:00)"
    )
    args = parser.parse_args()

    if args.schedule:
        run_scheduled(args.time)
    else:
        run_pipeline()