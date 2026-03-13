#!/usr/bin/env python3
"""
Compute activity weather context + wind rose chart from GPS + Open-Meteo (free, no API key).

Usage:
    echo '{"date": "YYYY-MM-DD", "hour": HH, "lats": [...], "lngs": [...]}' | python3 tools/weather.py

Input JSON (stdin):
    date   - activity date, e.g. "2026-03-11"
    hour   - activity start hour (0-23), e.g. 17
    lats   - list of latitude floats from latlng stream (MCP data field)
    lngs   - list of longitude floats from latlng stream (MCP data2 field)

Output JSON (stdout):
    description, average_temp, average_feels_like, average_wind_speed,
    prevailing_wind_deg, prevailing_wind_cardinal, headwind_percent,
    tailwind_percent, avg_yaw, max_rain, max_snow, average_clouds,
    plot_path (PNG wind rose chart, None if matplotlib unavailable)
"""

import json
import math
import sys
import tempfile
import urllib.request
from datetime import date as date_cls


# ── Open-Meteo ────────────────────────────────────────────────────────────────

def get_openmeteo_weather(lat, lng, date_str, hour):
    """Fetch hourly weather from Open-Meteo. Forecast API for ≤5 days ago, archive for older."""
    activity_date = date_cls.fromisoformat(date_str)
    days_ago = (date_cls.today() - activity_date).days

    variables = "temperature_2m,apparent_temperature,windspeed_10m,winddirection_10m,precipitation,snowfall,cloudcover,weathercode"

    if days_ago <= 5:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lng}"
            f"&hourly={variables}"
            f"&past_days={min(days_ago + 1, 5)}&forecast_days=1"
            f"&timezone=auto&wind_speed_unit=kmh"
        )
    else:
        url = (
            f"https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={lat}&longitude={lng}"
            f"&start_date={date_str}&end_date={date_str}"
            f"&hourly={variables}"
            f"&timezone=auto&wind_speed_unit=kmh"
        )

    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())

    hourly = data["hourly"]
    target = f"{date_str}T{hour:02d}:00"
    idx = next((i for i, t in enumerate(hourly["time"]) if t.startswith(target[:13])), 0)

    return {
        "temp": hourly["temperature_2m"][idx],
        "feels_like": hourly["apparent_temperature"][idx],
        "wind_speed": hourly["windspeed_10m"][idx],
        "wind_deg": hourly["winddirection_10m"][idx],
        "precipitation": hourly["precipitation"][idx],
        "snowfall": hourly["snowfall"][idx],
        "clouds": hourly["cloudcover"][idx],
        "weathercode": hourly["weathercode"][idx],
    }


# ── Bearing + headwind math ───────────────────────────────────────────────────

