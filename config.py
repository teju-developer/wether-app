import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()

# Config file for persisted user preferences
CONFIG_FILE = BASE_DIR / "user_config.json"

DEFAULT_SETTINGS = {
    "default_city": "Hubballi",
    "units": "metric",            # "metric" (°C) or "imperial" (°F)
    "theme": "midnight",          # "midnight", "sunset", "light"
    "auto_refresh_minutes": 30,   # 0 to disable
    "api_provider": "auto",       # "auto", "openweathermap", "openmeteo"
}


def load_user_config() -> dict:
    """Load persisted user preferences from user_config.json."""
    config = DEFAULT_SETTINGS.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    config.update(saved)
        except Exception:
            pass
    return config


def save_user_config(key: str, value) -> None:
    """Save a preference key/value to user_config.json."""
    config = load_user_config()
    config[key] = value
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception:
        pass


def get_api_key() -> str:
    """Retrieve the OpenWeatherMap API key from environment or user config."""
    # Check environment variable first
    api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if not api_key:
        user_config = load_user_config()
        api_key = user_config.get("api_key", "").strip()
    return api_key


def set_api_key(key: str) -> None:
    """Persist the API key to user config."""
    save_user_config("api_key", key.strip())
