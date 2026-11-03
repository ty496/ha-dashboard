"""Place lookup and forecast shaping for Open-Meteo. No Home Assistant imports, so it can be tested alone.

A place name is matched against Open-Meteo's geocoder. "Vail" alone means the nearest Vail (within NEAR_MILES of
home, the most populous one there), so local names don't land in another state; "Vail, Arizona" or "Paris, France"
picks by the qualifier; with no nearby match the geocoder's own first result (usually the best-known) wins.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone, tzinfo
from math import asin, cos, radians, sin, sqrt
from typing import Any

NEAR_MILES = 350

STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado",
    "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia",
    "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}

# WMO weather interpretation codes, as Open-Meteo reports them.
WMO = {
    0: "clear", 1: "mostly clear", 2: "partly cloudy", 3: "overcast", 45: "fog", 48: "freezing fog",
    51: "light drizzle", 53: "drizzle", 55: "heavy drizzle", 56: "light freezing drizzle", 57: "freezing drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain", 66: "light freezing rain", 67: "freezing rain",
    71: "light snow", 73: "snow", 75: "heavy snow", 77: "snow grains", 80: "light showers", 81: "showers",
    82: "heavy showers", 85: "light snow showers", 86: "snow showers", 95: "thunderstorms",
    96: "thunderstorms with hail", 99: "thunderstorms with heavy hail",
}

# The same codes as Home Assistant's weather conditions, for the weather entity behind the pop-up.
HA_CONDITIONS = {
    0: "sunny", 1: "sunny", 2: "partlycloudy", 3: "cloudy", 45: "fog", 48: "fog", 51: "rainy", 53: "rainy",
    55: "rainy", 56: "snowy-rainy", 57: "snowy-rainy", 61: "rainy", 63: "rainy", 65: "pouring",
    66: "snowy-rainy", 67: "snowy-rainy", 71: "snowy", 73: "snowy", 75: "snowy", 77: "snowy", 80: "rainy",
    81: "rainy", 82: "pouring", 85: "snowy", 86: "snowy", 95: "lightning-rainy", 96: "lightning-rainy",
    99: "lightning-rainy",
}


def miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    a = sin(radians(lat2 - lat1) / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(radians(lon2 - lon1) / 2) ** 2
    return 2 * 3958.8 * asin(sqrt(a))


def split_place(place: str) -> tuple[str, list[str]]:
    """'Vail, CO' -> ('Vail', ['colorado']); 'Paris France' stays one name (the geocoder handles words)."""
    parts = [p.strip() for p in place.split(",") if p.strip()]
    name, quals = parts[0], []
    for q in parts[1:]:
        quals.append(STATES.get(q.upper(), q).lower())
    return name, quals


def label(r: dict[str, Any]) -> str:
    bits = [r.get("name"), r.get("admin1"), r.get("country") or r.get("country_code")]
    return ", ".join(dict.fromkeys(b for b in bits if b))


def short_label(r: dict[str, Any]) -> str:
    """'Vail, Colorado' in the US, 'Paris, France' abroad: short enough for a card's header."""
    second = r.get("admin1") if r.get("country_code") == "US" else r.get("country")
    return ", ".join(dict.fromkeys(b for b in (r.get("name"), second) if b))


def choose(results: list[dict[str, Any]], quals: list[str], home: tuple[float, float]) -> dict[str, Any] | None:
    if not results:
        return None
    if quals:
        def fits(r: dict[str, Any]) -> bool:
            names = {str(r.get(k, "")).lower() for k in ("admin1", "admin2", "country", "country_code")}
            return all(any(q == n or q in n for n in names if n) for q in quals)

        fitting = [r for r in results if fits(r)]
        return fitting[0] if fitting else None
    near = [r for r in results if miles(home[0], home[1], r["latitude"], r["longitude"]) <= NEAR_MILES]
    if near:
        return max(near, key=lambda r: (r.get("population") or 0, -miles(home[0], home[1], r["latitude"], r["longitude"])))
    return results[0]


def conditions(code: Any) -> str:
    try:
        return WMO.get(int(code), "unknown")
    except (TypeError, ValueError):
        return "unknown"


def ha_condition(code: Any, is_day: Any = 1) -> str | None:
    try:
        cond = HA_CONDITIONS.get(int(code))
    except (TypeError, ValueError):
        return None
    return "clear-night" if cond == "sunny" and is_day == 0 else cond


