"""
visualize.py
------------
Generates charts and visualizations from the weather database.
Creates 4 charts: Temperature trend, Precipitation, Wind Speed, Dashboard.
"""

import os
import tempfile
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

import matplotlib
matplotlib.use("Agg")

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import logging
from sqlalchemy import text
from load import get_db_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Style settings
plt.rcParams.update({
    "figure.facecolor": "#f8f9fa",
    "axes.facecolor": "#ffffff",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "font.family": "sans-serif",
})


def fetch_data_for_charts(engine, city: str = None) -> pd.DataFrame:
    """
    Fetch weather records from DB for visualization.
    Filters by city (defaulting to the first city in DB) to avoid multi-city collision.

    Args:
        engine: SQLAlchemy engine
        city (str, optional): City name to filter by

    Returns:
        pd.DataFrame: Weather data sorted by date
    """
    with engine.connect() as conn:
        if not city:
            first = conn.execute(text("SELECT city FROM weather ORDER BY date DESC, city ASC LIMIT 1")).fetchone()
            city = first.city if first else None

        if not city:
            return pd.DataFrame()

        df = pd.read_sql(text("SELECT * FROM weather WHERE city = :city ORDER BY date ASC"), conn, params={"city": city})

    df["date"] = pd.to_datetime(df["date"])
    return df


def chart_temperature(df: pd.DataFrame):
    """Line chart: Max, Avg, Min temperature over time."""
    city_name = df["city"].iloc[0] if "city" in df.columns and not df.empty else ""
    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(df["date"], df["temp_max"], label="Max Temp", color="#e74c3c", linewidth=2, marker="o")
    ax.plot(df["date"], df["temp_avg"], label="Avg Temp", color="#f39c12", linewidth=2, marker="s", linestyle="--")
    ax.plot(df["date"], df["temp_min"], label="Min Temp", color="#3498db", linewidth=2, marker="^")
    ax.fill_between(df["date"], df["temp_min"], df["temp_max"], alpha=0.1, color="#e74c3c")

    ax.set_title(f"🌡️  Temperature Trend Over Time — {city_name}", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Temperature (°C)", fontsize=12)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.legend(fontsize=11)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("chart_temperature.png", dpi=150, bbox_inches="tight")
    logger.info("Saved: chart_temperature.png")
    plt.close(fig)


def chart_precipitation(df: pd.DataFrame):
    """Bar chart: Daily precipitation."""
    city_name = df["city"].iloc[0] if "city" in df.columns and not df.empty else ""
    fig, ax = plt.subplots(figsize=(12, 5))

    colors = ["#2980b9" if r else "#aed6f1" for r in df["is_rainy"]]
    bars = ax.bar(df["date"], df["precipitation"], color=colors, edgecolor="white", width=0.6)

    # Add value labels on top of bars
    for bar, val in zip(bars, df["precipitation"]):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                    f"{val:.1f}", ha="center", va="bottom", fontsize=9)

    ax.set_title(f"🌧️  Daily Precipitation (mm) — {city_name}", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Precipitation (mm)", fontsize=12)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

    # Custom legend
    from matplotlib.patches import Patch
    legend = [Patch(color="#2980b9", label="Rainy Day"), Patch(color="#aed6f1", label="Dry Day")]
    ax.legend(handles=legend, fontsize=11)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("chart_precipitation.png", dpi=150, bbox_inches="tight")
    logger.info("Saved: chart_precipitation.png")
    plt.close(fig)


def chart_wind_humidity(df: pd.DataFrame):
    """Dual-axis line chart: Wind speed and humidity over time."""
    city_name = df["city"].iloc[0] if "city" in df.columns and not df.empty else ""
    fig, ax1 = plt.subplots(figsize=(12, 5))

    # Wind speed on left axis
    ax1.plot(df["date"], df["wind_speed_max"], label="Wind Speed (km/h)",
             color="#8e44ad", linewidth=2, marker="o")
    ax1.set_ylabel("Wind Speed (km/h)", color="#8e44ad", fontsize=12)
    ax1.tick_params(axis="y", labelcolor="#8e44ad")

    # Humidity on right axis
    ax2 = ax1.twinx()
    ax2.plot(df["date"], df["humidity_avg"], label="Humidity (%)",
             color="#27ae60", linewidth=2, marker="s", linestyle="--")
    ax2.set_ylabel("Humidity (%)", color="#27ae60", fontsize=12)
    ax2.tick_params(axis="y", labelcolor="#27ae60")

    ax1.set_title(f"💨  Wind Speed & Humidity Over Time — {city_name}", fontsize=16, fontweight="bold", pad=15)
    ax1.set_xlabel("Date", fontsize=12)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=11)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("chart_wind_humidity.png", dpi=150, bbox_inches="tight")
    logger.info("Saved: chart_wind_humidity.png")
    plt.close(fig)


