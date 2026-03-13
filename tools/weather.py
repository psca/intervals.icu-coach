#!/usr/bin/env python3
"""
Compute activity weather context from GPS streams + Open-Meteo (free, no API key).

Usage:
    python3 tools/weather.py <activity_id>

Output: JSON matching intervals.icu ActivityWeatherSummary fields:
    description, average_feels_like, average_wind_speed, prevailing_wind_deg,
    headwind_percent, tailwind_percent, max_rain, max_showers, max_snow,
    average_clouds, average_temp
"""

import base64
import json
import math
import os
import sys
import urllib.request
from datetime import datetime, timezone


# ── Auth ──────────────────────────────────────────────────────────────────────

def _auth_header():
    key = os.environ.get("INTERVALS_API_KEY", "")
    if not key:
        raise SystemExit("INTERVALS_API_KEY not set")
    return "Basic " + base64.b64encode(f"API_KEY:{key}".encode()).decode()


def _fetch(url, auth):
    req = urllib.request.Request(url, headers={"Authorization": auth, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


# ── intervals.icu ─────────────────────────────────────────────────────────────

def get_activity(activity_id, auth):
    return _fetch(f"https://intervals.icu/api/v1/activity/{activity_id}", auth)


def get_streams(activity_id, auth):
    streams = _fetch(f"https://intervals.icu/api/v1/activity/{activity_id}/streams", auth)
    result = {}
    for s in streams:
        t = s.get("type")
        if t == "latlng":
            result["lat"] = s["data"]
            result["lng"] = s["data2"]
        elif t == "time":
            result["time"] = s["data"]
    return result


# ── Open-Meteo ────────────────────────────────────────────────────────────────

def get_openmeteo_weather(lat, lng, date_str, hour):
    """
    Fetch hourly weather from Open-Meteo for the given date.
    Uses forecast API (supports past_days=2) for recent activities,
    archive API for older ones.
    """
    from datetime import date as date_cls
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
    times = hourly["time"]

    # Find the index for the activity hour
    target = f"{date_str}T{hour:02d}:00"
    idx = next((i for i, t in enumerate(times) if t.startswith(target[:13])), None)
    if idx is None:
        # fallback: closest hour
        idx = 0

    return {
        "temp": hourly["temperature_2m"][idx],
        "feels_like": hourly["apparent_temperature"][idx],
        "wind_speed": hourly["windspeed_10m"][idx],
        "wind_deg": hourly["winddirection_10m"][idx],  # FROM direction (meteorological)
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


def wind_component(travel_bearing, wind_from_deg):
    """
    Angle between travel direction and wind.
    Returns: 'headwind' if wind is mostly in the face, 'tailwind' otherwise.
    wind_from_deg: the direction the wind is coming FROM.
    wind_to_deg: where the wind is going TO = wind_from_deg + 180.
    """
    wind_to = (wind_from_deg + 180) % 360
    angle_diff = abs(((travel_bearing - wind_to + 180) % 360) - 180)
    return "headwind" if angle_diff < 90 else "tailwind"


def deg_to_cardinal(deg):
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return dirs[round(deg / 22.5) % 16]


def weathercode_to_description(code):
    """WMO weather code to plain English."""
    if code == 0: return "Clear sky"
    if code in (1, 2, 3): return "Partly cloudy" if code < 3 else "Overcast"
    if code in (45, 48): return "Foggy"
    if code in (51, 53, 55): return "Drizzle"
    if code in (61, 63, 65): return "Rain"
    if code in (71, 73, 75): return "Snow"
    if code in (80, 81, 82): return "Rain showers"
    if code in (95, 96, 99): return "Thunderstorm"
    return "Mixed conditions"


# ── Main ──────────────────────────────────────────────────────────────────────

def compute_weather(activity_id):
    auth = _auth_header()

    # 1. Fetch activity for start time + basic info
    activity = get_activity(activity_id, auth)
    start_local = activity.get("start_date_local", "")  # e.g. "2026-03-11T17:03:26"
    dt = datetime.fromisoformat(start_local)
    date_str = dt.strftime("%Y-%m-%d")
    hour = dt.hour

    # 2. Fetch GPS streams
    print(f"Fetching GPS streams for {activity_id}...", file=sys.stderr)
    streams = get_streams(activity_id, auth)
    lats = streams.get("lat", [])
    lngs = streams.get("lng", [])

    if not lats or not lngs:
        return {"error": "No GPS data available for this activity"}

    # Start location for weather lookup
    start_lat, start_lng = lats[0], lngs[0]

    # 3. Fetch weather for the activity hour
    print(f"Fetching weather for {date_str} {hour:02d}:00 at {start_lat:.4f},{start_lng:.4f}...", file=sys.stderr)
    weather = get_openmeteo_weather(start_lat, start_lng, date_str, hour)

    wind_from = weather["wind_deg"]
    wind_speed = weather["wind_speed"]

    # 4. Compute headwind/tailwind from GPS bearings
    headwind_secs = 0
    tailwind_secs = 0
    yaw_sum = 0
    yaw_count = 0

    # Downsample: compute bearing every 10 points to avoid noise
    step = 10
    for i in range(0, len(lats) - step, step):
        b = bearing(lats[i], lngs[i], lats[i + step], lngs[i + step])
        component = wind_component(b, wind_from)
        if component == "headwind":
            headwind_secs += step
        else:
            tailwind_secs += step

        # Yaw = angle between travel bearing and wind direction
        yaw = abs(((b - wind_from + 180) % 360) - 180)
        yaw_sum += yaw
        yaw_count += 1

    total = headwind_secs + tailwind_secs
    headwind_pct = round(headwind_secs / total * 100, 1) if total else 0
    tailwind_pct = round(tailwind_secs / total * 100, 1) if total else 0
    avg_yaw = round(yaw_sum / yaw_count, 1) if yaw_count else None

    # 5. Build output matching ActivityWeatherSummary
    result = {
        "description": weathercode_to_description(weather["weathercode"]),
        "average_temp": weather["temp"],
        "average_feels_like": weather["feels_like"],
        "average_wind_speed": wind_speed,
        "prevailing_wind_deg": wind_from,
        "prevailing_wind_cardinal": deg_to_cardinal(wind_from),
        "headwind_percent": headwind_pct,
        "tailwind_percent": tailwind_pct,
        "avg_yaw": avg_yaw,
        "max_rain": weather["precipitation"],
        "max_showers": 0.0,
        "max_snow": weather["snowfall"],
        "average_clouds": weather["clouds"],
        "source": "open-meteo",
        "activity_date": date_str,
        "activity_hour": hour,
    }

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 tools/weather.py <activity_id>", file=sys.stderr)
        sys.exit(1)

    result = compute_weather(sys.argv[1])
    print(json.dumps(result, indent=2))
