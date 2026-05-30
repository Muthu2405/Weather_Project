"""
load.py
-------
Loads the cleaned DataFrame into PostgreSQL database.
Handles duplicate prevention using upsert logic.
"""

import pandas as pd
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def get_db_engine():
    """
    Create and return a SQLAlchemy database engine using .env credentials.

    Returns:
        sqlalchemy.Engine: Database engine connected to PostgreSQL
    """
    db_user     = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "password")
    db_host     = os.getenv("DB_HOST", "localhost")
    db_port     = int(os.getenv("DB_PORT") or "5432")
    db_name     = os.getenv("DB_NAME", "weather_db")

    # Use SSL for cloud databases like Neon
    is_cloud = "neon.tech" in db_host or "amazonaws" in db_host
    connection_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    if is_cloud:
        connection_url += "?sslmode=require"

    try:
        engine = create_engine(connection_url)
        logger.info("Database engine created successfully.")
        return engine
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise


def create_table_if_not_exists(engine):
    """
    Create the weather table if it doesn't already exist.
    The UNIQUE constraint on (date, city) prevents duplicate records.

    Args:
        engine: SQLAlchemy database engine
    """
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS weather (
            id              SERIAL PRIMARY KEY,
            date            DATE          NOT NULL,
            city            TEXT          NOT NULL,
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
            UNIQUE (date, city)          -- Prevents duplicate entries
        );
    """
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()
    logger.info("Table 'weather' is ready.")


def load_weather(df: pd.DataFrame, engine) -> int:
    """
    Load cleaned weather DataFrame into PostgreSQL.
    Uses upsert to avoid inserting duplicate records.

    Args:
        df (pd.DataFrame): Cleaned weather data
        engine: SQLAlchemy database engine

    Returns:
        int: Number of rows successfully inserted/updated
    """
    logger.info(f"Loading {len(df)} rows into PostgreSQL...")

    rows_affected = 0

    with engine.connect() as conn:
        for _, row in df.iterrows():
            upsert_sql = text("""
                INSERT INTO weather (
                    date, city, temp_max, temp_min, temp_avg,
                    temp_range, precipitation, wind_speed_max,
                    humidity_avg, is_rainy, condition, loaded_at
                )
                VALUES (
                    :date, :city, :temp_max, :temp_min, :temp_avg,
                    :temp_range, :precipitation, :wind_speed_max,
                    :humidity_avg, :is_rainy, :condition, :loaded_at
                )
                ON CONFLICT (date, city)
                DO UPDATE SET
                    temp_max       = EXCLUDED.temp_max,
                    temp_min       = EXCLUDED.temp_min,
                    temp_avg       = EXCLUDED.temp_avg,
                    temp_range     = EXCLUDED.temp_range,
                    precipitation  = EXCLUDED.precipitation,
                    wind_speed_max = EXCLUDED.wind_speed_max,
                    humidity_avg   = EXCLUDED.humidity_avg,
                    is_rainy       = EXCLUDED.is_rainy,
                    condition      = EXCLUDED.condition,
                    loaded_at      = EXCLUDED.loaded_at;
            """)

            conn.execute(upsert_sql, {
                "date":           row["date"].date(),
                "city":           row["city"],
                "temp_max":       row["temp_max"],
                "temp_min":       row["temp_min"],
                "temp_avg":       row["temp_avg"],
                "temp_range":     row["temp_range"],
                "precipitation":  row["precipitation"],
                "wind_speed_max": row["wind_speed_max"],
                "humidity_avg":   row["humidity_avg"],
                "is_rainy":       bool(row["is_rainy"]),
                "condition":      row["condition"],
                "loaded_at":      row["loaded_at"],
            })
            rows_affected += 1

        conn.commit()

    logger.info(f"Successfully loaded {rows_affected} rows into the database.")
    return rows_affected


# --- Run this file directly to test the load step ---
if __name__ == "__main__":
    from extract import fetch_weather, CITY_CONFIG
    from transform import transform_weather

    raw_data = fetch_weather(CITY_CONFIG)
    df = transform_weather(raw_data, CITY_CONFIG["name"])

    engine = get_db_engine()
    create_table_if_not_exists(engine)
    rows = load_weather(df, engine)
    print(f"\n✅ {rows} rows loaded into PostgreSQL successfully!")