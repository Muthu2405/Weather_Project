"""
extract.py
----------
Fetches raw weather data from the Open-Meteo API.
No API key required — completely free!
"""

import requests
import logging

# Set up logging so we can see what's happening
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# --- City Configuration ---
# Chennai, India (change latitude/longitude for your city)
# Find your city coordinates at: https://www.latlong.net/
CITY_CONFIG = {
    "name": "Chennai",
    "latitude": 13.0827,
    "longitude": 80.2707,
    "timezone": "Asia/Kolkata"
}

# Open-Meteo API endpoint
API_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_weather(city: dict = CITY_CONFIG) -> dict:
    """
    Fetch daily weather data for the given city.

    Args:
        city (dict): City config with name, latitude, longitude, timezone

    Returns:
        dict: Raw JSON response from the API
    """
    params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "timezone": city["timezone"],
        "daily": [
            "temperature_2m_max",          # Max temperature (°C)
            "temperature_2m_min",          # Min temperature (°C)
            "precipitation_sum",           # Total rainfall (mm)
            "wind_speed_10m_max",          # Max wind speed (km/h)
            "relative_humidity_2m_max",    # Max humidity (%)
            "relative_humidity_2m_min",    # Min humidity (%)
        ],
        "forecast_days": 7              # Fetch next 7 days
    }

    logger.info(f"Fetching weather data for {city['name']}...")

    try:
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()  # Raise error if status is not 200

        data = response.json()
        logger.info(f"Successfully fetched {len(data['daily']['time'])} days of weather data.")
        return data

    except requests.exceptions.ConnectionError:
        logger.error("Connection failed. Check your internet connection.")
        raise

    except requests.exceptions.Timeout:
        logger.error("Request timed out. Try again later.")
        raise

    except requests.exceptions.HTTPError as e:
        logger.error(f"API returned an error: {e}")
        raise


# --- Run this file directly to test the extract step ---
if __name__ == "__main__":
    raw_data = fetch_weather()
    print("\n--- Raw API Response (sample) ---")
    print(f"City     : {CITY_CONFIG['name']}")
    print(f"Dates    : {raw_data['daily']['time']}")
    print(f"Max Temps: {raw_data['daily']['temperature_2m_max']}")
    print(f"Rain(mm) : {raw_data['daily']['precipitation_sum']}")