def chart_dashboard(df: pd.DataFrame):
    """Combined 2x2 dashboard with all metrics."""
    city_name = df["city"].iloc[0] if "city" in df.columns and not df.empty else ""
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(f"🌤️  Weather Dashboard — {city_name}",
                 fontsize=20, fontweight="bold", y=1.01)

    # --- Top Left: Temperature ---
    ax = axes[0, 0]
    ax.plot(df["date"], df["temp_max"], color="#e74c3c", label="Max", linewidth=2)
    ax.plot(df["date"], df["temp_avg"], color="#f39c12", label="Avg", linewidth=2, linestyle="--")
    ax.plot(df["date"], df["temp_min"], color="#3498db", label="Min", linewidth=2)
    ax.fill_between(df["date"], df["temp_min"], df["temp_max"], alpha=0.1, color="#e74c3c")
    ax.set_title("🌡️ Temperature (°C)", fontweight="bold")
    ax.legend(fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))

    # --- Top Right: Precipitation ---
    ax = axes[0, 1]
    colors = ["#2980b9" if r else "#aed6f1" for r in df["is_rainy"]]
    ax.bar(df["date"], df["precipitation"], color=colors, edgecolor="white", width=0.6)
    ax.set_title("🌧️ Precipitation (mm)", fontweight="bold")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))

    # --- Bottom Left: Wind Speed ---
    ax = axes[1, 0]
    ax.plot(df["date"], df["wind_speed_max"], color="#8e44ad", linewidth=2, marker="o")
    ax.fill_between(df["date"], 0, df["wind_speed_max"], alpha=0.15, color="#8e44ad")
    ax.set_title("💨 Wind Speed Max (km/h)", fontweight="bold")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))

    # --- Bottom Right: Humidity ---
    ax = axes[1, 1]
    ax.plot(df["date"], df["humidity_avg"], color="#27ae60", linewidth=2, marker="s")
    ax.fill_between(df["date"], 0, df["humidity_avg"], alpha=0.15, color="#27ae60")
    ax.set_title("💧 Avg Humidity (%)", fontweight="bold")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))

    for ax_row in axes:
        for ax in ax_row:
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=30)

    plt.tight_layout()
    plt.savefig("chart_dashboard.png", dpi=150, bbox_inches="tight")
    logger.info("Saved: chart_dashboard.png")
    plt.close(fig)


def visualize(city: str = None):
    """Run all visualizations."""
    engine = get_db_engine()
    df = fetch_data_for_charts(engine, city=city)

    if df.empty:
        logger.warning("No data found in the database. Run the pipeline first!")
        return

    logger.info(f"Generating charts for {df['city'].iloc[0]} ({len(df)} records)...")
    chart_temperature(df)
    chart_precipitation(df)
    chart_wind_humidity(df)
    chart_dashboard(df)
    logger.info("All charts generated successfully! ✅")


# --- Run this file directly to generate all charts ---
if __name__ == "__main__":
    visualize()
