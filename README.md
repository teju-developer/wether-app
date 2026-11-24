# SkyPulse Weather Dashboard 2.0

> Premium, commercial-grade desktop weather station and forecasting dashboard developed in Python.
> Built as an upgrade to Tejashwini's (`teju-developer`) original Python weather application.

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![UI Framework](https://img.shields.io/badge/GUI-CustomTkinter-00F0FF.svg)](https://customtkinter.tomschimansky.com/)
[![Visualization](https://img.shields.io/badge/charts-Matplotlib-orange.svg)](https://matplotlib.org/)
[![Tests](https://img.shields.io/badge/tests-20%20passed%20(100%25)-brightgreen.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

---

## 🌟 Overview

**SkyPulse Weather Dashboard 2.0** transforms a simple command-line weather script into a modern desktop weather platform. It integrates a dual-engine data provider, responsive glassmorphism UI, real-time hourly and weekly visualizations, multi-city side-by-side analytics, and on-the-fly theme customization.

---

## 🚀 Key Features

### 1. Modern Glassmorphism Interface
- Deep navy, sunset purple, and crisp sky-light color schemes.
- Rounded translucent cards, high-contrast typography, and smooth layouts.
- Dynamic high-resolution vector weather icons generated via Pillow.
- 100% resizable and responsive design with smooth scrolling containers.

### 2. Dual-Engine Live Weather Service
- **Primary Engine**: OpenWeatherMap API integration with secure `.env` key storage.
- **Fallback Engine**: Zero-config Open-Meteo API integration (preserving the original application's data source).
- Full fault-tolerance: automatically falls back to Open-Meteo if an OpenWeatherMap key is missing or invalid.

### 3. Comprehensive Weather Metrics
- Visual current temperature in large prominent font.
- "Feels like" apparent temperature.
- Daily high / low temperature spreads.
- Humidity with comfort index evaluation.
- Wind speed and 16-point cardinal compass direction (e.g. `17.1 km/h E`).
- Atmospheric barometric pressure in `hPa`.
- Visibility estimations in kilometers / miles.
- Sunrise and sunset local times.
- Real-time Air Quality Index (AQI) with health safety category.
- UV Index with sun-exposure risk categorization.
- Precipitation probability.

### 4. 24-Hour Hourly Forecast
- Horizontal scrollable ribbon displaying time, conditions, temperature, and rain chance.
- Embedded Matplotlib trajectory spline chart showing temperature trends across 24 hours.

### 5. 7-Day Extended Weekly Forecast
- Comprehensive 7-day outlook cards with weather conditions and rain chances.
- Interactive high vs. low temperature band chart with shaded range fill.

### 6. Interactive Theme Engine
Switch between three visual themes instantly without restarting the application:
1. **Midnight Blue** (Default): Deep dark navy (`#0B132B`) with electric cyan (`#00F0FF`) accents.
2. **Sunset Glow**: Deep twilight purple (`#1E112A`) with warm coral (`#FF6B6B`) and peach highlights.
3. **Light Sky**: Clean slate-white (`#F1F5F9`) with ocean blue (`#0284C7`) accents.

### 7. Multi-City Management & Comparison
- Star/unstar cities to save them to local favorites.
- Instant switching between favorite cities with one click.
- Side-by-side comparison matrix comparing temperature, humidity, wind, and air quality across saved cities.
- Recent search history saved locally in `saved_locations.json`.

### 8. Backwards Compatibility
- Preserves Tejashwini's original command-line script (`wether app.py`).
- Supports running in terminal mode (`python main.py --cli [city]`) or full GUI mode (`python main.py`).

---

## 📁 Project Architecture

```
weather-app/
├── main.py                  # Main application launcher (GUI & CLI modes)
├── wether app.py            # Original script preserved with 100% backwards-compatibility
├── config.py                # Configuration and secure environment variables manager
├── requirements.txt         # Project dependencies
├── .env.example             # Template for API credentials
├── .gitignore               # Ignored files (secrets, caches, local configs)
├── README.md                # Project documentation and portfolio presentation
│
├── app/
│   ├── __init__.py          # Package initializer
│   ├── ui.py                # CustomTkinter glassmorphism GUI implementation
│   ├── weather_service.py   # Dual-engine weather fetcher & data models
│   ├── forecast.py          # Forecast processors, unit conversions & WMO/OWM mappings
│   ├── charts.py            # Matplotlib theme-integrated visualizations
│   ├── locations.py         # Saved locations & search history JSON persistence
│   └── themes.py            # Color palettes for Midnight, Sunset, and Light themes
│
├── assets/
│   ├── generate_icons.py    # Pillow script to render anti-aliased icons
│   └── weather_icons/       # 17 rendered weather condition and gauge PNG icons
│
└── tests/
    └── test_weather_service.py  # 20 offline unit tests with mocked API responses
```

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10 or higher
- `pip` package manager

### 1. Clone or Open the Repository
```bash
git clone https://github.com/teju-developer/wether-app.git
cd wether-app
```

### 2. Install Required Dependencies
```bash
python -m pip install -r requirements.txt
```

### 3. Configure API Key (Optional)
The application works immediately out-of-the-box without an API key using the Open-Meteo fallback engine.

To connect OpenWeatherMap API:
1. Sign up for a free API key at [OpenWeatherMap](https://home.openweathermap.org/users/sign_up).
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Open `.env` and insert your key:
   ```env
   OPENWEATHER_API_KEY=your_actual_api_key_here
   ```
*(You can also set or test your API key directly within the app's Settings tab!)*

---

## 💻 How to Run

### 1. Launch Modern Desktop GUI Dashboard
```bash
python main.py
```
Or launch through the legacy script:
```bash
python "wether app.py" --gui
```

### 2. Launch Local Web Dashboard
```bash
python main.py --web
```
Open [http://localhost:5000](http://localhost:5000) in any browser to access the responsive glassmorphism web station.

### 3. Deploy to Vercel (1-Click Cloud Deployment)
SkyPulse 2.0 exports standard serverless entrypoints (`app`, `application`, `handler`) in `main.py` and `api/index.py` configured via `vercel.json`.
- Connect your GitHub repository (`wether-app`) to [Vercel](https://vercel.com).
- Vercel automatically detects the Python runtime and deploys your live web dashboard instantly!

### 4. Run in CLI Terminal Mode
```bash
# Default city (Hubballi)
python main.py --cli

# Specify any city
python main.py --cli "Tokyo"

# Use Fahrenheit units
python main.py --cli "New York" --units imperial
```

### 3. Run Original Interactive CLI
```bash
python "wether app.py"
```

---

## 🧪 Testing

The project includes an offline unit test suite with 20 tests verifying:
- Weather data parsing (OpenWeatherMap & Open-Meteo)
- Error handling (Invalid city, Network timeout, 401 Unauthorized, 429 Rate limit)
- Unit conversions (°C to °F, °F to °C)
- Cardinal wind direction calculations
- UV Index and Air Quality (AQI) risk categories
- Location manager persistence & duplicate prevention
- Theme registry and fallback mechanisms

To execute all tests:
```bash
python -m unittest discover tests -v
```

---

## 👤 Author & Credits

- **Developer**: [Tejashwini (teju-developer)](https://github.com/teju-developer)
- **Original Repository**: [teju-developer/wether-app](https://github.com/teju-developer/wether-app)
- **Upgrade Release**: SkyPulse Weather Dashboard 2.0
