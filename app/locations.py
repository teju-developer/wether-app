"""
Locations Module for SkyPulse Weather Dashboard.
Manages saved favorite locations and recent search history with local JSON persistence.
"""

import json
from pathlib import Path
from typing import List


class LocationManager:
    """Handles saved favorite cities and recent searches."""

    DEFAULT_SAVED = ["Hubballi", "Bengaluru", "New York", "London", "Tokyo"]

    def __init__(self, storage_path: Path = None):
        if storage_path is None:
            storage_path = Path(__file__).resolve().parent.parent / "saved_locations.json"
        self.storage_path = storage_path
        self._data = {"saved_cities": self.DEFAULT_SAVED.copy(), "recent_searches": []}
        self.load()

    def load(self) -> None:
        """Load saved locations and recent searches from JSON file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if isinstance(content, dict):
                        saved = content.get("saved_cities", [])
                        if isinstance(saved, list) and saved:
                            self._data["saved_cities"] = [str(c).strip() for c in saved if str(c).strip()]
                        recent = content.get("recent_searches", [])
                        if isinstance(recent, list):
                            self._data["recent_searches"] = [str(c).strip() for c in recent if str(c).strip()][:10]
            except Exception:
                pass

    def save(self) -> None:
        """Persist state to JSON file."""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4)
        except Exception:
            pass

    def get_saved_cities(self) -> List[str]:
        """Return list of saved city names."""
        return list(self._data["saved_cities"])

    def add_saved_city(self, city_name: str) -> bool:
        """Add a city to favorites if not already present."""
        clean = city_name.strip()
        if not clean:
            return False
        # Case-insensitive duplicate check
        for c in self._data["saved_cities"]:
            if c.lower() == clean.lower():
                return False
        self._data["saved_cities"].append(clean)
        self.save()
        return True

    def remove_saved_city(self, city_name: str) -> bool:
        """Remove a city from favorites."""
        clean = city_name.strip().lower()
        initial_len = len(self._data["saved_cities"])
        self._data["saved_cities"] = [c for c in self._data["saved_cities"] if c.lower() != clean]
        if len(self._data["saved_cities"]) != initial_len:
            self.save()
            return True
        return False

    def is_saved(self, city_name: str) -> bool:
        """Check if city is in saved favorites."""
        clean = city_name.strip().lower()
        return any(c.lower() == clean for c in self._data["saved_cities"])

    def get_recent_searches(self) -> List[str]:
        """Return list of recent searches."""
        return list(self._data["recent_searches"])

    def add_recent_search(self, city_name: str) -> None:
        """Prepend search query to recent searches without duplicates."""
        clean = city_name.strip()
        if not clean:
            return
        # Remove if already exists
        recents = [c for c in self._data["recent_searches"] if c.lower() != clean.lower()]
        recents.insert(0, clean)
        self._data["recent_searches"] = recents[:8]
        self.save()

    def clear_recent_searches(self) -> None:
        """Clear recent searches."""
        self._data["recent_searches"] = []
        self.save()
