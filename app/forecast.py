"""
Forecast Utilities Module for SkyPulse Weather Dashboard.
Provides unit conversions, WMO/OWM icon mapping, AQI/UV evaluations, and date formatting.
"""

from datetime import datetime, timezone, timedelta
from typing import Tuple, Dict, Any


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return round((celsius * 9 / 5) + 32, 1)


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius."""
    return round((fahrenheit - 32) * 5 / 9, 1)


def convert_temp(temp: float, from_unit: str, to_unit: str) -> float:
    """Convert temperature between metric (°C) and imperial (°F)."""
    if from_unit == to_unit:
        return round(temp, 1)
    if from_unit == "metric" and to_unit == "imperial":
        return celsius_to_fahrenheit(temp)
    if from_unit == "imperial" and to_unit == "metric":
        return fahrenheit_to_celsius(temp)
    return round(temp, 1)


def degrees_to_cardinal(deg: float) -> str:
    """Convert wind direction in degrees to 16-point cardinal compass string."""
    val = int((deg / 22.5) + 0.5)
    cardinals = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    ]
    return cardinals[(val % 16)]


def calculate_uv_category(uv_index: float) -> Tuple[str, str]:
    """Return risk category and color for a UV Index value."""
    if uv_index < 3.0:
        return "Low", "#10B981"         # Green
    elif uv_index < 6.0:
        return "Moderate", "#F59E0B"    # Yellow/Amber
    elif uv_index < 8.0:
        return "High", "#F97316"        # Orange
    elif uv_index < 11.0:
        return "Very High", "#EF4444"   # Red
    else:
        return "Extreme", "#8B5CF6"     # Purple


def calculate_aqi_category(aqi_val: int) -> Tuple[str, str]:
    """
    Return category and color for an Air Quality Index.
    Supports OpenWeatherMap scale (1-5) and standard US AQI scale (0-500).
    """
    if aqi_val <= 5:
        # OpenWeatherMap 1 to 5 scale
        mapping = {
            1: ("Good", "#10B981"),
            2: ("Fair", "#84CC16"),
            3: ("Moderate", "#F59E0B"),
            4: ("Poor", "#F97316"),
            5: ("Very Poor", "#EF4444"),
        }
        return mapping.get(aqi_val, ("Unknown", "#94A3B8"))
    else:
        # Standard US AQI scale
        if aqi_val <= 50:
            return "Good", "#10B981"
        elif aqi_val <= 100:
            return "Moderate", "#F59E0B"
        elif aqi_val <= 150:
            return "Unhealthy for Sensitive", "#F97316"
        elif aqi_val <= 200:
            return "Unhealthy", "#EF4444"
        elif aqi_val <= 300:
            return "Very Unhealthy", "#8B5CF6"
        else:
            return "Hazardous", "#7E22CE"


def wmo_code_to_condition(code: int, is_day: bool = True) -> Tuple[str, str, str]:
    """
    Translate WMO Weather interpretation code (Open-Meteo) to
    (Condition, Description, Standard Icon Key).
    """
    table = {
        0: ("Clear", "Clear sky", "clear_day" if is_day else "clear_night"),
        1: ("Mainly Clear", "Mainly clear sky", "few_clouds_day" if is_day else "few_clouds_night"),
        2: ("Partly Cloudy", "Partly cloudy", "few_clouds_day" if is_day else "few_clouds_night"),
        3: ("Overcast", "Overcast skies", "cloudy"),
        45: ("Foggy", "Foggy conditions", "fog"),
        48: ("Depositing Rime Fog", "Icy rime fog", "fog"),
        51: ("Light Drizzle", "Light drizzle", "rain"),
        53: ("Moderate Drizzle", "Moderate drizzle", "rain"),
        55: ("Dense Drizzle", "Dense drizzle", "rain"),
        56: ("Freezing Drizzle", "Light freezing drizzle", "snow"),
        57: ("Dense Freezing Drizzle", "Dense freezing drizzle", "snow"),
        61: ("Slight Rain", "Slight rain showers", "rain"),
        63: ("Moderate Rain", "Moderate continuous rain", "heavy_rain"),
        65: ("Heavy Rain", "Heavy downpour", "heavy_rain"),
        66: ("Freezing Rain", "Light freezing rain", "snow"),
        67: ("Heavy Freezing Rain", "Heavy freezing rain", "snow"),
        71: ("Slight Snow", "Slight snowfall", "snow"),
        73: ("Moderate Snow", "Moderate snowfall", "snow"),
        75: ("Heavy Snow", "Heavy snowfall", "snow"),
        77: ("Snow Grains", "Snow grains", "snow"),
        80: ("Slight Rain Showers", "Scattered rain showers", "rain"),
        81: ("Moderate Rain Showers", "Moderate rain showers", "heavy_rain"),
        82: ("Violent Rain Showers", "Violent torrential showers", "heavy_rain"),
        85: ("Slight Snow Showers", "Slight snow showers", "snow"),
        86: ("Heavy Snow Showers", "Heavy snow showers", "snow"),
        95: ("Thunderstorm", "Thunderstorm", "thunderstorm"),
        96: ("Thunderstorm with Hail", "Thunderstorm with slight hail", "thunderstorm"),
        99: ("Severe Thunderstorm", "Severe thunderstorm with heavy hail", "thunderstorm"),
    }
    return table.get(code, ("Variable", "Variable weather", "cloudy"))


def owm_icon_to_key(icon_code: str, condition_id: int = 800) -> str:
    """
    Map OpenWeatherMap icon code and condition id to our standard icon key.
    """
    is_day = not icon_code.endswith("n")
    prefix = icon_code[:2] if len(icon_code) >= 2 else ""

    if prefix == "01":
        return "clear_day" if is_day else "clear_night"
    elif prefix == "02":
        return "few_clouds_day" if is_day else "few_clouds_night"
    elif prefix in ("03", "04"):
        return "cloudy"
    elif prefix == "09":
        return "rain"
    elif prefix == "10":
        return "heavy_rain" if is_day else "rain"
    elif prefix == "11":
        return "thunderstorm"
    elif prefix == "13":
        return "snow"
    elif prefix == "50":
        return "fog"

    # Fallback based on condition id
    if 200 <= condition_id < 300:
        return "thunderstorm"
    elif 300 <= condition_id < 600:
        return "rain"
    elif 600 <= condition_id < 700:
        return "snow"
    elif 700 <= condition_id < 800:
        return "fog"
    elif condition_id == 800:
        return "clear_day" if is_day else "clear_night"
    return "cloudy"


def format_timestamp(ts: int, tz_offset: int = 0) -> str:
    """Format Unix timestamp with timezone offset into 'hh:mm AM/PM'."""
    try:
        tz = timezone(timedelta(seconds=tz_offset))
        dt = datetime.fromtimestamp(ts, tz=tz)
        return dt.strftime("%I:%M %p")
    except Exception:
        return "--:--"


def format_day_name(date_str: str) -> str:
    """Format 'YYYY-MM-DD' into 'Day, Mon DD' (e.g. 'Tue, Nov 24')."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%a, %b %d")
    except Exception:
        return date_str
