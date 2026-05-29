"""
analyze.py
----------
Runs analytical SQL queries against the weather database.
Answers real questions from the stored data.
"""

import pandas as pd
import logging
from sqlalchemy import text
from load import get_db_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_query(engine, sql: str, description: str) -> pd.DataFrame:
    """
    Execute a SQL query and return results as a DataFrame.

    Args:
        engine: SQLAlchemy engine
        sql (str): SQL query to run
        description (str): Human-readable description of the query

    Returns:
        pd.DataFrame: Query results
    """
    logger.info(f"Running query: {description}")
    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn)
    return df


def analyze(engine):
    """
    Run all analytical queries and print results.

    Args:
        engine: SQLAlchemy database engine
    """

    print("\n" + "="*60)
    print("        🌤️  WEATHER DATA INSIGHTS")
    print("="*60)

    # --- Query 1: Hottest Day ---
    q1 = """
        SELECT date, city, temp_max, condition
        FROM weather
        ORDER BY temp_max DESC
        LIMIT 5;
    """
    df1 = run_query(engine, q1, "Top 5 Hottest Days")
    print("\n🌡️  Top 5 Hottest Days:")
    print(df1.to_string(index=False))

    # --- Query 2: Coldest Day ---
    q2 = """
        SELECT date, city, temp_min, condition
        FROM weather
        ORDER BY temp_min ASC
        LIMIT 5;
    """
    df2 = run_query(engine, q2, "Top 5 Coldest Days")
    print("\n🥶 Top 5 Coldest Days:")
    print(df2.to_string(index=False))

    # --- Query 3: Rainy Days Summary ---
    q3 = """
        SELECT
            city,
            COUNT(*) FILTER (WHERE is_rainy = TRUE) AS rainy_days,
            COUNT(*) AS total_days,
            ROUND(AVG(precipitation)::numeric, 2) AS avg_precipitation_mm
        FROM weather
        GROUP BY city;
    """
    df3 = run_query(engine, q3, "Rainy Days Summary")
    print("\n🌧️  Rainy Days Summary:")
    print(df3.to_string(index=False))

    # --- Query 4: Average Stats Per City ---
    q4 = """
        SELECT
            city,
            ROUND(AVG(temp_avg)::numeric, 2)       AS avg_temperature,
            ROUND(AVG(wind_speed_max)::numeric, 2) AS avg_wind_speed,
            ROUND(AVG(humidity_avg)::numeric, 2)   AS avg_humidity
        FROM weather
        GROUP BY city;
    """
    df4 = run_query(engine, q4, "Average Stats Per City")
    print("\n📊 Overall Weather Averages:")
    print(df4.to_string(index=False))

    # --- Query 5: Weather Condition Breakdown ---
    q5 = """
        SELECT
            condition,
            COUNT(*) AS days
        FROM weather
        GROUP BY condition
        ORDER BY days DESC;
    """
    df5 = run_query(engine, q5, "Weather Condition Breakdown")
    print("\n🏷️  Weather Condition Breakdown:")
    print(df5.to_string(index=False))

    # --- Query 6: All-Time Records ---
    q6 = """
        SELECT
            MAX(temp_max)       AS highest_temp,
            MIN(temp_min)       AS lowest_temp,
            MAX(precipitation)  AS max_rain_mm,
            MAX(wind_speed_max) AS max_wind_kmh
        FROM weather;
    """
    df6 = run_query(engine, q6, "All-Time Records")
    print("\n🏆 All-Time Records:")
    print(df6.to_string(index=False))

    print("\n" + "="*60 + "\n")


# --- Run this file directly to see insights ---
if __name__ == "__main__":
    engine = get_db_engine()
    analyze(engine)
