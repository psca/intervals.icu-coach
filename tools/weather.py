#!/usr/bin/env python3
"""
Compute activity weather context + wind rose chart.
GPS + bearing data comes from MCP; weather fetched from Open-Meteo (free, no API key).

Usage:
    echo '<json>' | python3 tools/weather.py

Input JSON (stdin):
    date     - activity date, e.g. "2026-03-11"
    hour     - activity start hour (0-23)
    lats     - list of lat floats  (latlng stream, data field)
    lngs     - list of lng floats  (latlng stream, data2 field)
    bearings - list of int degrees (bearing stream, data field); None values are skipped

Output JSON (stdout):
    description, average_temp, average_feels_like, average_wind_speed,
    prevailing_wind_deg, prevailing_wind_cardinal, headwind_percent,
    tailwind_percent, avg_yaw, max_rain, max_snow, average_clouds,
    waypoints (list of per-waypoint weather),
    plot_path (PNG wind rose, None if matplotlib unavailable)
"""

import json
import math
import sys
import tempfile
import urllib.request
from datetime import date as date_cls


# ── Open-Meteo ────────────────────────────────────────────────────────────────

def fetch_openmeteo(lat, lng, date_str, hour):
    """Fetch hourly weather at (lat, lng) for the given date/hour."""
    activity_date = date_cls.fromisoformat(date_str)
    days_ago = (date_cls.today() - activity_date).days
    variables = "temperature_2m,apparent_temperature,windspeed_10m,winddirection_10m,precipitation,snowfall,cloudcover,weathercode"

    if days_ago <= 5:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lng}&hourly={variables}"
            f"&past_days={min(days_ago + 1, 5)}&forecast_days=1"
            f"&timezone=auto&wind_speed_unit=kmh"
        )
    else:
        url = (
            f"https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={lat}&longitude={lng}&start_date={date_str}&end_date={date_str}"
            f"&hourly={variables}&timezone=auto&wind_speed_unit=kmh"
        )

    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())

    h = data["hourly"]
    target = f"{date_str}T{hour:02d}:00"
    idx = next((i for i, t in enumerate(h["time"]) if t.startswith(target[:13])), 0)

    return {
        "temp":          h["temperature_2m"][idx],
        "feels_like":    h["apparent_temperature"][idx],
        "wind_speed":    h["windspeed_10m"][idx],
        "wind_deg":      h["winddirection_10m"][idx],
        "precipitation": h["precipitation"][idx],
        "snowfall":      h["snowfall"][idx],
        "clouds":        h["cloudcover"][idx],
        "weathercode":   h["weathercode"][idx],
    }


# ── Waypoint sampling ─────────────────────────────────────────────────────────

SAMPLE_INTERVAL = 1800  # seconds between weather lookups (30 min)

def build_waypoints(lats, lngs, date_str, start_hour):
    """
    Sample latlng every 30 minutes, fetch Open-Meteo for each waypoint.
    Returns list of {idx, lat, lng, hour, weather} dicts.
    """
    n = len(lats)
    waypoints = []
    idx = 0
    while idx < n:
        lat, lng = lats[idx], lngs[idx]
        elapsed_hours = idx // 3600
        hour = (start_hour + elapsed_hours) % 24
        print(f"  Waypoint {len(waypoints)+1}: idx={idx}, {lat:.4f},{lng:.4f}, hour={hour:02d}:00", file=sys.stderr)
        w = fetch_openmeteo(lat, lng, date_str, hour)
        waypoints.append({"idx": idx, "lat": lat, "lng": lng, "hour": hour, "weather": w})
        idx += SAMPLE_INTERVAL
    return waypoints


def nearest_weather(waypoints, bearing_idx):
    """Return weather dict for the waypoint nearest to bearing_idx."""
    return min(waypoints, key=lambda wp: abs(wp["idx"] - bearing_idx))["weather"]


# ── Bearing + headwind math ───────────────────────────────────────────────────

def is_headwind(travel_bearing, wind_from_deg):
    # Headwind = traveling toward where the wind is coming FROM
    return abs(((travel_bearing - wind_from_deg + 180) % 360) - 180) < 90


def deg_to_cardinal(deg):
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
            "S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return dirs[round(deg / 22.5) % 16]


def weathercode_to_description(code):
    if code == 0:           return "Clear sky"
    if code in (1, 2):      return "Partly cloudy"
    if code == 3:           return "Overcast"
    if code in (45, 48):    return "Foggy"
    if code in (51,53,55):  return "Drizzle"
    if code in (61,63,65):  return "Rain"
    if code in (71,73,75):  return "Snow"
    if code in (80,81,82):  return "Rain showers"
    if code in (95,96,99):  return "Thunderstorm"
    return "Mixed conditions"


