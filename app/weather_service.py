"""
Weather Service Module for SkyPulse Weather Dashboard.
Provides robust dual-engine weather fetching (OpenWeatherMap + Open-Meteo zero-config fallback),
supporting current weather, 24-hour hourly forecast, 7-day daily forecast, air quality, and UV index.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
import requests

import config
from app.forecast import (
    degrees_to_cardinal,
    calculate_aqi_category,
    calculate_uv_category,
    wmo_code_to_condition,
    owm_icon_to_key,
    format_timestamp,
    format_day_name,
)


class WeatherError(Exception):
    """Base exception for weather operations."""
    pass


class CityNotFoundError(WeatherError):
    """Raised when city is not found by geocoding or weather API."""
    pass


class NetworkError(WeatherError):
    """Raised when network failure or timeout occurs."""
    pass


class InvalidApiKeyError(WeatherError):
    """Raised when OpenWeatherMap API key is invalid."""
    pass


class RateLimitError(WeatherError):
    """Raised when API rate limit is exceeded."""
    pass


@dataclass
class WeatherData:
    """Comprehensive current weather data model."""
    city: str
    country: str
    latitude: float
    longitude: float
    temperature: float
    feels_like: float
    temp_min: float
    temp_max: float
    condition: str
    description: str
    humidity: int
    pressure: int
    wind_speed: float
    wind_direction_deg: float
    wind_direction_cardinal: str
    visibility_km: Optional[float]
    sunrise: str
    sunset: str
    uv_index: Optional[float]
    uv_category: str
    uv_color: str
    aqi: Optional[int]
    aqi_category: str
    aqi_color: str
    rain_probability: Optional[int]
    icon_key: str
    last_updated: str
    provider: str
    units: str = "metric"


@dataclass
class HourlyForecast:
    """Hourly forecast item for 24-hour trend."""
    time_label: str
    hour: int
    temperature: float
    condition: str
    icon_key: str
    rain_probability: Optional[int]
    humidity: int
    wind_speed: float


@dataclass
class DailyForecast:
    """Daily forecast item for 7-day outlook."""
    date_str: str
    day_name: str
    temp_min: float
    temp_max: float
    condition: str
    description: str
    icon_key: str
    rain_probability: Optional[int]
    humidity: Optional[int]
    uv_index: Optional[float]


@dataclass
class ForecastData:
    """Complete forecast package containing hourly and daily data."""
    hourly: List[HourlyForecast] = field(default_factory=list)
    daily: List[DailyForecast] = field(default_factory=list)


class WeatherService:
    """
    Dual-engine weather service supporting OpenWeatherMap (primary when key present)
    and Open-Meteo (zero-config, high-precision fallback).
    """

    DEFAULT_TIMEOUT = 10

    def __init__(self):
        self.session = requests.Session()

    def get_complete_weather(self, city_name: str, units: str = "metric") -> Tuple[WeatherData, ForecastData]:
        """Fetch both current weather and extended forecast for a city."""
        clean_city = city_name.strip()
        if not clean_city:
            raise WeatherError("Please enter a valid city name.")

        api_key = config.get_api_key()
        provider_pref = config.load_user_config().get("api_provider", "auto")

        # Try OpenWeatherMap if key is available and provider preference allows
        if api_key and provider_pref in ("auto", "openweathermap"):
            try:
                return self._fetch_openweathermap(clean_city, api_key, units)
            except InvalidApiKeyError:
                # Fallback to Open-Meteo with warning
                pass
            except CityNotFoundError:
                raise
            except Exception:
                # Other transient errors fall back to Open-Meteo
                pass

        # Fallback to Open-Meteo (Teju's original API foundation upgraded to full capabilities)
        return self._fetch_openmeteo(clean_city, units)

    def _fetch_openweathermap(self, city_name: str, api_key: str, units: str) -> Tuple[WeatherData, ForecastData]:
        """Fetch weather and forecast using OpenWeatherMap API."""
        # 1. Current Weather
        current_url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city_name,
            "appid": api_key,
            "units": units,
        }

        try:
            resp = self.session.get(current_url, params=params, timeout=self.DEFAULT_TIMEOUT)
        except requests.exceptions.Timeout:
            raise NetworkError("Connection to OpenWeatherMap timed out. Please check your internet.")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network error: {e}")

        if resp.status_code == 401:
            raise InvalidApiKeyError("Invalid OpenWeatherMap API key. Falling back to Open-Meteo.")
        elif resp.status_code == 404:
            raise CityNotFoundError(f"City '{city_name}' was not found. Please check spelling.")
        elif resp.status_code == 429:
            raise RateLimitError("OpenWeatherMap rate limit reached. Please wait a moment.")
        elif resp.status_code != 200:
            raise WeatherError(f"OpenWeatherMap error (Code {resp.status_code}): {resp.text}")

        data = resp.json()

        lat = data["coord"]["lat"]
        lon = data["coord"]["lon"]
        found_city = data.get("name", city_name)
        country = data.get("sys", {}).get("country", "")

        main_data = data.get("main", {})
        temp = round(main_data.get("temp", 0.0), 1)
        feels_like = round(main_data.get("feels_like", temp), 1)
        temp_min = round(main_data.get("temp_min", temp), 1)
        temp_max = round(main_data.get("temp_max", temp), 1)
        humidity = int(main_data.get("humidity", 0))
        pressure = int(main_data.get("pressure", 1013))

        weather_list = data.get("weather", [{}])
        first_weather = weather_list[0] if weather_list else {}
        condition = first_weather.get("main", "Clear")
        description = first_weather.get("description", "clear sky").title()
        icon_code = first_weather.get("icon", "01d")
        condition_id = first_weather.get("id", 800)
        icon_key = owm_icon_to_key(icon_code, condition_id)

        wind_data = data.get("wind", {})
        wind_speed = round(wind_data.get("speed", 0.0) * (3.6 if units == "metric" else 1.0), 1)
        wind_deg = float(wind_data.get("deg", 0.0))
        wind_cardinal = degrees_to_cardinal(wind_deg)

        vis_m = data.get("visibility")
        visibility_km = round(vis_m / 1000.0, 1) if vis_m is not None else None

        tz_offset = data.get("timezone", 0)
        sys_data = data.get("sys", {})
        sunrise = format_timestamp(sys_data.get("sunrise", 0), tz_offset)
        sunset = format_timestamp(sys_data.get("sunset", 0), tz_offset)

        # 2. Air Pollution & UV (if available)
        aqi_val = None
        aqi_cat, aqi_color = "N/A", "#94A3B8"
        try:
            aqi_url = "https://api.openweathermap.org/data/2.5/air_pollution"
            aqi_resp = self.session.get(aqi_url, params={"lat": lat, "lon": lon, "appid": api_key}, timeout=5)
            if aqi_resp.status_code == 200:
                aqi_list = aqi_resp.json().get("list", [])
                if aqi_list:
                    aqi_val = aqi_list[0].get("main", {}).get("aqi")
                    if aqi_val:
                        aqi_cat, aqi_color = calculate_aqi_category(int(aqi_val))
        except Exception:
            pass

        # 3. Forecast Data (5-day / 3-hour)
        forecast_data = ForecastData()
        try:
            fc_url = "https://api.openweathermap.org/data/2.5/forecast"
            fc_resp = self.session.get(fc_url, params={"lat": lat, "lon": lon, "appid": api_key, "units": units}, timeout=self.DEFAULT_TIMEOUT)
            if fc_resp.status_code == 200:
                fc_json = fc_resp.json()
                forecast_data = self._parse_owm_forecast(fc_json, tz_offset)
        except Exception:
            pass

        # UV index from Open-Meteo supplementary call (OWM free tier does not include UV in 2.5)
        uv_val = None
        uv_cat, uv_color = "Moderate", "#F59E0B"
        try:
            uv_resp = self.session.get(
                "https://api.open-meteo.com/v1/forecast",
                params={"latitude": lat, "longitude": lon, "daily": "uv_index_max", "timezone": "auto"},
                timeout=4
            )
            if uv_resp.status_code == 200:
                daily_uv = uv_resp.json().get("daily", {}).get("uv_index_max", [])
                if daily_uv:
                    uv_val = round(float(daily_uv[0]), 1)
                    uv_cat, uv_color = calculate_uv_category(uv_val)
        except Exception:
            pass

        current_weather = WeatherData(
            city=found_city,
            country=country,
            latitude=lat,
            longitude=lon,
            temperature=temp,
            feels_like=feels_like,
            temp_min=temp_min,
            temp_max=temp_max,
            condition=condition,
            description=description,
            humidity=humidity,
            pressure=pressure,
            wind_speed=wind_speed,
            wind_direction_deg=wind_deg,
            wind_direction_cardinal=wind_cardinal,
            visibility_km=visibility_km,
            sunrise=sunrise,
            sunset=sunset,
            uv_index=uv_val,
            uv_category=uv_cat,
            uv_color=uv_color,
            aqi=aqi_val,
            aqi_category=aqi_cat,
            aqi_color=aqi_color,
            rain_probability=forecast_data.hourly[0].rain_probability if forecast_data.hourly else None,
            icon_key=icon_key,
            last_updated=datetime.now().strftime("%I:%M %p"),
            provider="OpenWeatherMap",
            units=units,
        )

        return current_weather, forecast_data

    def _parse_owm_forecast(self, fc_json: dict, tz_offset: int) -> ForecastData:
        """Parse OpenWeatherMap 5-day / 3-hour forecast into Hourly and Daily models."""
        items = fc_json.get("list", [])
        hourly: List[HourlyForecast] = []
        daily_map: Dict[str, dict] = {}

        for item in items:
            dt_ts = item.get("dt", 0)
            time_label = format_timestamp(dt_ts, tz_offset)
            hour_val = int(datetime.fromtimestamp(dt_ts, tz=timezone.utc).strftime("%H"))

            main = item.get("main", {})
            temp = round(main.get("temp", 0.0), 1)
            humidity = int(main.get("humidity", 0))

            w_list = item.get("weather", [{}])
            w_first = w_list[0] if w_list else {}
            cond = w_first.get("main", "Clear")
            icon_code = w_first.get("icon", "01d")
            cond_id = w_first.get("id", 800)
            icon_key = owm_icon_to_key(icon_code, cond_id)

            wind_spd = round(item.get("wind", {}).get("speed", 0.0) * 3.6, 1)
            pop = round(item.get("pop", 0.0) * 100)

            # Keep next 8 items for 24-hour hourly ribbon
            if len(hourly) < 8:
                hourly.append(
                    HourlyForecast(
                        time_label=time_label,
                        hour=hour_val,
                        temperature=temp,
                        condition=cond,
                        icon_key=icon_key,
                        rain_probability=pop,
                        humidity=humidity,
                        wind_speed=wind_spd,
                    )
                )

            # Aggregate into daily map by date string
            date_str = item.get("dt_txt", "").split(" ")[0]
            if date_str:
                if date_str not in daily_map:
                    daily_map[date_str] = {
                        "date_str": date_str,
                        "temps": [],
                        "conditions": [],
                        "icons": [],
                        "pops": [],
                        "humidities": [],
                    }
                daily_map[date_str]["temps"].append(temp)
                daily_map[date_str]["conditions"].append(cond)
                daily_map[date_str]["icons"].append(icon_key)
                daily_map[date_str]["pops"].append(pop)
                daily_map[date_str]["humidities"].append(humidity)

        daily: List[DailyForecast] = []
        for d_str, d_val in list(daily_map.items())[:7]:
            temps = d_val["temps"]
            min_t = min(temps) if temps else 0.0
            max_t = max(temps) if temps else 0.0
            cond = max(set(d_val["conditions"]), key=d_val["conditions"].count) if d_val["conditions"] else "Clear"
            icon = max(set(d_val["icons"]), key=d_val["icons"].count) if d_val["icons"] else "clear_day"
            max_pop = max(d_val["pops"]) if d_val["pops"] else 0
            avg_hum = int(sum(d_val["humidities"]) / len(d_val["humidities"])) if d_val["humidities"] else 50

            daily.append(
                DailyForecast(
                    date_str=d_str,
                    day_name=format_day_name(d_str),
                    temp_min=min_t,
                    temp_max=max_t,
                    condition=cond,
                    description=cond,
                    icon_key=icon,
                    rain_probability=max_pop,
                    humidity=avg_hum,
                    uv_index=None,
                )
            )

        return ForecastData(hourly=hourly, daily=daily)

    def _fetch_openmeteo(self, city_name: str, units: str) -> Tuple[WeatherData, ForecastData]:
        """
        Fetch full real-time weather and forecast using Open-Meteo.
        Preserves and elevates the exact API foundation from Teju's original wether app.py.
        """
        # 1. Geocoding
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        try:
            geo_resp = self.session.get(geo_url, params={"name": city_name, "count": 5}, timeout=self.DEFAULT_TIMEOUT)
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()
        except requests.exceptions.Timeout:
            raise NetworkError("Geocoding request timed out. Please check your internet.")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network error during geocoding: {e}")

        results = geo_data.get("results", [])
        if not results:
            raise CityNotFoundError(f"City '{city_name}' was not found. Please check spelling.")

        place = results[0]
        lat = place["latitude"]
        lon = place["longitude"]
        resolved_city = place.get("name", city_name)
        country = place.get("country", "")

        # 2. Weather & Forecast
        temp_unit = "fahrenheit" if units == "imperial" else "celsius"
        wind_unit = "mph" if units == "imperial" else "kmh"

        params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "is_day",
                "weather_code",
                "surface_pressure",
                "wind_speed_10m",
                "wind_direction_10m",
            ],
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation_probability",
                "weather_code",
                "wind_speed_10m",
                "is_day",
            ],
            "daily": [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_probability_max",
                "sunrise",
                "sunset",
                "uv_index_max",
            ],
            "temperature_unit": temp_unit,
            "wind_speed_unit": wind_unit,
            "timezone": "auto",
        }

        try:
            weather_resp = self.session.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=self.DEFAULT_TIMEOUT)
            weather_resp.raise_for_status()
            w_data = weather_resp.json()
        except requests.exceptions.Timeout:
            raise NetworkError("Weather data request timed out.")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network error fetching weather: {e}")

        current = w_data.get("current", {})
        temp = round(current.get("temperature_2m", 0.0), 1)
        feels_like = round(current.get("apparent_temperature", temp), 1)
        humidity = int(current.get("relative_humidity_2m", 0))
        pressure = int(round(current.get("surface_pressure", 1013.0)))
        wind_speed = round(current.get("wind_speed_10m", 0.0), 1)
        wind_deg = float(current.get("wind_direction_10m", 0.0))
        wind_cardinal = degrees_to_cardinal(wind_deg)
        is_day = bool(current.get("is_day", 1))

        code = int(current.get("weather_code", 0))
        condition, description, icon_key = wmo_code_to_condition(code, is_day=is_day)

        daily = w_data.get("daily", {})
        temp_max_list = daily.get("temperature_2m_max", [])
        temp_min_list = daily.get("temperature_2m_min", [])
        temp_max = round(temp_max_list[0], 1) if temp_max_list else temp
        temp_min = round(temp_min_list[0], 1) if temp_min_list else temp

        # Sunrise & Sunset
        sunrises = daily.get("sunrise", [])
        sunsets = daily.get("sunset", [])
        sunrise_str = sunrises[0].split("T")[-1][:5] if sunrises else "--:--"
        sunset_str = sunsets[0].split("T")[-1][:5] if sunsets else "--:--"

        # Convert to 12-hour AM/PM format
        try:
            sr_dt = datetime.strptime(sunrise_str, "%H:%M")
            sunrise_fmt = sr_dt.strftime("%I:%M %p")
        except Exception:
            sunrise_fmt = sunrise_str

        try:
            ss_dt = datetime.strptime(sunset_str, "%H:%M")
            sunset_fmt = ss_dt.strftime("%I:%M %p")
        except Exception:
            sunset_fmt = sunset_str

        # UV Index
        uv_list = daily.get("uv_index_max", [])
        uv_val = round(float(uv_list[0]), 1) if uv_list else None
        uv_cat, uv_color = calculate_uv_category(uv_val) if uv_val is not None else ("Moderate", "#F59E0B")

        # 3. Air Quality
        aqi_val = None
        aqi_cat, aqi_color = "Good", "#10B981"
        try:
            aq_resp = self.session.get(
                "https://air-quality-api.open-meteo.com/v1/air-quality",
                params={"latitude": lat, "longitude": lon, "current": "us_aqi"},
                timeout=5
            )
            if aq_resp.status_code == 200:
                aq_cur = aq_resp.json().get("current", {})
                raw_aqi = aq_cur.get("us_aqi")
                if raw_aqi is not None:
                    aqi_val = int(raw_aqi)
                    aqi_cat, aqi_color = calculate_aqi_category(aqi_val)
        except Exception:
            pass

        # 4. Hourly Forecast (next 24 hours, take every 2-3 hours or 8 points)
        hourly_raw = w_data.get("hourly", {})
        h_times = hourly_raw.get("time", [])
        h_temps = hourly_raw.get("temperature_2m", [])
        h_pops = hourly_raw.get("precipitation_probability", [])
        h_codes = hourly_raw.get("weather_code", [])
        h_hums = hourly_raw.get("relative_humidity_2m", [])
        h_winds = hourly_raw.get("wind_speed_10m", [])
        h_is_days = hourly_raw.get("is_day", [])

        hourly_items: List[HourlyForecast] = []
        # Find current hour index or start from 0
        now_hour = datetime.now().hour
        for idx in range(min(24, len(h_times))):
            t_str = h_times[idx]
            # e.g. "2026-11-24T14:00"
            hour_val = int(t_str.split("T")[-1].split(":")[0])
            try:
                t_dt = datetime.strptime(t_str.split("T")[-1][:5], "%H:%M")
                t_label = t_dt.strftime("%I %p")
            except Exception:
                t_label = f"{hour_val}:00"

            h_code = int(h_codes[idx]) if idx < len(h_codes) else 0
            h_day = bool(h_is_days[idx]) if idx < len(h_is_days) else True
            _, _, h_icon = wmo_code_to_condition(h_code, is_day=h_day)

            hourly_items.append(
                HourlyForecast(
                    time_label=t_label,
                    hour=hour_val,
                    temperature=round(h_temps[idx], 1) if idx < len(h_temps) else temp,
                    condition=wmo_code_to_condition(h_code, is_day=h_day)[0],
                    icon_key=h_icon,
                    rain_probability=int(h_pops[idx]) if idx < len(h_pops) and h_pops[idx] is not None else 0,
                    humidity=int(h_hums[idx]) if idx < len(h_hums) else humidity,
                    wind_speed=round(h_winds[idx], 1) if idx < len(h_winds) else wind_speed,
                )
            )

        # 5. 7-Day Forecast
        daily_items: List[DailyForecast] = []
        d_dates = daily.get("time", [])
        d_codes = daily.get("weather_code", [])
        d_maxs = daily.get("temperature_2m_max", [])
        d_mins = daily.get("temperature_2m_min", [])
        d_pops = daily.get("precipitation_probability_max", [])
        d_uvs = daily.get("uv_index_max", [])

        for d_i in range(min(7, len(d_dates))):
            dt_s = d_dates[d_i]
            d_c = int(d_codes[d_i]) if d_i < len(d_codes) else 0
            d_cond, d_desc, d_icon = wmo_code_to_condition(d_c, is_day=True)
            d_pop = int(d_pops[d_i]) if d_i < len(d_pops) and d_pops[d_i] is not None else 0
            d_uv = round(float(d_uvs[d_i]), 1) if d_i < len(d_uvs) and d_uvs[d_i] is not None else None

            daily_items.append(
                DailyForecast(
                    date_str=dt_s,
                    day_name=format_day_name(dt_s),
                    temp_min=round(d_mins[d_i], 1) if d_i < len(d_mins) else temp_min,
                    temp_max=round(d_maxs[d_i], 1) if d_i < len(d_maxs) else temp_max,
                    condition=d_cond,
                    description=d_desc,
                    icon_key=d_icon,
                    rain_probability=d_pop,
                    humidity=None,
                    uv_index=d_uv,
                )
            )

        forecast_data = ForecastData(hourly=hourly_items, daily=daily_items)

        current_weather = WeatherData(
            city=resolved_city,
            country=country,
            latitude=lat,
            longitude=lon,
            temperature=temp,
            feels_like=feels_like,
            temp_min=temp_min,
            temp_max=temp_max,
            condition=condition,
            description=description,
            humidity=humidity,
            pressure=pressure,
            wind_speed=wind_speed,
            wind_direction_deg=wind_deg,
            wind_direction_cardinal=wind_cardinal,
            visibility_km=None,  # Open-Meteo standard tier doesn't estimate surface visibility
            sunrise=sunrise_fmt,
            sunset=sunset_fmt,
            uv_index=uv_val,
            uv_category=uv_cat,
            uv_color=uv_color,
            aqi=aqi_val,
            aqi_category=aqi_cat,
            aqi_color=aqi_color,
            rain_probability=hourly_items[0].rain_probability if hourly_items else None,
            icon_key=icon_key,
            last_updated=datetime.now().strftime("%I:%M %p"),
            provider="Open-Meteo",
            units=units,
        )

        return current_weather, forecast_data

    def detect_current_location(self) -> Tuple[float, float, str, str]:
        """
        Detect user location using IP geolocation with explicit permission.
        Returns (latitude, longitude, city, country).
        """
        try:
            resp = self.session.get("https://ipapi.co/json/", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                lat = float(data.get("latitude", 0.0))
                lon = float(data.get("longitude", 0.0))
                city = data.get("city", "Hubballi")
                country = data.get("country_name", "India")
                return lat, lon, city, country
        except Exception:
            pass

        # Fallback to ip-api
        try:
            resp = self.session.get("http://ip-api.com/json/", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    return (
                        float(data.get("lat", 0.0)),
                        float(data.get("lon", 0.0)),
                        data.get("city", "Hubballi"),
                        data.get("country", "India"),
                    )
        except Exception:
            pass

        raise NetworkError("Unable to detect current location from IP address.")

    def test_api_key(self, api_key: str) -> Tuple[bool, str]:
        """Validate if an OpenWeatherMap API key is active and authorized."""
        if not api_key.strip():
            return False, "API key cannot be empty."
        try:
            resp = self.session.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": "London", "appid": api_key.strip()},
                timeout=5
            )
            if resp.status_code == 200:
                return True, "API key is valid and active!"
            elif resp.status_code == 401:
                return False, "Invalid API key (Unauthorized). Please check key."
            else:
                return False, f"API test returned status {resp.status_code}."
        except Exception as e:
            return False, f"Connection test failed: {e}"

    # PRESERVE ORIGINAL WORKING FUNCTIONALITY: Teju's original CLI function
    def fetch_weather_cli(self, city: str) -> None:
        """
        Original working CLI function from Teju's initial wether app.py,
        preserved 100% for backwards-compatibility.
        """
        geo_response = self.session.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1},
            timeout=10,
        )
        geo_response.raise_for_status()
        geo_data = geo_response.json()

        if not geo_data.get("results"):
            print(f"City not found: {city}")
            return

        place = geo_data["results"][0]
        lat = place["latitude"]
        lon = place["longitude"]
        city_name = place["name"]
        country = place.get("country", "")

        weather_response = self.session.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
                "timezone": "auto",
            },
            timeout=10,
        )
        weather_response.raise_for_status()
        current = weather_response.json()["current"]

        print(f"\nWeather in {city_name}, {country}")
        print(f"Temperature : {current['temperature_2m']} °C")
        print(f"Humidity    : {current['relative_humidity_2m']}%")
        print(f"Wind Speed  : {current['wind_speed_10m']} km/h")
