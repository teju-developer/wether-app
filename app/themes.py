"""
Themes Module for SkyPulse Weather Dashboard.
Supports dynamic switching across Midnight Blue, Sunset, and Light Sky themes.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ThemeColors:
    name: str
    display_name: str
    bg_window: str
    bg_card: str
    bg_card_secondary: str
    bg_input: str
    border: str
    border_accent: str
    text_primary: str
    text_secondary: str
    text_muted: str
    accent: str
    accent_hover: str
    accent_secondary: str
    success: str
    warning: str
    danger: str
    chart_bg: str
    chart_text: str
    chart_line: str
    chart_secondary_line: str
    chart_grid: str
    is_dark: bool


THEMES: Dict[str, ThemeColors] = {
    "midnight": ThemeColors(
        name="midnight",
        display_name="Midnight Blue",
        bg_window="#0B132B",
        bg_card="#1C2541",
        bg_card_secondary="#232F52",
        bg_input="#141E38",
        border="#2E3B5E",
        border_accent="#38BDF8",
        text_primary="#F8FAFC",
        text_secondary="#94A3B8",
        text_muted="#64748B",
        accent="#00F0FF",
        accent_hover="#00D2E0",
        accent_secondary="#38BDF8",
        success="#10B981",
        warning="#F59E0B",
        danger="#EF4444",
        chart_bg="#1C2541",
        chart_text="#94A3B8",
        chart_line="#00F0FF",
        chart_secondary_line="#38BDF8",
        chart_grid="#2A3757",
        is_dark=True,
    ),
    "sunset": ThemeColors(
        name="sunset",
        display_name="Sunset Glow",
        bg_window="#1E112A",
        bg_card="#2E1A40",
        bg_card_secondary="#3D2455",
        bg_input="#261536",
        border="#4F2B6E",
        border_accent="#FF6B6B",
        text_primary="#FFF5FA",
        text_secondary="#D4B8E5",
        text_muted="#9F7EB2",
        accent="#FF6B6B",
        accent_hover="#FA5252",
        accent_secondary="#FFA07A",
        success="#20C997",
        warning="#FCC419",
        danger="#FF6B6B",
        chart_bg="#2E1A40",
        chart_text="#D4B8E5",
        chart_line="#FF6B6B",
        chart_secondary_line="#FFA07A",
        chart_grid="#472863",
        is_dark=True,
    ),
    "light": ThemeColors(
        name="light",
        display_name="Light Sky",
        bg_window="#F1F5F9",
        bg_card="#FFFFFF",
        bg_card_secondary="#F8FAFC",
        bg_input="#E2E8F0",
        border="#CBD5E1",
        border_accent="#0284C7",
        text_primary="#0F172A",
        text_secondary="#475569",
        text_muted="#94A3B8",
        accent="#0284C7",
        accent_hover="#0369A1",
        accent_secondary="#38BDF8",
        success="#059669",
        warning="#D97706",
        danger="#DC2626",
        chart_bg="#FFFFFF",
        chart_text="#475569",
        chart_line="#0284C7",
        chart_secondary_line="#38BDF8",
        chart_grid="#E2E8F0",
        is_dark=False,
    ),
}


def get_theme(name: str) -> ThemeColors:
    """Retrieve theme colors by identifier with fallback to midnight."""
    return THEMES.get(name.lower(), THEMES["midnight"])


def get_theme_names() -> list[str]:
    """Get list of supported theme identifiers."""
    return list(THEMES.keys())
