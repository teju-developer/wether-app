"""
Charts Module for SkyPulse Weather Dashboard.
Generates responsive, theme-tailored Matplotlib visualizations embedded seamlessly in CustomTkinter.
"""

import os
import tempfile
# Ensure Matplotlib config uses writable temp directory to avoid Windows sandbox EPERM
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

import matplotlib
matplotlib.use("Agg")  # Use non-GUI backend for rendering to Canvas
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from typing import List, Optional

from app.themes import ThemeColors
from app.weather_service import HourlyForecast, DailyForecast


def style_figure(fig: Figure, ax: plt.Axes, theme: ThemeColors) -> None:
    """Apply consistent glassmorphism theme styling to a matplotlib figure and axis."""
    fig.patch.set_facecolor(theme.chart_bg)
    ax.set_facecolor(theme.chart_bg)

    # Spine colors
    for spine in ax.spines.values():
        spine.set_color(theme.chart_grid)
        spine.set_linewidth(1.0)

    # Tick and label styling
    ax.tick_params(colors=theme.chart_text, labelsize=9)
    ax.xaxis.label.set_color(theme.chart_text)
    ax.yaxis.label.set_color(theme.chart_text)
    ax.title.set_color(theme.text_primary)
    ax.grid(True, linestyle="--", linewidth=0.6, color=theme.chart_grid, alpha=0.6)


def create_hourly_temp_chart(hourly_data: List[HourlyForecast], theme: ThemeColors, units: str = "metric") -> Figure:
    """Create a sleek 24-hour hourly temperature trend chart."""
    fig = Figure(figsize=(7.5, 2.7), dpi=100)
    ax = fig.add_subplot(111)

    if not hourly_data:
        ax.text(0.5, 0.5, "No hourly forecast data available", color=theme.text_secondary, ha="center", va="center")
        style_figure(fig, ax, theme)
        fig.tight_layout()
        return fig

    # Take up to 8-12 points for clean readability
    points = hourly_data[:10]
    times = [item.time_label for item in points]
    temps = [item.temperature for item in points]
    x_indices = np.arange(len(points))

    unit_sym = "°F" if units == "imperial" else "°C"

    # Line plot with smooth styling
    ax.plot(
        x_indices,
        temps,
        color=theme.chart_line,
        linewidth=2.8,
        marker="o",
        markersize=6,
        markerfacecolor=theme.chart_bg,
        markeredgecolor=theme.chart_line,
        markeredgewidth=2.2,
        zorder=4,
    )

    # Gradient-like shaded area under line
    ax.fill_between(
        x_indices,
        temps,
        min(temps) - 3,
        color=theme.chart_line,
        alpha=0.20,
        zorder=3,
    )

    # Add temperature value labels above points
    min_temp = min(temps)
    max_temp = max(temps)
    for i, (x_pos, temp_val) in enumerate(zip(x_indices, temps)):
        is_extreme = temp_val == max_temp or temp_val == min_temp
        fontweight = "bold" if is_extreme else "normal"
        color = theme.accent if temp_val == max_temp else (theme.accent_secondary if temp_val == min_temp else theme.text_primary)
        ax.annotate(
            f"{temp_val:g}{unit_sym}",
            (x_pos, temp_val),
            textcoords="offset points",
            xytext=(0, 9),
            ha="center",
            fontsize=8.5,
            fontweight=fontweight,
            color=color,
        )

    ax.set_xticks(x_indices)
    ax.set_xticklabels(times, rotation=0, fontsize=8.5)
    ax.set_ylim(min_temp - 2.5, max_temp + 3.5)
    ax.set_ylabel(f"Temp ({unit_sym})", fontsize=9)
    ax.set_title("24-Hour Temperature Trajectory", fontsize=11, fontweight="bold", pad=10)

    style_figure(fig, ax, theme)
    fig.tight_layout()
    return fig


