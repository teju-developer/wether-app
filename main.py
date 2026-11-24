"""
SkyPulse Weather Dashboard - Universal Desktop & Cloud Web Entry Point.
Exports top-level 'app', 'application', and 'handler' variables for Vercel Serverless deployment,
while supporting native desktop GUI (CustomTkinter) and terminal CLI mode when run locally.
"""

import sys
import os
import json
import tempfile
import argparse
import urllib.parse
from dataclasses import asdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Set writable temp directory for Matplotlib cache
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.weather_service import WeatherService
from app.web_template import get_html_dashboard

weather_service = WeatherService()


def handle_request(path: str, query_params: dict) -> tuple[int, str, bytes]:
    """Shared HTTP router serving web dashboard and JSON API."""
    if path == "/" or path == "/index.html":
        html = get_html_dashboard()
        return 200, "text/html; charset=utf-8", html.encode("utf-8")

    elif path == "/api/weather":
        city = query_params.get("city", ["Hubballi"])[0]
        units = query_params.get("units", ["metric"])[0]
        try:
            w_data, f_data = weather_service.get_complete_weather(city, units=units)
            resp = {
                "weather": asdict(w_data),
                "forecast": {
                    "hourly": [asdict(h) for h in f_data.hourly],
                    "daily": [asdict(d) for d in f_data.daily],
                }
            }
            return 200, "application/json; charset=utf-8", json.dumps(resp).encode("utf-8")
        except Exception as e:
            err = {"error": str(e)}
            return 400, "application/json; charset=utf-8", json.dumps(err).encode("utf-8")

    elif path == "/api/compare":
        cities_raw = query_params.get("cities", ["Hubballi,London,Tokyo"])[0]
        units = query_params.get("units", ["metric"])[0]
        city_list = [c.strip() for c in cities_raw.split(",") if c.strip()][:5]
        results = []
        for c in city_list:
            try:
                w_data, _ = weather_service.get_complete_weather(c, units=units)
                results.append(asdict(w_data))
            except Exception:
                results.append(None)
        resp = {"cities": results}
        return 200, "application/json; charset=utf-8", json.dumps(resp).encode("utf-8")

    return 404, "text/plain; charset=utf-8", b"Not Found"


# 1. WSGI Callable for Vercel, Gunicorn, and standard WSGI servers
def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    qs = environ.get("QUERY_STRING", "")
    query_params = urllib.parse.parse_qs(qs)
    status_code, content_type, body = handle_request(path, query_params)
    status_str = "200 OK" if status_code == 200 else f"{status_code} Error"
    headers = [
        ("Content-Type", content_type),
        ("Content-Length", str(len(body))),
        ("Access-Control-Allow-Origin", "*"),
    ]
    start_response(status_str, headers)
    return [body]


# Standard WSGI alias
application = app


# 2. BaseHTTPRequestHandler for Vercel Python Serverless Runtime
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)
        status_code, content_type, body = handle_request(path, query_params)
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Suppress noisy request logging in serverless
        pass


def run_cli(city: str, units: str = "metric"):
    """Run in terminal CLI mode."""
    print(f"\n==========================================")
    print(f"  SkyPulse Weather Terminal Edition       ")
    print(f"==========================================")
    try:
        w_data, f_data = weather_service.get_complete_weather(city, units=units)
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


def run_web_server(port: int = 5000):
    """Run local HTTP web server."""
    server = HTTPServer(("0.0.0.0", port), handler)
    print(f"\n=======================================================")
    print(f"  SkyPulse Weather Web Dashboard Live!                ")
    print(f"  Local URL: http://localhost:{port}                  ")
    print(f"=======================================================\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down web server...")
        server.server_close()


def run_desktop_gui():
    """Launch native desktop GUI with fallback to web if display is unavailable."""
    try:
        from app.ui import WeatherDashboardApp
        desktop_app = WeatherDashboardApp()
        desktop_app.mainloop()
    except Exception as e:
        print(f"[Notice] Desktop display unavailable ({e}). Starting web dashboard...")
        run_web_server()


def main():
    parser = argparse.ArgumentParser(description="SkyPulse Smart Weather Dashboard")
    parser.add_argument("--cli", "-c", nargs="?", const="Hubballi", help="Run in CLI mode for a specified city")
    parser.add_argument("--web", "-w", action="store_true", help="Launch local web server")
    parser.add_argument("--port", "-p", type=int, default=5000, help="Web server port (default: 5000)")
    parser.add_argument("--units", "-u", choices=["metric", "imperial"], default="metric", help="Temperature units")
    args = parser.parse_args()

    if args.cli is not None:
        run_cli(args.cli, units=args.units)
    elif args.web:
        run_web_server(args.port)
    else:
        run_desktop_gui()


if __name__ == "__main__":
    main()