def bearing(lat1, lon1, lat2, lon2):
    """Compass bearing from point 1 → point 2 (degrees, 0=N, 90=E)."""
    d_lon = math.radians(lon2 - lon1)
    lat1, lat2 = math.radians(lat1), math.radians(lat2)
    x = math.sin(d_lon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def is_headwind(travel_bearing, wind_from_deg):
    wind_to = (wind_from_deg + 180) % 360
    angle_diff = abs(((travel_bearing - wind_to + 180) % 360) - 180)
    return angle_diff < 90


def deg_to_cardinal(deg):
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return dirs[round(deg / 22.5) % 16]


def weathercode_to_description(code):
    if code == 0: return "Clear sky"
    if code in (1, 2, 3): return "Partly cloudy" if code < 3 else "Overcast"
    if code in (45, 48): return "Foggy"
    if code in (51, 53, 55): return "Drizzle"
    if code in (61, 63, 65): return "Rain"
    if code in (71, 73, 75): return "Snow"
    if code in (80, 81, 82): return "Rain showers"
    if code in (95, 96, 99): return "Thunderstorm"
    return "Mixed conditions"


# ── Wind rose chart ───────────────────────────────────────────────────────────

def plot_wind_rose(bearings, wind_from_deg, wind_speed, weather, date_str, hour):
    """
    Generate two-panel wind rose chart (matches intervals.icu layout).
    Left:  compass rose — GPS bearing distribution coloured by headwind/tailwind.
    Right: relative rose — bearing relative to wind (headwind at top, tailwind at bottom).
    Returns path to saved PNG, or None if matplotlib is unavailable.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return None

    N = 16
    sector_deg = 360 / N
    wind_to = (wind_from_deg + 180) % 360

    # Bin bearings
    compass_hw = np.zeros(N)   # headwind counts per compass sector
    compass_tw = np.zeros(N)   # tailwind counts per compass sector
    rel_hw = np.zeros(N)       # headwind counts per relative sector
    rel_tw = np.zeros(N)       # tailwind counts per relative sector

    for b in bearings:
        hw = is_headwind(b, wind_from_deg)
        cs = int((b + sector_deg / 2) % 360 / sector_deg) % N
        rel_angle = (b - wind_to) % 360
        rs = int((rel_angle + sector_deg / 2) % 360 / sector_deg) % N
        if hw:
            compass_hw[cs] += 1
            rel_hw[rs] += 1
        else:
            compass_tw[cs] += 1
            rel_tw[rs] += 1

    fig = plt.figure(figsize=(11, 6), facecolor="white")
    fig.suptitle(
        f"{weathercode_to_description(weather['weathercode'])} — "
        f"{weather['feels_like']:.0f}°C feels-like · "
        f"{wind_speed:.0f} km/h {deg_to_cardinal(wind_from_deg)}",
        fontsize=12, fontweight="bold", y=0.97
    )

    GREEN  = "#4CAF50"
    ORANGE = "#FFA726"
    GREY   = "#CCCCCC"

    def polar_rose(ax, hw_counts, tw_counts, title, tick_labels):
        angles = np.radians(np.arange(0, 360, sector_deg))
        width = 2 * np.pi / N * 0.85
        peak = max((hw_counts + tw_counts).max(), 1)

        ax.bar(angles, hw_counts / peak, width=width, color=GREEN,  alpha=0.85, edgecolor="white", linewidth=0.5, label="Headwind")
        ax.bar(angles, tw_counts / peak, width=width, color=ORANGE, alpha=0.85, edgecolor="white", linewidth=0.5,
               bottom=hw_counts / peak, label="Tailwind")

        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.set_xticks(np.radians(np.arange(0, 360, 45)))
        ax.set_xticklabels(tick_labels, fontsize=9)
        ax.set_yticklabels([])
        ax.set_title(title, pad=12, fontsize=10)
        ax.spines["polar"].set_color(GREY)
        ax.grid(color=GREY, linewidth=0.5)

    # Left: compass rose
    ax1 = fig.add_subplot(121, projection="polar")
    polar_rose(ax1, compass_hw, compass_tw, "Route Direction", ["N", "NE", "E", "SE", "S", "SW", "W", "NW"])

    # Mark wind-from direction with an arrow
    arrow_angle = math.radians(wind_from_deg)
    ax1.annotate(
        "", xy=(arrow_angle, 0.15), xytext=(arrow_angle, 0.9),
        xycoords="data", textcoords="data",
        arrowprops=dict(arrowstyle="->", color="navy", lw=1.8),
    )

    # Right: relative rose (headwind at top = 0°)
    hw_pct = round(sum(compass_hw) / max(sum(compass_hw) + sum(compass_tw), 1) * 100)
    tw_pct = 100 - hw_pct
    ax2 = fig.add_subplot(122, projection="polar")
    polar_rose(ax2, rel_hw, rel_tw,
               f"Headwind {hw_pct}%  /  Tailwind {tw_pct}%",
               ["Head", "R", "Tail", "L", "", "", "", ""])

    # Legend + bottom summary
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=GREEN,  alpha=0.85, label="Headwind"),
        plt.Rectangle((0, 0), 1, 1, color=ORANGE, alpha=0.85, label="Tailwind"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=2, fontsize=9,
               frameon=False, bbox_to_anchor=(0.5, 0.01))

    summary_parts = [
        f"Temp {weather['temp']:.0f}°C",
        f"Clouds {weather['clouds']}%",
    ]
    if weather["precipitation"] > 0:
        summary_parts.append(f"Rain {weather['precipitation']:.1f} mm")
    if weather["snowfall"] > 0:
        summary_parts.append(f"Snow {weather['snowfall']:.1f} cm")
    fig.text(0.5, 0.05, "  ·  ".join(summary_parts), ha="center", fontsize=9, color="#555")

    plt.tight_layout(rect=[0, 0.09, 1, 0.94])

    out = tempfile.mktemp(suffix=f"_weather_{date_str}_{hour:02d}h.png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


# ── Core computation ──────────────────────────────────────────────────────────

def compute_weather(date_str, hour, lats, lngs):
    start_lat, start_lng = lats[0], lngs[0]
    print(f"Fetching weather for {date_str} {hour:02d}:00 at {start_lat:.4f},{start_lng:.4f}...", file=sys.stderr)
    weather = get_openmeteo_weather(start_lat, start_lng, date_str, hour)

    wind_from = weather["wind_deg"]
    step = 10
    bearings_list = []
    headwind_count = tailwind_count = 0
    yaw_sum = yaw_count = 0

    for i in range(0, len(lats) - step, step):
        b = bearing(lats[i], lngs[i], lats[i + step], lngs[i + step])
        bearings_list.append(b)
        if is_headwind(b, wind_from):
            headwind_count += 1
        else:
            tailwind_count += 1
        yaw = abs(((b - wind_from + 180) % 360) - 180)
        yaw_sum += yaw
        yaw_count += 1

    total = headwind_count + tailwind_count
    headwind_pct = round(headwind_count / total * 100, 1) if total else 0
    tailwind_pct = round(tailwind_count / total * 100, 1) if total else 0
    avg_yaw = round(yaw_sum / yaw_count, 1) if yaw_count else None

    plot_path = plot_wind_rose(bearings_list, wind_from, weather["wind_speed"], weather, date_str, hour)

    return {
        "description": weathercode_to_description(weather["weathercode"]),
        "average_temp": weather["temp"],
        "average_feels_like": weather["feels_like"],
        "average_wind_speed": weather["wind_speed"],
        "prevailing_wind_deg": wind_from,
        "prevailing_wind_cardinal": deg_to_cardinal(wind_from),
        "headwind_percent": headwind_pct,
        "tailwind_percent": tailwind_pct,
        "avg_yaw": avg_yaw,
        "max_rain": weather["precipitation"],
        "max_snow": weather["snowfall"],
        "average_clouds": weather["clouds"],
        "plot_path": plot_path,
        "source": "open-meteo",
    }


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        inp = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON input: {e}"}))
        sys.exit(1)

    required = {"date", "hour", "lats", "lngs"}
    missing = required - inp.keys()
    if missing:
        print(json.dumps({"error": f"Missing required fields: {missing}"}))
        sys.exit(1)

    lats, lngs = inp["lats"], inp["lngs"]
    if not lats or not lngs:
        print(json.dumps({"error": "No GPS data available for this activity"}))
        sys.exit(1)

    result = compute_weather(inp["date"], inp["hour"], lats, lngs)
    print(json.dumps(result, indent=2))
