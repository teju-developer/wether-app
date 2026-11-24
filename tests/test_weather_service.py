"""
Comprehensive Unit Tests for SkyPulse Weather Dashboard.
Uses mocked API responses to thoroughly test parsing, error handling,
forecast processing, conversions, locations manager, and theme engine offline.
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import tempfile
import shutil

from app.forecast import (
    celsius_to_fahrenheit,
    fahrenheit_to_celsius,
    convert_temp,
    degrees_to_cardinal,
    calculate_aqi_category,
    calculate_uv_category,
    wmo_code_to_condition,
    owm_icon_to_key,
    format_timestamp,
    format_day_name,
)
from app.locations import LocationManager
from app.themes import get_theme, get_theme_names
from app.weather_service import (
    WeatherService,
    WeatherData,
    ForecastData,
    HourlyForecast,
    DailyForecast,
    CityNotFoundError,
    NetworkError,
    InvalidApiKeyError,
    RateLimitError,
    WeatherError,
)


class TestForecastUtilities(unittest.TestCase):
    """Test temperature conversions, cardinal compass, AQI and UV calculations."""

    def test_celsius_to_fahrenheit(self):
        self.assertEqual(celsius_to_fahrenheit(0), 32.0)
        self.assertEqual(celsius_to_fahrenheit(100), 212.0)
        self.assertEqual(celsius_to_fahrenheit(25), 77.0)
        self.assertEqual(celsius_to_fahrenheit(-40), -40.0)

    def test_fahrenheit_to_celsius(self):
        self.assertEqual(fahrenheit_to_celsius(32), 0.0)
        self.assertEqual(fahrenheit_to_celsius(212), 100.0)
        self.assertEqual(fahrenheit_to_celsius(77), 25.0)
        self.assertEqual(fahrenheit_to_celsius(-40), -40.0)

    def test_convert_temp(self):
        self.assertEqual(convert_temp(20.0, "metric", "imperial"), 68.0)
        self.assertEqual(convert_temp(68.0, "imperial", "metric"), 20.0)
        self.assertEqual(convert_temp(20.0, "metric", "metric"), 20.0)

    def test_degrees_to_cardinal(self):
        self.assertEqual(degrees_to_cardinal(0), "N")
        self.assertEqual(degrees_to_cardinal(45), "NE")
        self.assertEqual(degrees_to_cardinal(90), "E")
        self.assertEqual(degrees_to_cardinal(135), "SE")
        self.assertEqual(degrees_to_cardinal(180), "S")
        self.assertEqual(degrees_to_cardinal(225), "SW")
        self.assertEqual(degrees_to_cardinal(270), "W")
        self.assertEqual(degrees_to_cardinal(315), "NW")
        self.assertEqual(degrees_to_cardinal(350), "N")

    def test_calculate_uv_category(self):
        cat, color = calculate_uv_category(1.5)
        self.assertEqual(cat, "Low")
        cat, color = calculate_uv_category(4.0)
        self.assertEqual(cat, "Moderate")
        cat, color = calculate_uv_category(7.0)
        self.assertEqual(cat, "High")
        cat, color = calculate_uv_category(9.5)
        self.assertEqual(cat, "Very High")
        cat, color = calculate_uv_category(12.0)
        self.assertEqual(cat, "Extreme")

    def test_calculate_aqi_category(self):
        # OpenWeatherMap 1-5 scale
        self.assertEqual(calculate_aqi_category(1)[0], "Good")
        self.assertEqual(calculate_aqi_category(2)[0], "Fair")
        self.assertEqual(calculate_aqi_category(3)[0], "Moderate")
        self.assertEqual(calculate_aqi_category(4)[0], "Poor")
        self.assertEqual(calculate_aqi_category(5)[0], "Very Poor")

        # US AQI scale
        self.assertEqual(calculate_aqi_category(25)[0], "Good")
        self.assertEqual(calculate_aqi_category(75)[0], "Moderate")
        self.assertEqual(calculate_aqi_category(125)[0], "Unhealthy for Sensitive")
        self.assertEqual(calculate_aqi_category(175)[0], "Unhealthy")
        self.assertEqual(calculate_aqi_category(250)[0], "Very Unhealthy")
        self.assertEqual(calculate_aqi_category(350)[0], "Hazardous")

    def test_wmo_code_to_condition(self):
        cond, desc, icon = wmo_code_to_condition(0, is_day=True)
        self.assertEqual(cond, "Clear")
        self.assertEqual(icon, "clear_day")

        cond, desc, icon = wmo_code_to_condition(0, is_day=False)
        self.assertEqual(icon, "clear_night")

        cond, desc, icon = wmo_code_to_condition(61, is_day=True)
        self.assertEqual(cond, "Slight Rain")
        self.assertEqual(icon, "rain")

        cond, desc, icon = wmo_code_to_condition(95, is_day=True)
        self.assertEqual(cond, "Thunderstorm")
        self.assertEqual(icon, "thunderstorm")

    def test_owm_icon_to_key(self):
        self.assertEqual(owm_icon_to_key("01d", 800), "clear_day")
        self.assertEqual(owm_icon_to_key("01n", 800), "clear_night")
        self.assertEqual(owm_icon_to_key("02d", 801), "few_clouds_day")
        self.assertEqual(owm_icon_to_key("04d", 804), "cloudy")
        self.assertEqual(owm_icon_to_key("10d", 500), "heavy_rain")
        self.assertEqual(owm_icon_to_key("11d", 211), "thunderstorm")
        self.assertEqual(owm_icon_to_key("13d", 600), "snow")
        self.assertEqual(owm_icon_to_key("50d", 701), "fog")

    def test_format_helpers(self):
        # 1600000000 = Sun, Sep 13, 2020 12:26:40 PM UTC
        formatted_time = format_timestamp(1600000000, tz_offset=0)
        self.assertTrue(":" in formatted_time)

        formatted_day = format_day_name("2026-11-24")
        self.assertTrue("Nov 24" in formatted_day)


class TestLocationManager(unittest.TestCase):
    """Test saved cities, duplicate prevention, and search history persistence."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage_file = Path(self.test_dir) / "test_locations.json"
        self.loc_mgr = LocationManager(storage_path=self.storage_file)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_default_cities(self):
        cities = self.loc_mgr.get_saved_cities()
        self.assertIn("Hubballi", cities)
        self.assertIn("London", cities)

    def test_add_and_remove_city(self):
        # Add new city
        added = self.loc_mgr.add_saved_city("Paris")
        self.assertTrue(added)
        self.assertTrue(self.loc_mgr.is_saved("Paris"))
        self.assertTrue(self.loc_mgr.is_saved("paris"))  # case-insensitive check

        # Prevent duplicate add
        added_again = self.loc_mgr.add_saved_city("paris")
        self.assertFalse(added_again)

        # Remove city
        removed = self.loc_mgr.remove_saved_city("Paris")
        self.assertTrue(removed)
        self.assertFalse(self.loc_mgr.is_saved("Paris"))

    def test_recent_searches(self):
        self.loc_mgr.add_recent_search("Sydney")
        self.loc_mgr.add_recent_search("Mumbai")
        recents = self.loc_mgr.get_recent_searches()
        self.assertEqual(recents[0], "Mumbai")
        self.assertEqual(recents[1], "Sydney")

        self.loc_mgr.clear_recent_searches()
        self.assertEqual(len(self.loc_mgr.get_recent_searches()), 0)