# ── Wind rose chart ───────────────────────────────────────────────────────────

def plot_wind_rose(bearing_weather_pairs, waypoints, date_str, start_hour):
    """
    Two-panel wind rose:
      Left:  compass rose — GPS bearing distribution coloured by headwind/tailwind.
      Right: relative rose — bearing relative to wind (headwind at top, tailwind at bottom).
    bearing_weather_pairs: list of (bearing_deg, wind_from_deg)
    Returns PNG path, or None if matplotlib unavailable.
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
    compass_hw = np.zeros(N)
    compass_tw = np.zeros(N)
    rel_hw     = np.zeros(N)
    rel_tw     = np.zeros(N)

    for b, wind_from in bearing_weather_pairs:
        wind_to = (wind_from + 180) % 360
        hw = is_headwind(b, wind_from)
        cs = int((b + sector_deg / 2) % 360 / sector_deg) % N
        rel_angle = (b - wind_to) % 360
        rs = int((rel_angle + sector_deg / 2) % 360 / sector_deg) % N
        if hw:
            compass_hw[cs] += 1
            rel_hw[rs] += 1
        else:
            compass_tw[cs] += 1
            rel_tw[rs] += 1

    # Summary weather from first waypoint for title
    w0 = waypoints[0]["weather"]
    avg_wind_speed = sum(wp["weather"]["wind_speed"] for wp in waypoints) / len(waypoints)
    avg_wind_deg   = sum(wp["weather"]["wind_deg"]   for wp in waypoints) / len(waypoints)

    fig = plt.figure(figsize=(11, 6), facecolor="white")
    fig.suptitle(
        f"{weathercode_to_description(w0['weathercode'])} — "
        f"{w0['feels_like']:.0f}°C feels-like · "
        f"{avg_wind_speed:.0f} km/h {deg_to_cardinal(avg_wind_deg)} (avg)",
        fontsize=12, fontweight="bold", y=0.97,
    )

    GREEN  = "#4CAF50"
    ORANGE = "#FFA726"
    GREY   = "#CCCCCC"

    def polar_rose(ax, hw_counts, tw_counts, title, tick_labels):
        angles = np.radians(np.arange(0, 360, sector_deg))
        width  = 2 * np.pi / N * 0.85
        peak   = max((hw_counts + tw_counts).max(), 1)
        ax.bar(angles, hw_counts / peak, width=width, color=GREEN,  alpha=0.85,
               edgecolor="white", linewidth=0.5)
        ax.bar(angles, tw_counts / peak, width=width, color=ORANGE, alpha=0.85,
               edgecolor="white", linewidth=0.5, bottom=hw_counts / peak)
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.set_xticks(np.radians(np.arange(0, 360, 45)))
        ax.set_xticklabels(tick_labels, fontsize=9)
        ax.set_yticklabels([])
        ax.set_title(title, pad=12, fontsize=10)
        ax.spines["polar"].set_color(GREY)
        ax.grid(color=GREY, linewidth=0.5)

    ax1 = fig.add_subplot(121, projection="polar")
    polar_rose(ax1, compass_hw, compass_tw, "Route Direction",
               ["N","NE","E","SE","S","SW","W","NW"])

    # Average wind-from arrow
    arrow_angle = math.radians(avg_wind_deg)
    ax1.annotate("", xy=(arrow_angle, 0.15), xytext=(arrow_angle, 0.9),
                 arrowprops=dict(arrowstyle="->", color="navy", lw=1.8))

    hw_pct = round(compass_hw.sum() / max(compass_hw.sum() + compass_tw.sum(), 1) * 100)
    ax2 = fig.add_subplot(122, projection="polar")
    polar_rose(ax2, rel_hw, rel_tw,
               f"Headwind {hw_pct}%  /  Tailwind {100-hw_pct}%",
               ["Head","R","Tail","L","","","",""])

    handles = [
        plt.Rectangle((0,0),1,1, color=GREEN,  alpha=0.85, label="Headwind"),
        plt.Rectangle((0,0),1,1, color=ORANGE, alpha=0.85, label="Tailwind"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=2, fontsize=9,
               frameon=False, bbox_to_anchor=(0.5, 0.01))

    summary_parts = [
        f"Temp {w0['temp']:.0f}°C",
        f"Clouds {w0['clouds']}%",
        f"{len(waypoints)} weather samples (30-min intervals)",
    ]
    if w0["precipitation"] > 0:
        summary_parts.append(f"Rain {w0['precipitation']:.1f} mm")
    if w0["snowfall"] > 0:
        summary_parts.append(f"Snow {w0['snowfall']:.1f} cm")
    fig.text(0.5, 0.05, "  ·  ".join(summary_parts), ha="center", fontsize=9, color="#555")

    plt.tight_layout(rect=[0, 0.09, 1, 0.94])
    out = tempfile.mktemp(suffix=f"_weather_{date_str}_{start_hour:02d}h.png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


# ── Core computation ──────────────────────────────────────────────────────────

def compute_weather(date_str, start_hour, lats, lngs, bearings):
    # 1. Build waypoints with 30-min Open-Meteo sampling
    print(f"Sampling weather every 30 min along route ({len(lats)} GPS points)...", file=sys.stderr)
    waypoints = build_waypoints(lats, lngs, date_str, start_hour)

    # 2. Classify each bearing against nearest waypoint's wind
    bearing_weather_pairs = []
    hw_count = tw_count = yaw_sum = 0

    for i, b in enumerate(bearings):
        if b is None:
            continue
        w = nearest_weather(waypoints, i)
        wind_from = w["wind_deg"]
        hw = is_headwind(b, wind_from)
        if hw:
            hw_count += 1
        else:
            tw_count += 1
        yaw_sum += abs(((b - wind_from + 180) % 360) - 180)
        bearing_weather_pairs.append((b, wind_from))

    total = hw_count + tw_count
    headwind_pct = round(hw_count / total * 100, 1) if total else 0
    tailwind_pct = round(tw_count / total * 100, 1) if total else 0
    avg_yaw      = round(yaw_sum / total, 1) if total else None

    # 3. Aggregate weather across waypoints (avg wind, worst-case precip)
    avg_wind_speed = round(sum(wp["weather"]["wind_speed"] for wp in waypoints) / len(waypoints), 1)
    avg_wind_deg   = round(sum(wp["weather"]["wind_deg"]   for wp in waypoints) / len(waypoints), 1)
    avg_temp       = round(sum(wp["weather"]["temp"]       for wp in waypoints) / len(waypoints), 1)
    avg_feels_like = round(sum(wp["weather"]["feels_like"] for wp in waypoints) / len(waypoints), 1)
    avg_clouds     = round(sum(wp["weather"]["clouds"]     for wp in waypoints) / len(waypoints), 1)
    max_rain       = max(wp["weather"]["precipitation"] for wp in waypoints)
    max_snow       = max(wp["weather"]["snowfall"]      for wp in waypoints)
    worst_code     = max(wp["weather"]["weathercode"]   for wp in waypoints)

    # 4. Chart
    plot_path = plot_wind_rose(bearing_weather_pairs, waypoints, date_str, start_hour)

    return {
        "description":            weathercode_to_description(worst_code),
        "average_temp":           avg_temp,
        "average_feels_like":     avg_feels_like,
        "average_wind_speed":     avg_wind_speed,
        "prevailing_wind_deg":    avg_wind_deg,
        "prevailing_wind_cardinal": deg_to_cardinal(avg_wind_deg),
        "headwind_percent":       headwind_pct,
        "tailwind_percent":       tailwind_pct,
        "avg_yaw":                avg_yaw,
        "max_rain":               max_rain,
        "max_snow":               max_snow,
        "average_clouds":         avg_clouds,
        "waypoints":              [
            {"idx": wp["idx"], "lat": wp["lat"], "lng": wp["lng"],
             "hour": wp["hour"], "wind_speed": wp["weather"]["wind_speed"],
             "wind_deg": wp["weather"]["wind_deg"]}
            for wp in waypoints
        ],
        "plot_path": plot_path,
        "source":    "open-meteo",
    }


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        inp = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON input: {e}"}))
        sys.exit(1)

    missing = {"date", "hour", "lats", "lngs", "bearings"} - inp.keys()
    if missing:
        print(json.dumps({"error": f"Missing fields: {missing}"}))
        sys.exit(1)

    lats, lngs, bearings = inp["lats"], inp["lngs"], inp["bearings"]
    if not lats or not lngs:
        print(json.dumps({"error": "No GPS data available for this activity"}))
        sys.exit(1)

    result = compute_weather(inp["date"], inp["hour"], lats, lngs, bearings)
    print(json.dumps(result, indent=2))
