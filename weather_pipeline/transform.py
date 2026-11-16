"""
transform.py
------------
Cleans and enriches the raw weather data from extract.py.
Converts raw JSON into a clean Pandas DataFrame ready for loading.
"""

import pandas as pd
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def transform_weather(raw_data: dict, city_name: str) -> pd.DataFrame:
    """
    Transform raw API JSON into a clean, enriched DataFrame.

    Args:
        raw_data (dict): Raw JSON response from Open-Meteo API
        city_name (str): Name of the city

    Returns:
        pd.DataFrame: Cleaned and enriched weather DataFrame
    """
    logger.info("Transforming raw weather data...")

    daily = raw_data.get("daily", {})

    # --- Step 1: Build base DataFrame from raw data ---
    df = pd.DataFrame({
        "date":          daily.get("time", []),
        "temp_max":      daily.get("temperature_2m_max", []),
        "temp_min":      daily.get("temperature_2m_min", []),
        "precipitation": daily.get("precipitation_sum", []),
        "wind_speed_max": daily.get("wind_speed_10m_max", []),
        "humidity_max":  daily.get("relative_humidity_2m_max", []),
        "humidity_min":  daily.get("relative_humidity_2m_min", []),
    })

    # --- Step 2: Set correct data types ---
    df["date"] = pd.to_datetime(df["date"])
    df["temp_max"] = pd.to_numeric(df["temp_max"], errors="coerce")
    df["temp_min"] = pd.to_numeric(df["temp_min"], errors="coerce")
    df["precipitation"] = pd.to_numeric(df["precipitation"], errors="coerce")
    df["wind_speed_max"] = pd.to_numeric(df["wind_speed_max"], errors="coerce")
    df["humidity_max"] = pd.to_numeric(df["humidity_max"], errors="coerce")
    df["humidity_min"] = pd.to_numeric(df["humidity_min"], errors="coerce")

    # --- Step 3: Handle missing values ---
    # Fill missing numerical values with 0 (safe for precipitation, wind)
    df["precipitation"] = df["precipitation"].fillna(0)

    # Drop rows where critical fields (temp) are missing
    before = len(df)
    df.dropna(subset=["temp_max", "temp_min"], inplace=True)
    after = len(df)
    if before != after:
        logger.warning(f"Dropped {before - after} rows due to missing temperature data.")

    # --- Step 4: Derive new useful columns ---
    df["temp_avg"]     = ((df["temp_max"] + df["temp_min"]) / 2).round(2)
    df["temp_range"]   = (df["temp_max"] - df["temp_min"]).round(2)  # Daily temp swing
    df["humidity_avg"] = ((df["humidity_max"] + df["humidity_min"]) / 2).round(2)
    df["is_rainy"]     = df["precipitation"] > 1.0  # Rainy if more than 1mm rain

    # Add weather condition label
    df["condition"] = df.apply(classify_condition, axis=1)

    # --- Step 5: Add metadata columns ---
    df["city"]      = city_name
    df["loaded_at"] = datetime.now(timezone.utc)

    # --- Step 6: Select and reorder final columns ---
    df = df[[
        "date", "city", "temp_max", "temp_min", "temp_avg",
        "temp_range", "precipitation", "wind_speed_max",
        "humidity_avg", "is_rainy", "condition", "loaded_at"
    ]]

    logger.info(f"Transformation complete. {len(df)} rows ready for loading.")
    return df


def classify_condition(row) -> str:
    """
    Classify weather condition based on metrics.

    Args:
        row: A single row from the DataFrame

    Returns:
        str: Weather condition label
    """
    if row["precipitation"] > 10:
        return "Heavy Rain"
    elif row["precipitation"] > 1:
        return "Light Rain"
    elif row["temp_max"] > 38:
        return "Very Hot"
    elif row["temp_max"] > 30:
        return "Hot"
    elif row["wind_speed_max"] > 40:
        return "Windy"
    else:
        return "Clear"


# --- Run this file directly to test the transform step ---
if __name__ == "__main__":
    from extract import fetch_weather, CITIES

    city = CITIES[0]
    raw_data = fetch_weather(city)
    df = transform_weather(raw_data, city["name"])

    print("\n--- Transformed DataFrame ---")
    print(df.to_string(index=False))
    print(f"\nShape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"\nData types:\n{df.dtypes}")