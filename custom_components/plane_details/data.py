"""Plain helpers for Plane details, with no Home Assistant in them (tested on their own): reading plane-alert-db,
pairing a Flightradar24 flight with an adsb.lol aircraft, and the record the dashboard reads."""

from __future__ import annotations

import csv
import io
import math
import re
from typing import Any

# plane-alert-db categories counted as people of interest (Ty, 2026-11-03: "celebrities or billionaires etc.").
# "Climate Crisis" is its list of celebrities' and billionaires' private jets. "As Seen on TV" holds more
# celebrities (Travis Scott's E190 crossed the house that day) and TV news helicopters.
POI_CATEGORIES = frozenset(
    {"Climate Crisis", "Don't you know who I am?", "As Seen on TV", "Joe Cool", "Big Hello", "Dictator Alert",
     "Governments"}
)

# adsb.lol dbFlags bits.
FLAG_PIA = 4  # the FAA's Privacy ICAO Address: an anonymous hex, nobody can name the aircraft
FLAG_LADD = 8  # the owner asked the FAA to keep it off public tracking sites (Flightradar24 shows "Blocked")


def parse_alert_db(text: str) -> dict[str, dict[str, Any]]:
    """plane-alert-db's CSV as hex (upper case) -> what it says about the aircraft."""
    out: dict[str, dict[str, Any]] = {}
    for row in csv.DictReader(io.StringIO(text)):
        hexcode = (row.get("$ICAO") or "").strip().upper()
        if not hexcode:
            continue
        category = (row.get("Category") or "").strip()
        tags = [t for t in ((row.get(k) or "").strip() for k in ("$Tag 1", "$#Tag 2", "$#Tag 3")) if t]
        operator = (row.get("$Operator") or "").strip()
        out[hexcode] = {
            "registration": (row.get("$Registration") or "").strip(),
            "name": display_name(operator, tags),
            "operator": operator,
            "category": category,
            "tags": tags,
            "poi": category in POI_CATEGORIES,
        }
    return out


_COMPANY = re.compile(
    r"\b(LLC|L\.L\.C|Inc|Ltd|Limited|Trust|Trustee|Holdings?|Aviation|Air|Corp|Corporation|Company|Co|Leasing|"
    r"Management|Partners|LP|GmbH|SA|AG|Services|Ventures|Capital|Investments?)\b\.?",
    re.IGNORECASE,
)


# Tags that read like names but are the database's jokes or kinds of aircraft.
_NOT_PEOPLE = frozenset(
    {"man made climate change", "climate crisis", "boeing business jet", "do a barrel roll", "pass the sick bag",
     "harvard dropout", "heavy lift"}
)
_PERSON = re.compile(r"[A-Z][\w'.&-]+(?: [A-Z][\w'.&-]+){1,3}")


def display_name(operator: str, tags: list[str]) -> str:
    """Who to name: the operator, unless it is a company (Elon Musk's jet is Falcon Landing LLC's) and a tag names
    someone (two to four capitalised words that aren't one of the database's jokes)."""
    if operator and not _COMPANY.search(operator):
        return operator
    for tag in tags:
        if _PERSON.fullmatch(tag) and tag.lower() not in _NOT_PEOPLE:
            return tag
    return operator or (tags[0] if tags else "")


def km_between(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(min(1.0, h)))


def _num(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def match_aircraft(flight: dict[str, Any], aircraft: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The adsb.lol aircraft that is this Flightradar24 flight.

    By registration, then by callsign; a flight Flightradar24 blocks has neither, so then the nearest aircraft of
    the same type within 15 km (the two sources poll 30 s apart, and a jet covers 7 km a minute), or of any type
    within 3 km.
    """
    reg = (flight.get("aircraft_registration") or "").strip().upper()
    if reg:
        for a in aircraft:
            if (a.get("r") or "").strip().upper() == reg:
                return a
    callsign = (flight.get("callsign") or "").strip().upper()
    if callsign and callsign != "BLOCKED":
        for a in aircraft:
            if (a.get("flight") or "").strip().upper() == callsign:
                return a
    flat, flon = _num(flight.get("latitude")), _num(flight.get("longitude"))
    if flat is None or flon is None:
        return None
    code = (flight.get("aircraft_code") or "").strip().upper()
    best, best_km, best_same = None, 1e9, False
    for a in aircraft:
        alat, alon = _num(a.get("lat")), _num(a.get("lon"))
        if alat is None or alon is None:
            continue
        km = km_between(flat, flon, alat, alon)
        same = bool(code) and (a.get("t") or "").strip().upper() == code
        # A same-type aircraft wins over a closer one of another type.
        if (same and not best_same) or (same == best_same and km < best_km):
            best, best_km, best_same = a, km, same
    if best is None or best_km > (15 if best_same else 3):
        return None
    return best


def record(a: dict[str, Any], owner: dict[str, Any] | None, alert: dict[str, Any] | None, home: tuple[float, float]) -> dict[str, Any]:
    """What the dashboard reads about one aircraft."""
    flags = int(a.get("dbFlags") or 0)
    lat, lon = _num(a.get("lat")), _num(a.get("lon"))
    alt = a.get("alt_baro")
    rec: dict[str, Any] = {
        "hex": (a.get("hex") or "").upper(),
        "registration": (a.get("r") or "").strip(),
        "callsign": (a.get("flight") or "").strip(),
        "type": (a.get("t") or "").strip(),
        "altitude": alt if isinstance(alt, (int, float)) else None,
        "ground_speed": _num(a.get("gs")),
        "latitude": lat,
        "longitude": lon,
        "distance": round(km_between(home[0], home[1], lat, lon), 2) if lat is not None and lon is not None else None,
        "ladd": bool(flags & FLAG_LADD),
        "pia": bool(flags & FLAG_PIA),
        "owner": (owner or {}).get("owner") or "",
        "owner_country": (owner or {}).get("country") or "",
        "poi": bool(alert and alert["poi"]),
        "notable_name": (alert or {}).get("name") or "",
        "notable_operator": (alert or {}).get("operator") or "",
        "notable_category": (alert or {}).get("category") or "",
        "notable_tags": (alert or {}).get("tags") or [],
    }
    if not rec["registration"] and alert and alert.get("registration"):
        rec["registration"] = alert["registration"]
    return rec
