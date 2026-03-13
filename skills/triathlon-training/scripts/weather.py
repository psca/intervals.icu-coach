#!/usr/bin/env python3
"""
Compute activity weather context from GPS + bearing streams + Open-Meteo (free, no API key).

Usage:
    echo '<json>' | python3 tools/weather.py

Input JSON (stdin):
    date     - activity date, e.g. "2026-03-11"
    hour     - activity start hour (0-23)
    lats     - list of lat floats  (latlng stream, data field)
    lngs     - list of lng floats  (latlng stream, data2 field)
    bearings - list of int degrees (bearing stream, data field); None values skipped

Output JSON (stdout):
    description, average_temp, average_feels_like, average_wind_speed,
    prevailing_wind_deg, prevailing_wind_cardinal, headwind_percent,
    tailwind_percent, avg_yaw, max_rain, max_snow, average_clouds,
    temp_bar (inline ASCII temperature bar), waypoints
"""

import json
import sys
import urllib.request
from datetime import date as date_cls


# ── Open-Meteo ────────────────────────────────────────────────────────────────

def fetch_openmeteo(lat, lng, date_str, hour):
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

SAMPLE_INTERVAL = 1800  # 30 min

def build_waypoints(lats, lngs, date_str, start_hour):
    waypoints = []
    idx = 0
    while idx < len(lats):
        lat, lng = lats[idx], lngs[idx]
        hour = (start_hour + idx // 3600) % 24
        print(f"  waypoint {len(waypoints)+1}: {lat:.4f},{lng:.4f} {hour:02d}:00", file=sys.stderr)
        waypoints.append({
            "idx": idx, "lat": lat, "lng": lng, "hour": hour,
            "weather": fetch_openmeteo(lat, lng, date_str, hour),
        })
        idx += SAMPLE_INTERVAL
    return waypoints


def nearest_weather(waypoints, idx):
    return min(waypoints, key=lambda wp: abs(wp["idx"] - idx))["weather"]


# ── Bearing + headwind math ───────────────────────────────────────────────────

def is_headwind(travel_bearing, wind_from_deg):
    return abs(((travel_bearing - wind_from_deg + 180) % 360) - 180) < 90


def deg_to_cardinal(deg):
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
            "S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return dirs[round(deg / 22.5) % 16]


def weathercode_to_description(code):
    if code == 0:          return "Clear sky"
    if code in (1, 2):     return "Partly cloudy"
    if code == 3:          return "Overcast"
    if code in (45, 48):   return "Foggy"
    if code in (51,53,55): return "Drizzle"
    if code in (61,63,65): return "Rain"
    if code in (71,73,75): return "Snow"
    if code in (80,81,82): return "Rain showers"
    if code in (95,96,99): return "Thunderstorm"
    return "Mixed conditions"


# ── Temperature bar ───────────────────────────────────────────────────────────

def temp_bar(temp, feels_like, width=20):
    """
    Simple inline ASCII bar on a 15–45°C scale.

    Temp       26.8°C  ████████████░░░░░░░░
    Feels like 31.0°C  ████████████████░░░░
    """
    lo, hi = 15, 45

    def bar(val):
        filled = max(0, min(width, round((val - lo) / (hi - lo) * width)))
        return "█" * filled + "░" * (width - filled)

    lines = [
        f"  Temp       {temp:5.1f}°C  {bar(temp)}",
        f"  Feels like {feels_like:5.1f}°C  {bar(feels_like)}",
    ]
    return "\n".join(lines)


# ── Core computation ──────────────────────────────────────────────────────────

def compute_weather(date_str, start_hour, lats, lngs, bearings):
    print(f"Sampling weather every 30 min ({len(lats)} GPS points)...", file=sys.stderr)
    waypoints = build_waypoints(lats, lngs, date_str, start_hour)

    hw_count = tw_count = yaw_sum = 0
    for i, b in enumerate(bearings):
        if b is None:
            continue
        wind_from = nearest_weather(waypoints, i)["wind_deg"]
        if is_headwind(b, wind_from):
            hw_count += 1
        else:
            tw_count += 1
        yaw_sum += abs(((b - wind_from + 180) % 360) - 180)

    total = hw_count + tw_count
    headwind_pct = round(hw_count / total * 100, 1) if total else 0
    tailwind_pct = round(tw_count / total * 100, 1) if total else 0
    avg_yaw      = round(yaw_sum / total, 1) if total else None

    avg_wind_speed = round(sum(wp["weather"]["wind_speed"] for wp in waypoints) / len(waypoints), 1)
    avg_wind_deg   = round(sum(wp["weather"]["wind_deg"]   for wp in waypoints) / len(waypoints), 1)
    avg_temp       = round(sum(wp["weather"]["temp"]       for wp in waypoints) / len(waypoints), 1)
    avg_feels_like = round(sum(wp["weather"]["feels_like"] for wp in waypoints) / len(waypoints), 1)
    avg_clouds     = round(sum(wp["weather"]["clouds"]     for wp in waypoints) / len(waypoints), 1)
    max_rain       = max(wp["weather"]["precipitation"] for wp in waypoints)
    max_snow       = max(wp["weather"]["snowfall"]      for wp in waypoints)
    worst_code     = max(wp["weather"]["weathercode"]   for wp in waypoints)

    return {
        "description":              weathercode_to_description(worst_code),
        "average_temp":             avg_temp,
        "average_feels_like":       avg_feels_like,
        "average_wind_speed":       avg_wind_speed,
        "prevailing_wind_deg":      avg_wind_deg,
        "prevailing_wind_cardinal": deg_to_cardinal(avg_wind_deg),
        "headwind_percent":         headwind_pct,
        "tailwind_percent":         tailwind_pct,
        "avg_yaw":                  avg_yaw,
        "max_rain":                 max_rain,
        "max_snow":                 max_snow,
        "average_clouds":           avg_clouds,
        "temp_bar":                 temp_bar(avg_temp, avg_feels_like),
        "waypoints": [
            {"idx": wp["idx"], "lat": wp["lat"], "lng": wp["lng"],
             "hour": wp["hour"], "wind_speed": wp["weather"]["wind_speed"],
             "wind_deg": wp["weather"]["wind_deg"]}
            for wp in waypoints
        ],
        "source": "open-meteo",
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
