"""
UI Module for SkyPulse Weather Dashboard.
Built with CustomTkinter, featuring glassmorphism aesthetics, dynamic theme switching,
interactive Matplotlib charts, multi-city comparison, and smooth responsive layouts.
"""

import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from typing import Optional, List, Dict, Any
from PIL import Image

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import config
from app.themes import get_theme, ThemeColors, THEMES
from app.locations import LocationManager
from app.forecast import convert_temp
from app.weather_service import (
    WeatherService,
    WeatherData,
    ForecastData,
    WeatherError,
    CityNotFoundError,
    NetworkError,
    InvalidApiKeyError,
    RateLimitError,
)
from app.charts import (
    create_hourly_temp_chart,
    create_weekly_trend_chart,
    create_rain_and_wind_chart,
)

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "weather_icons"


class WeatherDashboardApp(ctk.CTk):
    """Main Application Window for SkyPulse Weather Dashboard."""

    def __init__(self):
        super().__init__()

        # User preferences & service
        self.user_config = config.load_user_config()
        self.current_theme_key = self.user_config.get("theme", "midnight")
        self.theme: ThemeColors = get_theme(self.current_theme_key)
        self.current_units = self.user_config.get("units", "metric")
        self.location_manager = LocationManager()
        self.weather_service = WeatherService()

        # State
        self.current_weather: Optional[WeatherData] = None
        self.current_forecast: Optional[ForecastData] = None
        self.active_city = self.user_config.get("default_city", "Hubballi")
        self.comparison_data: Dict[str, Optional[WeatherData]] = {}
        self.is_loading = False
        self.refresh_timer_id = None
        self.cached_images: Dict[str, ctk.CTkImage] = {}

        # Configure window
        self.title("SkyPulse Weather Dashboard")
        self.geometry("1160x780")
        self.minsize(980, 680)

        # Set CustomTkinter appearance
        ctk.set_appearance_mode("Dark" if self.theme.is_dark else "Light")
        ctk.set_default_color_theme("blue")

        # Layout Setup
        self._setup_layout()
        self._apply_theme()

        # Initial Weather Load in Background Thread
        self.after(200, lambda: self.load_weather(self.active_city))

        # Schedule auto-refresh
        self._schedule_auto_refresh()

    def _get_icon_image(self, icon_key: str, size: tuple = (48, 48)) -> Optional[ctk.CTkImage]:
        """Load and cache CTkImage from assets directory."""
        cache_key = f"{icon_key}_{size[0]}x{size[1]}"
        if cache_key in self.cached_images:
            return self.cached_images[cache_key]

        icon_path = ASSETS_DIR / f"{icon_key}.png"
        if not icon_path.exists():
            icon_path = ASSETS_DIR / "cloudy.png"

        if icon_path.exists():
            try:
                pil_img = Image.open(icon_path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
                self.cached_images[cache_key] = ctk_img
                return ctk_img
            except Exception:
                return None
        return None

    def _setup_layout(self):
        """Construct the complete UI tree."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Top Header Bar
        self.header_frame = ctk.CTkFrame(self, height=70, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self._build_header(self.header_frame)

        # 2. Main Tabview Container
        self.tabview = ctk.CTkTabview(self, corner_radius=14)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=18, pady=(10, 10))

        # Define Tabs
        self.tab_dashboard = self.tabview.add("  Dashboard  ")
        self.tab_charts = self.tabview.add("  Analytics & Charts  ")
        self.tab_forecast = self.tabview.add("  7-Day Forecast  ")
        self.tab_compare = self.tabview.add("  Saved Cities & Compare  ")
        self.tab_settings = self.tabview.add("  Settings  ")

        # Build each tab view
        self._build_dashboard_tab(self.tab_dashboard)
        self._build_charts_tab(self.tab_charts)
        self._build_forecast_tab(self.tab_forecast)
        self._build_compare_tab(self.tab_compare)
        self._build_settings_tab(self.tab_settings)

        # 3. Bottom Status Bar
        self.status_bar = ctk.CTkFrame(self, height=32, corner_radius=0)
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        self._build_status_bar(self.status_bar)

    def _build_header(self, parent):
        """Create header with logo, search box, unit switch, theme selector, and buttons."""
        parent.grid_columnconfigure(2, weight=1)

        # Logo & App Title
        logo_img = self._get_icon_image("app_logo", size=(34, 34))
        self.logo_label = ctk.CTkLabel(
            parent,
            text=" SkyPulse",
            image=logo_img,
            compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=(20, 10), pady=14, sticky="w")

        # Subtitle badge
        self.badge_label = ctk.CTkLabel(
            parent,
            text="PRO",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            corner_radius=6,
            width=36,
            height=20,
        )
        self.badge_label.grid(row=0, column=1, padx=(0, 20), pady=14, sticky="w")

        # Search Bar
        search_container = ctk.CTkFrame(parent, corner_radius=12)
        search_container.grid(row=0, column=2, padx=10, pady=10, sticky="ew")
        search_container.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            search_container,
            placeholder_text="Search city (e.g. London, Hubballi, Tokyo)...",
            height=38,
            border_width=0,
            font=ctk.CTkFont(size=13),
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(12, 6), pady=4)
        self.search_entry.bind("<Return>", lambda e: self._on_search_click())

        self.btn_search = ctk.CTkButton(
            search_container,
            text="Search",
            width=80,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(weight="bold"),
            command=self._on_search_click,
        )
        self.btn_search.grid(row=0, column=1, padx=(4, 6), pady=4)

        # Controls Container (Right)
        ctrl_frame = ctk.CTkFrame(parent, fg_color="transparent")
        ctrl_frame.grid(row=0, column=3, padx=(10, 20), pady=10, sticky="e")

        # Current Location (GPS/IP) Button
        self.btn_location = ctk.CTkButton(
            ctrl_frame,
            text="📍 My Location",
            width=100,
            height=34,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            command=self._on_detect_location_click,
        )
        self.btn_location.pack(side="left", padx=4)

        # Unit Toggle (°C / °F)
        self.unit_segment = ctk.CTkSegmentedButton(
            ctrl_frame,
            values=["°C", "°F"],
            command=self._on_unit_change,
            width=70,
            height=32,
            font=ctk.CTkFont(weight="bold"),
        )
        self.unit_segment.set("°C" if self.current_units == "metric" else "°F")
        self.unit_segment.pack(side="left", padx=4)

        # Theme Selector Dropdown
        self.theme_dropdown = ctk.CTkOptionMenu(
            ctrl_frame,
            values=["Midnight Blue", "Sunset Glow", "Light Sky"],
            command=self._on_theme_select,
            width=125,
            height=32,
            font=ctk.CTkFont(size=12),
        )
        theme_display_map = {"midnight": "Midnight Blue", "sunset": "Sunset Glow", "light": "Light Sky"}
        self.theme_dropdown.set(theme_display_map.get(self.current_theme_key, "Midnight Blue"))
        self.theme_dropdown.pack(side="left", padx=4)

        # Refresh Button
        self.btn_refresh = ctk.CTkButton(
            ctrl_frame,
            text="🔄 Refresh",
            width=85,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            command=lambda: self.load_weather(self.active_city),
        )
        self.btn_refresh.pack(side="left", padx=4)

    def _build_dashboard_tab(self, parent):
        """Construct main dashboard view with hero card, key metrics grid, and hourly forecast ribbon."""
        # Scrollable container for flexible responsiveness
        self.dash_scroll = ctk.CTkScrollableFrame(parent, corner_radius=12)
        self.dash_scroll.pack(fill="both", expand=True, padx=4, pady=4)
        self.dash_scroll.grid_columnconfigure(0, weight=1)

        # 1. Hero Weather Card
        self.hero_card = ctk.CTkFrame(self.dash_scroll, corner_radius=16)
        self.hero_card.grid(row=0, column=0, sticky="ew", padx=8, pady=(4, 14))
        self.hero_card.grid_columnconfigure(1, weight=1)

        # Left: Condition Illustration
        self.hero_icon_label = ctk.CTkLabel(self.hero_card, text="", width=130, height=130)
        self.hero_icon_label.grid(row=0, column=0, rowspan=4, padx=(24, 16), pady=20)

        # Center: Location & Temp
        loc_row = ctk.CTkFrame(self.hero_card, fg_color="transparent")
        loc_row.grid(row=0, column=1, sticky="w", padx=4, pady=(16, 2))

        self.hero_city_label = ctk.CTkLabel(
            loc_row,
            text="Hubballi, IN",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
        )
        self.hero_city_label.pack(side="left")

        # Favorite Star Button
        self.btn_favorite = ctk.CTkButton(
            loc_row,
            text="★ Save",
            width=65,
            height=26,
            corner_radius=13,
            font=ctk.CTkFont(size=11),
            command=self._on_toggle_favorite,
        )
        self.btn_favorite.pack(side="left", padx=(12, 0))

        # Temperature Big Display
        temp_row = ctk.CTkFrame(self.hero_card, fg_color="transparent")
        temp_row.grid(row=1, column=1, sticky="w", padx=4, pady=2)

        self.hero_temp_label = ctk.CTkLabel(
            temp_row,
            text="28°",
            font=ctk.CTkFont(family="Segoe UI", size=54, weight="bold"),
        )
        self.hero_temp_label.pack(side="left")

        self.hero_feels_label = ctk.CTkLabel(
            temp_row,
            text="Feels like 29°",
            font=ctk.CTkFont(family="Segoe UI", size=15),
        )
        self.hero_feels_label.pack(side="left", padx=(14, 0), pady=(18, 0))

        # Condition & Description
        self.hero_condition_label = ctk.CTkLabel(
            self.hero_card,
            text="Partly Cloudy • Scattered clouds with pleasant breeze",
            font=ctk.CTkFont(family="Segoe UI", size=14),
        )
        self.hero_condition_label.grid(row=2, column=1, sticky="w", padx=4, pady=2)

        # Min/Max & Last Updated
        meta_row = ctk.CTkFrame(self.hero_card, fg_color="transparent")
        meta_row.grid(row=3, column=1, sticky="w", padx=4, pady=(2, 16))

        self.hero_high_low_label = ctk.CTkLabel(
            meta_row,
            text="▲ High: 31°   ▼ Low: 21°",
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self.hero_high_low_label.pack(side="left")

        self.hero_updated_label = ctk.CTkLabel(
            meta_row,
            text="•  Last updated: 11:30 AM",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.hero_updated_label.pack(side="left", padx=(12, 0))

        # 2. Key Metrics Grid (8 Cards: 4 columns x 2 rows)
        self.metrics_container = ctk.CTkFrame(self.dash_scroll, fg_color="transparent")
        self.metrics_container.grid(row=1, column=0, sticky="ew", padx=8, pady=6)
        for c in range(4):
            self.metrics_container.grid_columnconfigure(c, weight=1)

        self.metric_cards = {}
        metric_configs = [
            ("humidity", "Humidity", "💧", "humidity"),
            ("wind", "Wind Speed & Dir", "💨", "wind"),
            ("pressure", "Pressure", "⏱", "pressure"),
            ("visibility", "Visibility", "👁", "fog"),
            ("uv", "UV Index", "☀️", "uv"),
            ("aqi", "Air Quality (AQI)", "🍃", "clear_day"),
            ("sun", "Sunrise & Sunset", "🌅", "sunrise"),
            ("rain", "Rain Probability", "🌧️", "rain"),
        ]

        for i, (m_id, title, emoji, icon_name) in enumerate(metric_configs):
            row_idx = i // 4
            col_idx = i % 4
            card = self._create_metric_card(self.metrics_container, title, emoji, icon_name)
            card["frame"].grid(row=row_idx, column=col_idx, padx=6, pady=6, sticky="nsew")
            self.metric_cards[m_id] = card

        # 3. 24-Hour Hourly Forecast Ribbon
        hourly_heading = ctk.CTkLabel(
            self.dash_scroll,
            text="24-Hour Hourly Forecast",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            anchor="w",
        )
        hourly_heading.grid(row=2, column=0, sticky="w", padx=12, pady=(16, 6))

        self.hourly_ribbon = ctk.CTkScrollableFrame(self.dash_scroll, height=140, orientation="horizontal", corner_radius=14)
        self.hourly_ribbon.grid(row=3, column=0, sticky="ew", padx=8, pady=(4, 12))

    def _create_metric_card(self, parent, title: str, emoji: str, icon_name: str) -> dict:
        """Create a stylized glassmorphism metric widget card."""
        frame = ctk.CTkFrame(parent, corner_radius=14, height=105)
        frame.grid_propagate(False)
        frame.grid_columnconfigure(0, weight=1)

        # Header with icon and title
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(8, 2))

        icon_img = self._get_icon_image(icon_name, size=(20, 20))
        icon_lbl = ctk.CTkLabel(header, text="", image=icon_img) if icon_img else ctk.CTkLabel(header, text=emoji)
        icon_lbl.pack(side="left", padx=(0, 6))

        title_lbl = ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            anchor="w",
        )
        title_lbl.pack(side="left")

        # Big Value Label
        val_lbl = ctk.CTkLabel(
            frame,
            text="--",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            anchor="w",
        )
        val_lbl.pack(fill="x", padx=14, pady=2)

        # Subtitle / Category Pill
        sub_lbl = ctk.CTkLabel(
            frame,
            text="--",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            anchor="w",
        )
        sub_lbl.pack(fill="x", padx=14, pady=(0, 8))

        return {
            "frame": frame,
            "title_lbl": title_lbl,
            "val_lbl": val_lbl,
            "sub_lbl": sub_lbl,
            "icon_lbl": icon_lbl,
        }

    def _build_charts_tab(self, parent):
        """Construct Analytics & Charts view with embedded interactive Matplotlib graphs."""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        self.charts_scroll = ctk.CTkScrollableFrame(parent, corner_radius=12)
        self.charts_scroll.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.charts_scroll.grid_columnconfigure(0, weight=1)

        # Chart 1: 24h Temperature Curve
        self.chart_frame_1 = ctk.CTkFrame(self.charts_scroll, corner_radius=14)
        self.chart_frame_1.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.chart_canvas_1: Optional[FigureCanvasTkAgg] = None

        # Chart 2: 7-Day High/Low Range
        self.chart_frame_2 = ctk.CTkFrame(self.charts_scroll, corner_radius=14)
        self.chart_frame_2.grid(row=1, column=0, sticky="ew", padx=8, pady=8)
        self.chart_canvas_2: Optional[FigureCanvasTkAgg] = None

        # Chart 3: Rain & Wind Dynamics
        self.chart_frame_3 = ctk.CTkFrame(self.charts_scroll, corner_radius=14)
        self.chart_frame_3.grid(row=2, column=0, sticky="ew", padx=8, pady=8)
        self.chart_canvas_3: Optional[FigureCanvasTkAgg] = None

    def _build_forecast_tab(self, parent):
        """Construct 7-day extended forecast view with rich cards."""
        self.forecast_scroll = ctk.CTkScrollableFrame(parent, corner_radius=12)
        self.forecast_scroll.pack(fill="both", expand=True, padx=6, pady=6)
        self.forecast_scroll.grid_columnconfigure(0, weight=1)

        self.forecast_card_widgets = []

    def _build_compare_tab(self, parent):
        """Construct Saved Cities and Multi-City Comparison view."""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        # Top Controls: Add City, Refresh All
        ctrl_frame = ctk.CTkFrame(parent, corner_radius=12)
        ctrl_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))

        ctk.CTkLabel(
            ctrl_frame,
            text="Manage Saved Locations & Multi-City Comparison",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
        ).pack(side="left", padx=14, pady=10)

        self.btn_refresh_compare = ctk.CTkButton(
            ctrl_frame,
            text="🔄 Refresh Comparison",
            width=140,
            height=32,
            corner_radius=8,
            command=self._refresh_comparison_view,
        )
        self.btn_refresh_compare.pack(side="right", padx=12, pady=10)

        # Scrollable area for Saved Cities Grid + Comparison Table
        self.compare_scroll = ctk.CTkScrollableFrame(parent, corner_radius=12)
        self.compare_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=6)
        self.compare_scroll.grid_columnconfigure(0, weight=1)

    def _build_settings_tab(self, parent):
        """Construct Settings view: API key config, default city, refresh interval, about."""
        scroll = ctk.CTkScrollableFrame(parent, corner_radius=12)
        scroll.pack(fill="both", expand=True, padx=12, pady=12)
        scroll.grid_columnconfigure(0, weight=1)

        # Section 1: API Configuration
        api_box = ctk.CTkFrame(scroll, corner_radius=14)
        api_box.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        api_box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            api_box,
            text="Weather API Provider & Key Management",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(14, 4))

        ctk.CTkLabel(
            api_box,
            text="SkyPulse operates with high-precision OpenWeatherMap API (when key is provided) "
                 "and includes built-in zero-config Open-Meteo fallback out of the box.",
            font=ctk.CTkFont(size=12),
            wraplength=700,
            justify="left",
        ).grid(row=1, column=0, columnspan=3, sticky="w", padx=16, pady=(0, 12))

        ctk.CTkLabel(api_box, text="OpenWeatherMap API Key:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, sticky="w", padx=(16, 8), pady=8)
        self.settings_key_entry = ctk.CTkEntry(api_box, placeholder_text="Enter your API key or configure in .env...", show="*")
        current_k = config.get_api_key()
        if current_k:
            self.settings_key_entry.insert(0, current_k)
        self.settings_key_entry.grid(row=2, column=1, sticky="ew", padx=8, pady=8)

        btn_save_key = ctk.CTkButton(api_box, text="Save & Test Key", width=120, command=self._on_save_api_key)
        btn_save_key.grid(row=2, column=2, padx=(8, 16), pady=8)

        self.key_status_label = ctk.CTkLabel(api_box, text="", font=ctk.CTkFont(size=12))
        self.key_status_label.grid(row=3, column=0, columnspan=3, sticky="w", padx=16, pady=(0, 12))

        # Section 2: Preferences
        pref_box = ctk.CTkFrame(scroll, corner_radius=14)
        pref_box.grid(row=1, column=0, sticky="ew", padx=8, pady=8)
        pref_box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            pref_box,
            text="Application Preferences",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 12))

        # Default City
        ctk.CTkLabel(pref_box, text="Default City:").grid(row=1, column=0, sticky="w", padx=16, pady=8)
        self.settings_city_entry = ctk.CTkEntry(pref_box)
        self.settings_city_entry.insert(0, self.user_config.get("default_city", "Hubballi"))
        self.settings_city_entry.grid(row=1, column=1, sticky="w", padx=8, pady=8)

        # Auto-refresh Interval
        ctk.CTkLabel(pref_box, text="Auto-Refresh Interval:").grid(row=2, column=0, sticky="w", padx=16, pady=8)
        self.settings_refresh_menu = ctk.CTkOptionMenu(
            pref_box,
            values=["Disabled", "5 Minutes", "15 Minutes", "30 Minutes", "60 Minutes"],
        )
        refresh_min = self.user_config.get("auto_refresh_minutes", 30)
        refresh_map = {0: "Disabled", 5: "5 Minutes", 15: "15 Minutes", 30: "30 Minutes", 60: "60 Minutes"}
        self.settings_refresh_menu.set(refresh_map.get(refresh_min, "30 Minutes"))
        self.settings_refresh_menu.grid(row=2, column=1, sticky="w", padx=8, pady=8)

        btn_save_pref = ctk.CTkButton(pref_box, text="Save Preferences", width=140, command=self._on_save_preferences)
        btn_save_pref.grid(row=3, column=0, columnspan=2, sticky="w", padx=16, pady=(10, 16))

        # Section 3: About & Architecture
        about_box = ctk.CTkFrame(scroll, corner_radius=14)
        about_box.grid(row=2, column=0, sticky="ew", padx=8, pady=8)

        ctk.CTkLabel(
            about_box,
            text="About SkyPulse Weather Dashboard",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 6))

        about_text = (
            "SkyPulse Weather Dashboard 2.0 (Commercial Edition)\n\n"
            "Originally created by Tejashwini (teju-developer) as a Python weather utility, "
            "upgraded into a comprehensive modern desktop weather station featuring:\n"
            "• Dual-engine weather architecture (OpenWeatherMap + Open-Meteo zero-config fallback)\n"
            "• Live 24-hour hourly trend & 7-day extended forecasts\n"
            "• Interactive Matplotlib dark-themed analytical charts\n"
            "• Air Quality Index (AQI), UV Index, Atmospheric Pressure, Visibility, and Wind Dynamics\n"
            "• Dynamic Glassmorphism Theme Engine (Midnight Blue, Sunset Glow, Light Sky)\n"
            "• Multi-city favorites management and side-by-side weather comparison\n\n"
            "GitHub Profile: https://github.com/teju-developer\n"
            "Repository: https://github.com/teju-developer/wether-app"
        )
        ctk.CTkLabel(
            about_box,
            text=about_text,
            font=ctk.CTkFont(size=12),
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 16))

    def _build_status_bar(self, parent):
        """Construct bottom status ribbon."""
        self.status_provider_lbl = ctk.CTkLabel(
            parent,
            text="🟢 Engine: Open-Meteo (Zero-Config)",
            font=ctk.CTkFont(size=11),
        )
        self.status_provider_lbl.pack(side="left", padx=16)

        self.status_msg_lbl = ctk.CTkLabel(
            parent,
            text="Ready",
            font=ctk.CTkFont(size=11),
        )
        self.status_msg_lbl.pack(side="right", padx=16)

    def _apply_theme(self):
        """Apply active theme colors to all dynamic components."""
        theme = self.theme
        ctk.set_appearance_mode("Dark" if theme.is_dark else "Light")

        self.configure(fg_color=theme.bg_window)
        self.header_frame.configure(fg_color=theme.bg_card, border_color=theme.border, border_width=1)
        self.tabview.configure(
            fg_color=theme.bg_window,
            segmented_button_fg_color=theme.bg_card,
            segmented_button_selected_color=theme.accent,
            segmented_button_selected_hover_color=theme.accent_hover,
            segmented_button_unselected_color=theme.bg_card_secondary,
            segmented_button_unselected_hover_color=theme.border,
            text_color=theme.text_primary,
        )
        self.status_bar.configure(fg_color=theme.bg_card, border_color=theme.border, border_width=1)

        # Header controls
        self.logo_label.configure(text_color=theme.accent)
        self.badge_label.configure(fg_color=theme.accent, text_color="#000000" if theme.is_dark else "#FFFFFF")
        self.btn_search.configure(fg_color=theme.accent, text_color="#000000" if theme.is_dark else "#FFFFFF", hover_color=theme.accent_hover)
        self.btn_location.configure(fg_color=theme.bg_card_secondary, text_color=theme.text_primary, hover_color=theme.border)
        self.btn_refresh.configure(fg_color=theme.bg_card_secondary, text_color=theme.text_primary, hover_color=theme.border)

        # Hero Card
        self.hero_card.configure(fg_color=theme.bg_card, border_color=theme.border, border_width=1)
        self.hero_city_label.configure(text_color=theme.text_primary)
        self.hero_temp_label.configure(text_color=theme.accent)
        self.hero_feels_label.configure(text_color=theme.text_secondary)
        self.hero_condition_label.configure(text_color=theme.text_primary)
        self.hero_high_low_label.configure(text_color=theme.text_secondary)
        self.hero_updated_label.configure(text_color=theme.text_muted)

        # Metric Cards
        for m_id, widgets in self.metric_cards.items():
            widgets["frame"].configure(fg_color=theme.bg_card, border_color=theme.border, border_width=1)
            widgets["title_lbl"].configure(text_color=theme.text_secondary)
            widgets["val_lbl"].configure(text_color=theme.text_primary)
            widgets["sub_lbl"].configure(text_color=theme.text_muted)

        # Scroll containers
        self.dash_scroll.configure(fg_color="transparent")
        self.hourly_ribbon.configure(fg_color=theme.bg_card, border_color=theme.border, border_width=1)
        self.charts_scroll.configure(fg_color="transparent")
        self.chart_frame_1.configure(fg_color=theme.bg_card, border_color=theme.border, border_width=1)
        self.chart_frame_2.configure(fg_color=theme.bg_card, border_color=theme.border, border_width=1)
        self.chart_frame_3.configure(fg_color=theme.bg_card, border_color=theme.border, border_width=1)

        # Status Bar
        self.status_provider_lbl.configure(text_color=theme.text_secondary)
        self.status_msg_lbl.configure(text_color=theme.text_muted)

    def load_weather(self, city_name: str):
        """Asynchronously fetch complete weather data for a city."""
        if self.is_loading:
            return
        self.is_loading = True
        self.status_msg_lbl.configure(text=f"Fetching weather for {city_name}...")
        self.btn_refresh.configure(text="⏳ Loading...")

        def worker():
            try:
                w_data, f_data = self.weather_service.get_complete_weather(city_name, units=self.current_units)
                self.after(0, lambda: self._on_weather_success(w_data, f_data))
            except CityNotFoundError as e:
                self.after(0, lambda: self._on_weather_error(f"City '{city_name}' not found. Please verify spelling."))
            except NetworkError as e:
                self.after(0, lambda: self._on_weather_error("Network connection error. Please check your internet."))
            except Exception as e:
                self.after(0, lambda: self._on_weather_error(f"Error: {e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_weather_success(self, w_data: WeatherData, f_data: ForecastData):
        """Update all UI components with newly fetched weather and forecast data."""
        self.is_loading = False
        self.current_weather = w_data
        self.current_forecast = f_data
        self.active_city = w_data.city
        self.btn_refresh.configure(text="🔄 Refresh")

        # Remember in search history
        self.location_manager.add_recent_search(f"{w_data.city}, {w_data.country}".strip(", "))

        # 1. Update Hero Card
        flag_str = f", {w_data.country}" if w_data.country else ""
        self.hero_city_label.configure(text=f"{w_data.city}{flag_str}")
        unit_sym = "°F" if self.current_units == "imperial" else "°C"
        self.hero_temp_label.configure(text=f"{w_data.temperature:g}{unit_sym}")
        self.hero_feels_label.configure(text=f"Feels like {w_data.feels_like:g}{unit_sym}")
        self.hero_condition_label.configure(text=f"{w_data.condition} • {w_data.description}")
        self.hero_high_low_label.configure(text=f"▲ High: {w_data.temp_max:g}{unit_sym}   ▼ Low: {w_data.temp_min:g}{unit_sym}")
        self.hero_updated_label.configure(text=f"•  Updated: {w_data.last_updated}")

        # Hero Icon
        hero_img = self._get_icon_image(w_data.icon_key, size=(110, 110))
        if hero_img:
            self.hero_icon_label.configure(image=hero_img, text="")
        else:
            self.hero_icon_label.configure(image=None, text="⛅")

        # Favorite Star state
        is_fav = self.location_manager.is_saved(w_data.city)
        if is_fav:
            self.btn_favorite.configure(text="★ Saved", fg_color=self.theme.accent, text_color="#000000" if self.theme.is_dark else "#FFFFFF")
        else:
            self.btn_favorite.configure(text="☆ Save", fg_color=self.theme.bg_card_secondary, text_color=self.theme.text_primary)

        # 2. Update Metric Cards
        # Humidity
        hum = w_data.humidity
        hum_cat = "Dry" if hum < 30 else ("Comfortable" if hum <= 60 else "Humid")
        self.metric_cards["humidity"]["val_lbl"].configure(text=f"{hum}%")
        self.metric_cards["humidity"]["sub_lbl"].configure(text=hum_cat)

        # Wind
        speed_unit = "mph" if self.current_units == "imperial" else "km/h"
        self.metric_cards["wind"]["val_lbl"].configure(text=f"{w_data.wind_speed:g} {speed_unit}")
        self.metric_cards["wind"]["sub_lbl"].configure(text=f"{w_data.wind_direction_cardinal} ({int(w_data.wind_direction_deg)}°)")

        # Pressure
        self.metric_cards["pressure"]["val_lbl"].configure(text=f"{w_data.pressure} hPa")
        press_eval = "Normal" if 1000 <= w_data.pressure <= 1025 else ("Low Pressure" if w_data.pressure < 1000 else "High Pressure")
        self.metric_cards["pressure"]["sub_lbl"].configure(text=press_eval)

        # Visibility
        if w_data.visibility_km is not None:
            self.metric_cards["visibility"]["val_lbl"].configure(text=f"{w_data.visibility_km:g} km")
            vis_eval = "Clear" if w_data.visibility_km >= 10 else "Moderate"
            self.metric_cards["visibility"]["sub_lbl"].configure(text=vis_eval)
        else:
            self.metric_cards["visibility"]["val_lbl"].configure(text="10+ km")
            self.metric_cards["visibility"]["sub_lbl"].configure(text="Good Visibility")

        # UV Index
        if w_data.uv_index is not None:
            self.metric_cards["uv"]["val_lbl"].configure(text=f"{w_data.uv_index:g}")
            self.metric_cards["uv"]["sub_lbl"].configure(text=w_data.uv_category, text_color=w_data.uv_color)
        else:
            self.metric_cards["uv"]["val_lbl"].configure(text="N/A")
            self.metric_cards["uv"]["sub_lbl"].configure(text="No UV sensor data", text_color=self.theme.text_muted)

        # Air Quality
        if w_data.aqi is not None:
            self.metric_cards["aqi"]["val_lbl"].configure(text=f"AQI {w_data.aqi}")
            self.metric_cards["aqi"]["sub_lbl"].configure(text=w_data.aqi_category, text_color=w_data.aqi_color)
        else:
            self.metric_cards["aqi"]["val_lbl"].configure(text="Good (28)")
            self.metric_cards["aqi"]["sub_lbl"].configure(text="Clean Air", text_color=self.theme.success)

        # Sunrise & Sunset
        self.metric_cards["sun"]["val_lbl"].configure(text=f"↑ {w_data.sunrise}")
        self.metric_cards["sun"]["sub_lbl"].configure(text=f"↓ {w_data.sunset}")

        # Rain Probability
        pop = w_data.rain_probability if w_data.rain_probability is not None else 0
        self.metric_cards["rain"]["val_lbl"].configure(text=f"{pop}%")
        rain_desc = "Low chance" if pop < 20 else ("Likely showers" if pop > 60 else "Possible rain")
        self.metric_cards["rain"]["sub_lbl"].configure(text=rain_desc)

        # 3. Update Hourly Forecast Ribbon
        self._populate_hourly_ribbon(f_data.hourly)

        # 4. Update Charts
        self._render_charts(f_data)

        # 5. Update 7-Day Forecast Tab
        self._populate_forecast_tab(f_data.daily)

        # 6. Update Status Bar
        prov_icon = "🟢" if w_data.provider == "OpenWeatherMap" else "🔵"
        self.status_provider_lbl.configure(text=f"{prov_icon} Engine: {w_data.provider}")
        self.status_msg_lbl.configure(text=f"Updated successfully at {w_data.last_updated}")

    def _on_weather_error(self, message: str):
        """Handle weather fetching errors gracefully."""
        self.is_loading = False
        self.btn_refresh.configure(text="🔄 Refresh")
        self.status_msg_lbl.configure(text=message, text_color=self.theme.danger)

        # Show notification banner in main dashboard
        banner = ctk.CTkFrame(self.dash_scroll, fg_color=self.theme.danger, corner_radius=10)
        banner.grid(row=0, column=0, sticky="ew", padx=10, pady=8)
        lbl = ctk.CTkLabel(banner, text=f"⚠️ {message}", text_color="#FFFFFF", font=ctk.CTkFont(weight="bold"))
        lbl.pack(side="left", padx=16, pady=8)
        btn_close = ctk.CTkButton(banner, text="✕", width=30, height=24, fg_color="transparent", text_color="#FFFFFF", command=banner.destroy)
        btn_close.pack(side="right", padx=8)

        # Auto dismiss after 6 seconds
        self.after(6000, lambda: banner.destroy() if banner.winfo_exists() else None)

    def _populate_hourly_ribbon(self, hourly_items: List):
        """Render 24-hour horizontal forecast cards."""
        for child in self.hourly_ribbon.winfo_children():
            child.destroy()

        unit_sym = "°F" if self.current_units == "imperial" else "°C"
        for i, item in enumerate(hourly_items[:12]):
            card = ctk.CTkFrame(self.hourly_ribbon, corner_radius=12, width=92, height=120)
            card.grid(row=0, column=i, padx=5, pady=4)
            card.pack_propagate(False)

            # Time
            ctk.CTkLabel(card, text=item.time_label, font=ctk.CTkFont(size=11, weight="bold"), text_color=self.theme.text_secondary).pack(pady=(6, 2))

            # Icon
            c_img = self._get_icon_image(item.icon_key, size=(30, 30))
            if c_img:
                ctk.CTkLabel(card, text="", image=c_img).pack(pady=2)
            else:
                ctk.CTkLabel(card, text="☁️", font=ctk.CTkFont(size=14)).pack(pady=2)

            # Temp
            ctk.CTkLabel(card, text=f"{item.temperature:g}{unit_sym}", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.theme.text_primary).pack(pady=1)

            # Rain pop
            pop_val = item.rain_probability if item.rain_probability is not None else 0
            pop_text = f"💧{pop_val}%" if pop_val > 0 else "•"
            pop_color = self.theme.accent_secondary if pop_val > 0 else self.theme.text_muted
            ctk.CTkLabel(card, text=pop_text, font=ctk.CTkFont(size=10), text_color=pop_color).pack(pady=(0, 4))

    def _render_charts(self, f_data: ForecastData):
        """Render analytical charts in the Analytics & Charts tab."""
        # 1. Hourly Temperature Chart
        fig1 = create_hourly_temp_chart(f_data.hourly, self.theme, units=self.current_units)
        if self.chart_canvas_1 is not None:
            self.chart_canvas_1.get_tk_widget().destroy()
        self.chart_canvas_1 = FigureCanvasTkAgg(fig1, master=self.chart_frame_1)
        self.chart_canvas_1.draw()
        self.chart_canvas_1.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)

        # 2. Weekly Trend Chart
        fig2 = create_weekly_trend_chart(f_data.daily, self.theme, units=self.current_units)
        if self.chart_canvas_2 is not None:
            self.chart_canvas_2.get_tk_widget().destroy()
        self.chart_canvas_2 = FigureCanvasTkAgg(fig2, master=self.chart_frame_2)
        self.chart_canvas_2.draw()
        self.chart_canvas_2.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)

        # 3. Rain & Wind Chart
        fig3 = create_rain_and_wind_chart(f_data.hourly, self.theme)
        if self.chart_canvas_3 is not None:
            self.chart_canvas_3.get_tk_widget().destroy()
        self.chart_canvas_3 = FigureCanvasTkAgg(fig3, master=self.chart_frame_3)
        self.chart_canvas_3.draw()
        self.chart_canvas_3.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)

    def _populate_forecast_tab(self, daily_items: List):
        """Render 7-day extended forecast cards."""
        for child in self.forecast_scroll.winfo_children():
            child.destroy()

        unit_sym = "°F" if self.current_units == "imperial" else "°C"

        for i, item in enumerate(daily_items[:7]):
            card = ctk.CTkFrame(self.forecast_scroll, corner_radius=14, height=72)
            card.pack(fill="x", padx=10, pady=5)
            card.grid_columnconfigure(2, weight=1)

            # Date / Day Name
            day_lbl = ctk.CTkLabel(
                card,
                text=item.day_name,
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                width=130,
                anchor="w",
            )
            day_lbl.grid(row=0, column=0, padx=(18, 8), pady=16)

            # Icon
            c_img = self._get_icon_image(item.icon_key, size=(38, 38))
            icon_lbl = ctk.CTkLabel(card, text="", image=c_img) if c_img else ctk.CTkLabel(card, text="⛅")
            icon_lbl.grid(row=0, column=1, padx=8, pady=16)

            # Condition & Rain Chance
            cond_box = ctk.CTkFrame(card, fg_color="transparent")
            cond_box.grid(row=0, column=2, sticky="w", padx=12, pady=12)

            ctk.CTkLabel(
                cond_box,
                text=item.condition,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color=self.theme.text_primary,
                anchor="w",
            ).pack(anchor="w")

            pop = item.rain_probability if item.rain_probability is not None else 0
            pop_str = f"💧 {pop}% rain probability" if pop > 0 else "Clear skies expected"
            ctk.CTkLabel(
                cond_box,
                text=pop_str,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=self.theme.text_secondary,
                anchor="w",
            ).pack(anchor="w")

            # High / Low Temperature Range
            temp_box = ctk.CTkFrame(card, fg_color="transparent")
            temp_box.grid(row=0, column=3, sticky="e", padx=(8, 20), pady=16)

            ctk.CTkLabel(
                temp_box,
                text=f"{item.temp_max:g}{unit_sym}",
                font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
                text_color=self.theme.accent,
            ).pack(side="left", padx=4)

            ctk.CTkLabel(
                temp_box,
                text=f"/  {item.temp_min:g}{unit_sym}",
                font=ctk.CTkFont(family="Segoe UI", size=14),
                text_color=self.theme.text_secondary,
            ).pack(side="left", padx=4)

    def _refresh_comparison_view(self):
        """Fetch and populate multi-city side-by-side comparison matrix."""
        saved_cities = self.location_manager.get_saved_cities()
        if not saved_cities:
            return

        self.btn_refresh_compare.configure(text="⏳ Comparing...")

        for child in self.compare_scroll.winfo_children():
            child.destroy()

        # Favorites quick-access cards
        fav_header = ctk.CTkLabel(
            self.compare_scroll,
            text="Saved Favorite Locations (Click to View)",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            anchor="w",
        )
        fav_header.pack(fill="x", padx=10, pady=(6, 8))

        fav_container = ctk.CTkFrame(self.compare_scroll, fg_color="transparent")
        fav_container.pack(fill="x", padx=6, pady=4)

        for city in saved_cities:
            card = ctk.CTkFrame(fav_container, corner_radius=10, height=42)
            card.pack(side="left", padx=6, pady=4)

            btn = ctk.CTkButton(
                card,
                text=f"📍 {city}",
                width=110,
                height=32,
                fg_color="transparent",
                text_color=self.theme.text_primary,
                hover_color=self.theme.border,
                command=lambda c=city: self._switch_to_city(c),
            )
            btn.pack(side="left", padx=4)

            btn_del = ctk.CTkButton(
                card,
                text="✕",
                width=24,
                height=24,
                fg_color="transparent",
                text_color=self.theme.text_muted,
                hover_color=self.theme.danger,
                command=lambda c=city: self._remove_favorite_city(c),
            )
            btn_del.pack(side="left", padx=(0, 4))

        # Comparison Table
        table_header = ctk.CTkLabel(
            self.compare_scroll,
            text="Side-by-Side Weather Comparison Matrix",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            anchor="w",
        )
        table_header.pack(fill="x", padx=10, pady=(18, 8))

        table_frame = ctk.CTkFrame(self.compare_scroll, corner_radius=14)
        table_frame.pack(fill="x", padx=6, pady=6)

        # Columns: Metric, City1, City2, City3, ...
        cities_to_compare = saved_cities[:5]
        for col_idx in range(len(cities_to_compare) + 1):
            table_frame.grid_columnconfigure(col_idx, weight=1)

        # Header Row
        ctk.CTkLabel(table_frame, text="Metric", font=ctk.CTkFont(weight="bold"), text_color=self.theme.accent).grid(row=0, column=0, padx=10, pady=10)
        for c_idx, c_name in enumerate(cities_to_compare):
            ctk.CTkLabel(table_frame, text=c_name, font=ctk.CTkFont(weight="bold"), text_color=self.theme.text_primary).grid(row=0, column=c_idx + 1, padx=10, pady=10)

        # Asynchronously fetch comparison data
        def comp_worker():
            results = {}
            for c_name in cities_to_compare:
                try:
                    w_d, _ = self.weather_service.get_complete_weather(c_name, units=self.current_units)
                    results[c_name] = w_d
                except Exception:
                    results[c_name] = None
            self.after(0, lambda: self._fill_comparison_table(table_frame, cities_to_compare, results))

        threading.Thread(target=comp_worker, daemon=True).start()

    def _fill_comparison_table(self, table_frame, cities, results):
        """Populate rows in comparison matrix."""
        self.btn_refresh_compare.configure(text="🔄 Refresh Comparison")
        unit_sym = "°F" if self.current_units == "imperial" else "°C"
        spd_unit = "mph" if self.current_units == "imperial" else "km/h"

        metrics = [
            ("Temperature", lambda w: f"{w.temperature:g}{unit_sym}" if w else "--"),
            ("Condition", lambda w: f"{w.condition}" if w else "--"),
            ("Feels Like", lambda w: f"{w.feels_like:g}{unit_sym}" if w else "--"),
            ("High / Low", lambda w: f"{w.temp_max:g}° / {w.temp_min:g}°" if w else "--"),
            ("Humidity", lambda w: f"{w.humidity}%" if w else "--"),
            ("Wind Speed", lambda w: f"{w.wind_speed:g} {spd_unit}" if w else "--"),
            ("Pressure", lambda w: f"{w.pressure} hPa" if w else "--"),
            ("Air Quality", lambda w: f"{w.aqi_category} ({w.aqi})" if w and w.aqi else "Good"),
            ("UV Index", lambda w: f"{w.uv_category} ({w.uv_index})" if w and w.uv_index else "--"),
        ]

        for r_idx, (m_name, getter) in enumerate(metrics):
            bg_col = self.theme.bg_card_secondary if r_idx % 2 == 0 else "transparent"
            row_f = ctk.CTkFrame(table_frame, fg_color=bg_col, corner_radius=6)
            row_f.grid(row=r_idx + 1, column=0, columnspan=len(cities) + 1, sticky="ew", padx=4, pady=2)
            for c_i in range(len(cities) + 1):
                row_f.grid_columnconfigure(c_i, weight=1)

            ctk.CTkLabel(row_f, text=m_name, font=ctk.CTkFont(size=12, weight="bold"), text_color=self.theme.text_secondary).grid(row=0, column=0, padx=10, pady=8)
            for c_idx, c_name in enumerate(cities):
                w_obj = results.get(c_name)
                val_str = getter(w_obj)
                val_color = self.theme.accent if m_name == "Temperature" else self.theme.text_primary
                ctk.CTkLabel(row_f, text=val_str, font=ctk.CTkFont(size=12), text_color=val_color).grid(row=0, column=c_idx + 1, padx=10, pady=8)

    def _switch_to_city(self, city_name: str):
        """Switch to a saved city and display main dashboard."""
        self.tabview.set("  Dashboard  ")
        self.load_weather(city_name)

    def _remove_favorite_city(self, city_name: str):
        """Remove city from favorites and refresh comparison tab."""
        self.location_manager.remove_saved_city(city_name)
        if self.current_weather and self.current_weather.city.lower() == city_name.lower():
            self.btn_favorite.configure(text="☆ Save", fg_color=self.theme.bg_card_secondary, text_color=self.theme.text_primary)
        self._refresh_comparison_view()

    def _on_toggle_favorite(self):
        """Toggle star favorite for current active city."""
        if not self.current_weather:
            return
        city = self.current_weather.city
        if self.location_manager.is_saved(city):
            self.location_manager.remove_saved_city(city)
            self.btn_favorite.configure(text="☆ Save", fg_color=self.theme.bg_card_secondary, text_color=self.theme.text_primary)
        else:
            self.location_manager.add_saved_city(city)
            self.btn_favorite.configure(text="★ Saved", fg_color=self.theme.accent, text_color="#000000" if self.theme.is_dark else "#FFFFFF")

    def _on_search_click(self):
        """Trigger search from entry box."""
        query = self.search_entry.get().strip()
        if query:
            self.tabview.set("  Dashboard  ")
            self.load_weather(query)

    def _on_detect_location_click(self):
        """Detect location via IP geolocation with explicit user permission prompt."""
        # Confirmation Dialog ensuring user permission
        confirm = tk.messagebox.askyesno(
            "Location Permission",
            "SkyPulse requires permission to estimate your current location via IP geolocation.\n\n"
            "Do you wish to proceed?",
            parent=self,
        )
        if not confirm:
            return

        self.status_msg_lbl.configure(text="Detecting location...")

        def loc_worker():
            try:
                lat, lon, city, country = self.weather_service.detect_current_location()
                self.after(0, lambda: self.load_weather(city))
            except Exception as e:
                self.after(0, lambda: self._on_weather_error(f"Location detection error: {e}"))

        threading.Thread(target=loc_worker, daemon=True).start()

    def _on_unit_change(self, selected_unit_str: str):
        """Switch between Celsius and Fahrenheit."""
        new_units = "metric" if selected_unit_str == "°C" else "imperial"
        if new_units != self.current_units:
            self.current_units = new_units
            config.save_user_config("units", new_units)
            if self.active_city:
                self.load_weather(self.active_city)

    def _on_theme_select(self, theme_display_name: str):
        """Dynamically switch theme across entire app without restarting."""
        mapping = {
            "Midnight Blue": "midnight",
            "Sunset Glow": "sunset",
            "Light Sky": "light",
        }
        theme_key = mapping.get(theme_display_name, "midnight")
        self.current_theme_key = theme_key
        self.theme = get_theme(theme_key)
        config.save_user_config("theme", theme_key)

        self._apply_theme()

        # Re-render active weather data and charts with new theme colors
        if self.current_weather and self.current_forecast:
            self._on_weather_success(self.current_weather, self.current_forecast)

    def _on_save_api_key(self):
        """Save and test OpenWeatherMap API key."""
        key = self.settings_key_entry.get().strip()
        self.key_status_label.configure(text="Testing API key with OpenWeatherMap...", text_color=self.theme.text_secondary)

        def test_worker():
            valid, msg = self.weather_service.test_api_key(key)
            if valid:
                config.set_api_key(key)
                self.after(0, lambda: self.key_status_label.configure(text=f"✅ {msg}", text_color=self.theme.success))
                self.after(500, lambda: self.load_weather(self.active_city))
            else:
                self.after(0, lambda: self.key_status_label.configure(text=f"❌ {msg}", text_color=self.theme.danger))

        threading.Thread(target=test_worker, daemon=True).start()

    def _on_save_preferences(self):
        """Persist default city and auto-refresh interval preferences."""
        new_city = self.settings_city_entry.get().strip()
        if new_city:
            config.save_user_config("default_city", new_city)

        ref_str = self.settings_refresh_menu.get()
        ref_map = {"Disabled": 0, "5 Minutes": 5, "15 Minutes": 15, "30 Minutes": 30, "60 Minutes": 60}
        ref_val = ref_map.get(ref_str, 30)
        config.save_user_config("auto_refresh_minutes", ref_val)

        tk.messagebox.showinfo("Saved", "Your preferences have been saved successfully!", parent=self)
        self._schedule_auto_refresh()

    def _schedule_auto_refresh(self):
        """Schedule automatic periodic background weather refresh."""
        if self.refresh_timer_id is not None:
            self.after_cancel(self.refresh_timer_id)
            self.refresh_timer_id = None

        minutes = config.load_user_config().get("auto_refresh_minutes", 30)
        if minutes > 0:
            interval_ms = minutes * 60 * 1000
            self.refresh_timer_id = self.after(interval_ms, self._on_auto_refresh_tick)

    def _on_auto_refresh_tick(self):
        """Callback for automatic background refresh."""
        if self.active_city:
            self.load_weather(self.active_city)
        self._schedule_auto_refresh()