class TestThemes(unittest.TestCase):
    """Test theme registry and theme properties."""

    def test_theme_retrieval(self):
        midnight = get_theme("midnight")
        self.assertEqual(midnight.name, "midnight")
        self.assertTrue(midnight.is_dark)

        sunset = get_theme("sunset")
        self.assertEqual(sunset.name, "sunset")
        self.assertTrue(sunset.is_dark)

        light = get_theme("light")
        self.assertEqual(light.name, "light")
        self.assertFalse(light.is_dark)

        # Fallback for invalid theme name
        fallback = get_theme("non_existent")
        self.assertEqual(fallback.name, "midnight")

    def test_theme_names(self):
        names = get_theme_names()
        self.assertIn("midnight", names)
        self.assertIn("sunset", names)
        self.assertIn("light", names)


class TestWeatherService(unittest.TestCase):
    """Test weather service with mocked API responses (offline)."""

    def setUp(self):
        self.service = WeatherService()

    @patch("requests.Session.get")
    def test_openmeteo_fetch_success(self, mock_get):
        """Test complete weather parsing via Open-Meteo fallback."""
        # Mock geocoding response
        geo_mock = MagicMock()
        geo_mock.status_code = 200
        geo_mock.json.return_value = {
            "results": [{
                "name": "Hubballi",
                "country": "India",
                "latitude": 15.3647,
                "longitude": 75.1240,
            }]
        }

        # Mock weather response
        weather_mock = MagicMock()
        weather_mock.status_code = 200
        weather_mock.json.return_value = {
            "current": {
                "temperature_2m": 28.5,
                "relative_humidity_2m": 62,
                "apparent_temperature": 29.8,
                "is_day": 1,
                "weather_code": 1,
                "surface_pressure": 1012.0,
                "wind_speed_10m": 14.5,
                "wind_direction_10m": 120.0,
            },
            "hourly": {
                "time": ["2026-11-24T12:00", "2026-11-24T13:00", "2026-11-24T14:00"],
                "temperature_2m": [28.5, 29.0, 29.5],
                "precipitation_probability": [10, 15, 20],
                "weather_code": [1, 2, 2],
                "relative_humidity_2m": [62, 60, 58],
                "wind_speed_10m": [14.5, 15.0, 15.2],
                "is_day": [1, 1, 1],
            },
            "daily": {
                "time": ["2026-11-24", "2026-11-25"],
                "weather_code": [1, 2],
                "temperature_2m_max": [31.0, 31.5],
                "temperature_2m_min": [21.0, 20.5],
                "precipitation_probability_max": [20, 30],
                "sunrise": ["2026-11-24T06:30"],
                "sunset": ["2026-11-24T18:00"],
                "uv_index_max": [7.5, 8.0],
            }
        }

        # Mock air quality response
        aq_mock = MagicMock()
        aq_mock.status_code = 200
        aq_mock.json.return_value = {
            "current": {
                "us_aqi": 35
            }
        }

        mock_get.side_effect = [geo_mock, weather_mock, aq_mock]

        w_data, f_data = self.service._fetch_openmeteo("Hubballi", units="metric")

        self.assertEqual(w_data.city, "Hubballi")
        self.assertEqual(w_data.country, "India")
        self.assertEqual(w_data.temperature, 28.5)
        self.assertEqual(w_data.humidity, 62)
        self.assertEqual(w_data.wind_speed, 14.5)
        self.assertEqual(w_data.wind_direction_cardinal, "ESE")
        self.assertEqual(w_data.provider, "Open-Meteo")
        self.assertEqual(len(f_data.hourly), 3)
        self.assertEqual(len(f_data.daily), 2)
        self.assertEqual(f_data.daily[0].temp_max, 31.0)
        self.assertEqual(f_data.daily[0].temp_min, 21.0)

    @patch("requests.Session.get")
    def test_city_not_found(self, mock_get):
        """Test CityNotFoundError when city name doesn't exist."""
        geo_mock = MagicMock()
        geo_mock.status_code = 200
        geo_mock.json.return_value = {"results": []}
        mock_get.return_value = geo_mock

        with self.assertRaises(CityNotFoundError):
            self.service._fetch_openmeteo("InvalidCityXYZ999", units="metric")

    @patch("requests.Session.get")
    def test_network_timeout(self, mock_get):
        """Test NetworkError on connection timeout."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        with self.assertRaises(NetworkError):
            self.service._fetch_openmeteo("London", units="metric")

    @patch("requests.Session.get")
    def test_openweathermap_fetch_success(self, mock_get):
        """Test OpenWeatherMap response parsing."""
        cur_mock = MagicMock()
        cur_mock.status_code = 200
        cur_mock.json.return_value = {
            "coord": {"lat": 51.5074, "lon": -0.1278},
            "name": "London",
            "sys": {"country": "GB", "sunrise": 1600000000, "sunset": 1600045000},
            "main": {
                "temp": 18.5,
                "feels_like": 17.8,
                "temp_min": 16.0,
                "temp_max": 20.0,
                "humidity": 68,
                "pressure": 1016,
            },
            "weather": [{
                "main": "Rain",
                "description": "light rain",
                "icon": "10d",
                "id": 500,
            }],
            "wind": {"speed": 4.5, "deg": 240},
            "visibility": 10000,
            "timezone": 3600,
        }

        aqi_mock = MagicMock()
        aqi_mock.status_code = 200
        aqi_mock.json.return_value = {
            "list": [{"main": {"aqi": 2}}]
        }

        fc_mock = MagicMock()
        fc_mock.status_code = 200
        fc_mock.json.return_value = {
            "list": [
                {
                    "dt": 1600010000,
                    "dt_txt": "2026-11-24 15:00:00",
                    "main": {"temp": 18.0, "humidity": 70},
                    "weather": [{"main": "Rain", "icon": "10d", "id": 500}],
                    "wind": {"speed": 4.0},
                    "pop": 0.4,
                }
            ]
        }

        uv_mock = MagicMock()
        uv_mock.status_code = 200
        uv_mock.json.return_value = {
            "daily": {"uv_index_max": [5.0]}
        }

        mock_get.side_effect = [cur_mock, aqi_mock, fc_mock, uv_mock]

        w_data, f_data = self.service._fetch_openweathermap("London", "valid_test_api_key", units="metric")

        self.assertEqual(w_data.city, "London")
        self.assertEqual(w_data.country, "GB")
        self.assertEqual(w_data.temperature, 18.5)
        self.assertEqual(w_data.condition, "Rain")
        self.assertEqual(w_data.provider, "OpenWeatherMap")
        self.assertEqual(w_data.visibility_km, 10.0)
        self.assertEqual(w_data.aqi_category, "Fair")
        self.assertEqual(w_data.uv_category, "Moderate")

    @patch("requests.Session.get")
    def test_openweathermap_invalid_key(self, mock_get):
        """Test InvalidApiKeyError when 401 is returned."""
        err_mock = MagicMock()
        err_mock.status_code = 401
        mock_get.return_value = err_mock

        with self.assertRaises(InvalidApiKeyError):
            self.service._fetch_openweathermap("London", "bad_key", units="metric")

    @patch("requests.Session.get")
    def test_openweathermap_rate_limit(self, mock_get):
        """Test RateLimitError when 429 is returned."""
        err_mock = MagicMock()
        err_mock.status_code = 429
        mock_get.return_value = err_mock

        with self.assertRaises(RateLimitError):
            self.service._fetch_openweathermap("London", "valid_key", units="metric")


if __name__ == "__main__":
    unittest.main()