def create_weekly_trend_chart(daily_data: List[DailyForecast], theme: ThemeColors, units: str = "metric") -> Figure:
    """Create a 7-day temperature range (High vs Low) visualization."""
    fig = Figure(figsize=(7.5, 2.7), dpi=100)
    ax = fig.add_subplot(111)

    if not daily_data:
        ax.text(0.5, 0.5, "No 7-day forecast data available", color=theme.text_secondary, ha="center", va="center")
        style_figure(fig, ax, theme)
        fig.tight_layout()
        return fig

    days = daily_data[:7]
    labels = [d.day_name.split(",")[0] for d in days]  # e.g. "Mon", "Tue"
    max_temps = [d.temp_max for d in days]
    min_temps = [d.temp_min for d in days]
    x_indices = np.arange(len(days))

    unit_sym = "°F" if units == "imperial" else "°C"

    # High line
    high_color = theme.accent
    ax.plot(
        x_indices,
        max_temps,
        color=high_color,
        linewidth=2.4,
        marker="o",
        markersize=5.5,
        label=f"High ({unit_sym})",
        zorder=4,
    )
    # Low line
    low_color = theme.accent_secondary
    ax.plot(
        x_indices,
        min_temps,
        color=low_color,
        linewidth=2.4,
        linestyle="--",
        marker="s",
        markersize=5,
        label=f"Low ({unit_sym})",
        zorder=4,
    )

    # Shaded band between High and Low
    ax.fill_between(x_indices, min_temps, max_temps, color=high_color, alpha=0.14, zorder=3)

    # Labels
    for i, (x_pos, high_v, low_v) in enumerate(zip(x_indices, max_temps, min_temps)):
        ax.annotate(f"{high_v:g}°", (x_pos, high_v), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8, color=high_color, fontweight="bold")
        ax.annotate(f"{low_v:g}°", (x_pos, low_v), textcoords="offset points", xytext=(0, -14), ha="center", fontsize=8, color=low_color)

    ax.set_xticks(x_indices)
    ax.set_xticklabels(labels, fontsize=9)
    overall_min = min(min_temps) - 3.5
    overall_max = max(max_temps) + 3.5
    ax.set_ylim(overall_min, overall_max)
    ax.set_ylabel(f"Degrees ({unit_sym})", fontsize=9)
    ax.set_title("7-Day Temperature Range (High vs Low)", fontsize=11, fontweight="bold", pad=10)
    ax.legend(loc="upper right", frameon=True, facecolor=theme.bg_card_secondary, edgecolor=theme.border, fontsize=8, labelcolor=theme.text_secondary)

    style_figure(fig, ax, theme)
    fig.tight_layout()
    return fig


def create_rain_and_wind_chart(hourly_data: List[HourlyForecast], theme: ThemeColors) -> Figure:
    """Create a precipitation probability and wind speed dual visualization."""
    fig = Figure(figsize=(7.5, 2.7), dpi=100)
    ax1 = fig.add_subplot(111)

    if not hourly_data:
        ax1.text(0.5, 0.5, "No precipitation data available", color=theme.text_secondary, ha="center", va="center")
        style_figure(fig, ax1, theme)
        fig.tight_layout()
        return fig

    points = hourly_data[:10]
    times = [item.time_label for item in points]
    rain_probs = [item.rain_probability if item.rain_probability is not None else 0 for item in points]
    wind_speeds = [item.wind_speed for item in points]
    x = np.arange(len(points))

    # Bar chart for Rain Probability
    bar_color = theme.accent_secondary
    bars = ax1.bar(x, rain_probs, width=0.45, color=bar_color, alpha=0.65, label="Rain Chance (%)", zorder=3)

    for bar, prob in zip(bars, rain_probs):
        if prob > 0:
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2, f"{prob}%", ha="center", va="bottom", fontsize=7.5, color=theme.text_secondary)

    ax1.set_ylim(0, 115)
    ax1.set_ylabel("Rain Probability (%)", color=bar_color, fontsize=9)
    ax1.set_xticks(x)
    ax1.set_xticklabels(times, fontsize=8.5)
    ax1.set_title("Precipitation Chance & Wind Dynamics", fontsize=11, fontweight="bold", pad=10)

    # Twin axis for Wind Speed
    ax2 = ax1.twinx()
    line_color = theme.accent
    ax2.plot(x, wind_speeds, color=line_color, linewidth=2.2, marker="^", markersize=5, label="Wind Speed", zorder=4)
    max_wind = max(wind_speeds) if wind_speeds else 10
    ax2.set_ylim(0, max(25, max_wind + 5))
    ax2.set_ylabel("Wind Speed (km/h)", color=line_color, fontsize=9)
    ax2.tick_params(colors=theme.chart_text, labelsize=8)
    ax2.spines["right"].set_color(theme.chart_grid)
    ax2.spines["left"].set_color(theme.chart_grid)
    ax2.spines["top"].set_color(theme.chart_grid)
    ax2.spines["bottom"].set_color(theme.chart_grid)

    style_figure(fig, ax1, theme)
    fig.tight_layout()
    return fig
