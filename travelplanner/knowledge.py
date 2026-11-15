"""City data loading and geographic/time helpers."""

import json
import math
from pathlib import Path
from typing import Any

from .models import Place

EARTH_RADIUS_KM = 6371.0
EFFORT_LEVELS = {"low", "medium", "high"}


def to_minutes(hhmm: str) -> int:
    try:
        hour_text, minute_text = hhmm.split(":")
        hour, minute = int(hour_text), int(minute_text)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid time {hhmm!r}; expected HH:MM") from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"Invalid time {hhmm!r}; expected a valid 24-hour time")
    return hour * 60 + minute


def to_clock(minutes: float) -> str:
    rounded = math.floor(minutes + 0.5) % (24 * 60)
    return f"{rounded // 60:02d}:{rounded % 60:02d}"


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def travel_min(
    a: tuple[float, float], b: tuple[float, float], speed_kmh: float, factor: float = 1.0
) -> float:
    if speed_kmh <= 0 or factor <= 0:
        raise ValueError("speed_kmh and factor must be positive")
    return haversine_km(a, b) / speed_kmh * 60 * factor


def _required(mapping: dict[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise ValueError(f"Missing required field {key!r} in {context}")
    return mapping[key]


def load_city(path: str | Path) -> tuple[dict[str, Any], list[Place]]:
    try:
        with open(path, encoding="utf-8") as city_file:
            data = json.load(city_file)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not load city data from {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("City data must be a JSON object")
    city = _required(data, "city", "city data")
    verified = _required(data, "verified", "city data")
    start = _required(data, "start", "city data")
    if not isinstance(start, dict):
        raise ValueError("Field 'start' must be an object")
    for key in ("name", "lat", "lon"):
        _required(start, key, "start")
    raw_places = _required(data, "places", "city data")
    if not isinstance(raw_places, list):
        raise ValueError("Field 'places' must be a list")
    meta = {"city": city, "verified": bool(verified), "start": start}
    places: list[Place] = []
    names: set[str] = set()
    for index, item in enumerate(raw_places):
        context = f"places[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{context} must be an object")
        fields = ("name", "lat", "lon", "attraction", "souvenir", "duration_min", "open", "close", "effort")
        for key in fields:
            _required(item, key, context)
        name = item["name"]
        if name in names:
            raise ValueError(f"Duplicate place name: {name}")
        names.add(name)
        if not 1 <= item["attraction"] <= 10 or not 0 <= item["souvenir"] <= 5:
            raise ValueError(f"Scores out of range for {name!r}")
        if item["effort"] not in EFFORT_LEVELS:
            raise ValueError(f"Unknown effort label {item['effort']!r} for {name!r}")
        open_min, close_min = to_minutes(item["open"]), to_minutes(item["close"])
        if close_min <= open_min:
            raise ValueError(f"close must be after open for {name!r}")
        places.append(Place(
            name=name, lat=float(item["lat"]), lon=float(item["lon"]),
            attraction=int(item["attraction"]), souvenir=int(item["souvenir"]),
            duration_min=int(item["duration_min"]), open_min=open_min, close_min=close_min,
            effort=item["effort"], tags=tuple(item.get("tags", ())),
        ))
    return meta, places