def card_data(
    fc: dict[str, Any], home_tz: tzinfo, hours: int = 24
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Open-Meteo's answer as a weather entity's current state and its hourly and daily forecasts.

    Hours keep their true instant, so a card shows them on the home's clock. Days go at noon of the same
    date in the home's time zone, so a day in Tokyo isn't labelled with the day before.
    """
    off = timedelta(seconds=fc.get("utc_offset_seconds") or 0)

    def instant(local: str) -> str:
        return (datetime.fromisoformat(local) - off).replace(tzinfo=timezone.utc).isoformat()

    def col(src: dict[str, Any], key: str, i: int) -> Any:
        vals = src.get(key) or []
        return vals[i] if i < len(vals) else None

    cur = fc.get("current") or {}
    now = {
        "condition": ha_condition(cur.get("weather_code"), cur.get("is_day", 1)),
        "temperature": cur.get("temperature_2m"),
        "apparent": cur.get("apparent_temperature"),
        "humidity": cur.get("relative_humidity_2m"),
        "wind": cur.get("wind_speed_10m"),
        "gusts": cur.get("wind_gusts_10m"),
        "bearing": cur.get("wind_direction_10m"),
        "pressure": cur.get("pressure_msl"),
    }
    hourly = fc.get("hourly") or {}
    times = hourly.get("time", [])
    start = 0
    if cur.get("time") and times:
        start = next((i for i, t in enumerate(times) if t >= cur["time"][:13]), 0)
    by_hour = [
        {
            "datetime": instant(times[i]),
            "condition": ha_condition(col(hourly, "weather_code", i), col(hourly, "is_day", i)),
            "native_temperature": col(hourly, "temperature_2m", i),
            "precipitation_probability": col(hourly, "precipitation_probability", i),
        }
        for i in range(start, min(start + hours, len(times)))
    ]
    daily = fc.get("daily") or {}
    by_day = [
        {
            "datetime": datetime.combine(date.fromisoformat(day), time(12), home_tz).isoformat(),
            "condition": ha_condition(col(daily, "weather_code", i)),
            "native_temperature": col(daily, "temperature_2m_max", i),
            "native_templow": col(daily, "temperature_2m_min", i),
            "precipitation_probability": col(daily, "precipitation_probability_max", i),
            "native_precipitation": col(daily, "precipitation_sum", i),
            "native_wind_speed": col(daily, "wind_speed_10m_max", i),
        }
        for i, day in enumerate(daily.get("time", []))
    ]
    return now, by_hour, by_day


def shape(place: str, fc: dict[str, Any], hours: int = 12) -> dict[str, Any]:
    """Trim Open-Meteo's forecast to what a spoken answer needs (°F, mph, inches)."""
    out: dict[str, Any] = {"place": place, "source": "Open-Meteo", "units": "°F, mph, inches"}
    if (elev := fc.get("elevation")) is not None:
        out["elevation_ft"] = round(elev * 3.28084)
    cur = fc.get("current") or {}
    if cur:
        out["now"] = {
            "time": cur.get("time"),
            "conditions": conditions(cur.get("weather_code")),
            "temperature": cur.get("temperature_2m"),
            "feels_like": cur.get("apparent_temperature"),
            "humidity": cur.get("relative_humidity_2m"),
            "wind": cur.get("wind_speed_10m"),
            "gusts": cur.get("wind_gusts_10m"),
            "precipitation": cur.get("precipitation"),
            "snowfall": cur.get("snowfall"),
        }
    daily = fc.get("daily") or {}
    days = []
    for i, day in enumerate(daily.get("time", [])):
        def pick(key: str) -> Any:
            vals = daily.get(key) or []
            return vals[i] if i < len(vals) else None

        days.append(
            {
                "date": day,
                "conditions": conditions(pick("weather_code")),
                "high": pick("temperature_2m_max"),
                "low": pick("temperature_2m_min"),
                "precip_chance": pick("precipitation_probability_max"),
                "precipitation": pick("precipitation_sum"),
                "snowfall": pick("snowfall_sum"),
                "wind_max": pick("wind_speed_10m_max"),
            }
        )
    out["days"] = days
    hourly = fc.get("hourly") or {}
    start = 0
    times = hourly.get("time", [])
    if cur.get("time") and times:
        start = next((i for i, t in enumerate(times) if t >= cur["time"][:13]), 0)
    out["next_hours"] = [
        {
            "time": times[i],
            "temperature": (hourly.get("temperature_2m") or [None] * len(times))[i],
            "precip_chance": (hourly.get("precipitation_probability") or [None] * len(times))[i],
            "conditions": conditions((hourly.get("weather_code") or [None] * len(times))[i]),
        }
        for i in range(start, min(start + hours, len(times)))
    ]
    return out
