"""
extract.py
----------
Fetches raw weather data from the Open-Meteo API for multiple cities.
No API key required — completely free!
"""

import requests
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Add or remove cities here ──────────────────────────────────────────
# Find coordinates at: https://www.latlong.net/
CITIES = [
    {"name": "Chennai",   "latitude": 13.0827, "longitude": 80.2707,  "timezone": "Asia/Kolkata"},
    {"name": "Mumbai",    "latitude": 19.0760, "longitude": 72.8777,  "timezone": "Asia/Kolkata"},
    {"name": "Delhi",     "latitude": 28.6139, "longitude": 77.2090,  "timezone": "Asia/Kolkata"},
    {"name": "Bangalore", "latitude": 12.9716, "longitude": 77.5946,  "timezone": "Asia/Kolkata"},
    {"name": "Kolkata",   "latitude": 22.5726, "longitude": 88.3639,  "timezone": "Asia/Kolkata"},
    {"name": "Madurai",   "latitude": 9.9252,  "longitude": 78.1198,  "timezone": "Asia/Kolkata"},
]

# Open-Meteo API endpoint
API_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_weather(city: dict) -> dict:
    """
    Fetch daily weather data for a single city.

    Args:
        city (dict): City config with name, latitude, longitude, timezone

    Returns:
        dict: Raw JSON response from the API
    """
    params = {
        "latitude":     city["latitude"],
        "longitude":    city["longitude"],
        "timezone":     city["timezone"],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
            "relative_humidity_2m_max",
            "relative_humidity_2m_min",
        ],
        "forecast_days": 7
    }

    logger.info(f"Fetching weather for {city['name']}...")

    try:
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info(f"  ✅ {city['name']} — {len(data['daily']['time'])} days fetched.")
        return data

    except requests.exceptions.ConnectionError:
        logger.error(f"  ❌ {city['name']} — Connection failed.")
        raise

    except requests.exceptions.Timeout:
        logger.error(f"  ❌ {city['name']} — Request timed out.")
        raise

    except requests.exceptions.HTTPError as e:
        logger.error(f"  ❌ {city['name']} — API error: {e}")
        raise


def fetch_all_cities(cities: list = CITIES) -> list:
    """
    Fetch weather data for all cities in the list.
    Skips failed cities so one failure doesn't stop the whole pipeline.

    Args:
        cities (list): List of city config dicts

    Returns:
        list: List of (city_config, raw_data) tuples for successful fetches
    """
    results = []
    logger.info(f"Fetching weather for {len(cities)} cities...")

    for i, city in enumerate(cities):
        try:
            raw_data = fetch_weather(city)
            results.append((city, raw_data))

            # Be polite to the API — small delay between requests
            if i < len(cities) - 1:
                time.sleep(0.5)

        except Exception as e:
            logger.warning(f"  ⚠️ Skipping {city['name']} due to error: {e}")
            continue

    logger.info(f"Successfully fetched data for {len(results)}/{len(cities)} cities.")
    return results


# --- Run this file directly to test ---
if __name__ == "__main__":
    results = fetch_all_cities()
    print(f"\n--- Fetched {len(results)} cities ---")
    for city, data in results:
        print(f"  {city['name']:12} → {data['daily']['time'][0]} to {data['daily']['time'][-1]}")