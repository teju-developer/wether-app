"""
SkyPulse Weather Dashboard - Main Entry Point.
Launches the modern CustomTkinter weather station dashboard or runs in CLI mode.
"""

import sys
import os
import tempfile
import argparse
from pathlib import Path

# Set writable temp directory for Matplotlib cache
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.weather_service import WeatherService
from app.ui import WeatherDashboardApp


def parse_args():
    parser = argparse.ArgumentParser(description="SkyPulse Smart Weather Dashboard")
    parser.add_argument("--cli", "-c", nargs="?", const="Hubballi", help="Run in CLI mode for a specified city")
    parser.add_argument("--units", "-u", choices=["metric", "imperial"], default="metric", help="Temperature units")
    return parser.parse_args()


def run_cli(city: str, units: str = "metric"):
    print(f"\n==========================================")
    print(f"  SkyPulse Weather Terminal Edition       ")
    print(f"==========================================")
    service = WeatherService()
    try:
        w_data, f_data = service.get_complete_weather(city, units=units)
        unit_sym = "°F" if units == "imperial" else "°C"
        spd_unit = "mph" if units == "imperial" else "km/h"

        print(f"\nWeather for {w_data.city}, {w_data.country}:")
        print(f"  Condition   : {w_data.condition} ({w_data.description})")
        print(f"  Temperature : {w_data.temperature:g}{unit_sym} (Feels like {w_data.feels_like:g}{unit_sym})")
        print(f"  Range       : High {w_data.temp_max:g}{unit_sym} / Low {w_data.temp_min:g}{unit_sym}")
        print(f"  Humidity    : {w_data.humidity}%")
        print(f"  Wind        : {w_data.wind_speed:g} {spd_unit} ({w_data.wind_direction_cardinal})")
        print(f"  Pressure    : {w_data.pressure} hPa")
        if w_data.uv_index is not None:
            print(f"  UV Index    : {w_data.uv_index} ({w_data.uv_category})")
        if w_data.aqi is not None:
            print(f"  Air Quality : {w_data.aqi_category} (AQI {w_data.aqi})")
        print(f"  Sun         : Rise {w_data.sunrise} | Set {w_data.sunset}")
        print(f"  Provider    : {w_data.provider}")
        print(f"  Updated     : {w_data.last_updated}\n")

        print("24-Hour Forecast Highlights:")
        for item in f_data.hourly[:5]:
            print(f"  {item.time_label:<8} : {item.temperature:g}{unit_sym} | {item.condition:<15} | Rain: {item.rain_probability or 0}%")

        print("\n7-Day Outlook:")
        for day in f_data.daily[:5]:
            print(f"  {day.day_name:<12} : {day.temp_max:g}° / {day.temp_min:g}° | {day.condition:<16} | Rain: {day.rain_probability or 0}%")
        print()

    except Exception as e:
        print(f"\n[Error] {e}\n")


def main():
    args = parse_args()

    if args.cli is not None:
        run_cli(args.cli, units=args.units)
    else:
        # Launch modern CustomTkinter Dashboard
        app = WeatherDashboardApp()
        app.mainloop()


if __name__ == "__main__":
    main()
