"""Master dataset loading and geographic/time helpers (M0)."""

import json
import math
from pathlib import Path
from typing import Any

from .config import Config
from .models import City, Place, Transfer

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


def _number(value: Any, field: str, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"Field {field!r} must be a finite number in {context}")
    return float(value)


def _parse_dataset(data: Any) -> tuple[dict[str, City], dict[str, str]]:
    if not isinstance(data, dict):
        raise ValueError("Dataset must be a JSON object")
    schema = _required(data, "schema_version", "dataset")
    if not isinstance(schema, str) or not schema.startswith("2."):
        raise ValueError("Dataset schema_version must start with '2.'")
    categories = _required(data, "categories", "dataset")
    if not isinstance(categories, list) or not categories:
        raise ValueError("Field 'categories' must be a non-empty list")
    labels: dict[str, str] = {}
    for i, category in enumerate(categories):
        context = f"categories[{i}]"
        if not isinstance(category, dict):
            raise ValueError(f"{context} must be an object")
        category_id = _required(category, "id", context)
        label = _required(category, "label", context)
        if not isinstance(category_id, str) or not category_id or not isinstance(label, str) or not label:
            raise ValueError(f"Category id and label must be non-empty strings in {context}")
        if category_id in labels:
            raise ValueError(f"Duplicate category id: {category_id}")
        labels[category_id] = label

    raw_cities = _required(data, "cities", "dataset")
    if not isinstance(raw_cities, list) or not raw_cities:
        raise ValueError("Field 'cities' must be a non-empty list")
    cities: dict[str, City] = {}
    place_ids: set[str] = set()
    for index, raw_city in enumerate(raw_cities):
        context = f"cities[{index}]"
        if not isinstance(raw_city, dict):
            raise ValueError(f"{context} must be an object")
        name = _required(raw_city, "city", context)
        city_id = _required(raw_city, "city_id", context)
        verified = _required(raw_city, "verified", context)
        start = _required(raw_city, "start", context)
        raw_places = _required(raw_city, "places", context)
        if not isinstance(city_id, str) or not city_id:
            raise ValueError(f"city_id must be a non-empty string in {context}")
        if city_id in cities:
            raise ValueError(f"Duplicate city_id: {city_id}")
        if not isinstance(name, str) or not isinstance(verified, bool):
            raise ValueError(f"Invalid city name or verified flag in {context}")
        if not isinstance(start, dict):
            raise ValueError(f"Field 'start' must be an object in {context}")
        start_name = _required(start, "name", f"{context}.start")
        lat = _number(_required(start, "lat", f"{context}.start"), "lat", f"{context}.start")
        lon = _number(_required(start, "lon", f"{context}.start"), "lon", f"{context}.start")
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError(f"Invalid coordinates in {context}.start")
        if not isinstance(raw_places, list):
            raise ValueError(f"Field 'places' must be a list in {context}")
        places: list[Place] = []
        for p_index, item in enumerate(raw_places):
            pctx = f"{context}.places[{p_index}]"
            if not isinstance(item, dict):
                raise ValueError(f"{pctx} must be an object")
            fields = ("id", "name", "lat", "lon", "attraction", "souvenir", "duration_min",
                      "open", "close", "effort", "category", "tags", "area", "location_scope")
            for key in fields:
                _required(item, key, pctx)
            pid, pname = item["id"], item["name"]
            if not isinstance(pid, str) or not pid or not isinstance(pname, str) or not pname:
                raise ValueError(f"Place id and name must be non-empty strings in {pctx}")
            if pid in place_ids:
                raise ValueError(f"Duplicate place id: {pid}")
            place_ids.add(pid)
            plat = _number(item["lat"], "lat", pctx)
            plon = _number(item["lon"], "lon", pctx)
            if not -90 <= plat <= 90 or not -180 <= plon <= 180:
                raise ValueError(f"Invalid coordinates for {pname!r}")
            attraction, souvenir, duration = item["attraction"], item["souvenir"], item["duration_min"]
            if isinstance(attraction, bool) or not isinstance(attraction, int) or not 1 <= attraction <= 10:
                raise ValueError(f"Scores out of range for {pname!r}")
            if isinstance(souvenir, bool) or not isinstance(souvenir, int) or not 0 <= souvenir <= 5:
                raise ValueError(f"Scores out of range for {pname!r}")
            if isinstance(duration, bool) or not isinstance(duration, int) or duration <= 0:
                raise ValueError(f"Duration must be positive for {pname!r}")
            if item["effort"] not in EFFORT_LEVELS:
                raise ValueError(f"Unknown effort label {item['effort']!r} for {pname!r}")
            category = item["category"]
            if category not in labels:
                raise ValueError(f"Unknown category {category!r} for {pname!r}")
            if not isinstance(item["tags"], list) or any(not isinstance(tag, str) for tag in item["tags"]):
                raise ValueError(f"Field 'tags' must be a list of strings for {pname!r}")
            if not isinstance(item["area"], str) or item["location_scope"] not in {"city", "nearby_day_trip"}:
                raise ValueError(f"Invalid area or location_scope for {pname!r}")
            open_min, close_min = to_minutes(item["open"]), to_minutes(item["close"])
            if close_min <= open_min:
                raise ValueError(f"close must be after open for {pname!r}")
            places.append(Place(pid, pname, plat, plon, attraction, souvenir, duration,
                                open_min, close_min, item["effort"], category, item["area"],
                                item["location_scope"], tuple(item["tags"])))
        cities[city_id] = City(city_id, name, (lat, lon), start_name, tuple(places), verified)
    return cities, labels


def _read_json(path: str | Path) -> Any:
    try:
        with open(path, encoding="utf-8") as source:
            return json.load(source)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not load dataset from {path}: {exc}") from exc


def load_dataset(path: str | Path) -> dict[str, City]:
    cities, _ = _parse_dataset(_read_json(path))
    return cities


def load_city(path: str | Path, city_id: str) -> City:
    cities = load_dataset(path)
    try:
        return cities[city_id]
    except KeyError as exc:
        raise ValueError(f"Unknown city_id {city_id!r}") from exc


def intercity(a: City, b: City, cfg: Config) -> Transfer:
    km = haversine_km(a.start, b.start)
    minutes = km / cfg.intercity_speed_kmh * 60 + cfg.intercity_buffer_min
    return Transfer(a.city_id, b.city_id, km, minutes)


def load_categories(path: str | Path) -> dict[str, str]:
    _, labels = _parse_dataset(_read_json(path))
    return labels


def category_pool(
    cities: dict[str, City], labels: dict[str, str], city_ids: list[str]
) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for city_id in city_ids:
        if city_id not in cities:
            raise ValueError(f"Unknown city_id {city_id!r}")
        for place in cities[city_id].places:
            counts[place.category] = counts.get(place.category, 0) + 1
    return [
        {"id": category_id, "label": labels[category_id], "count": count}
        for category_id, count in sorted(counts.items(), key=lambda item: (-item[1], labels[item[0]]))
    ]
