import json
from pathlib import Path

import pytest

from travelplanner.config import Config
from travelplanner.knowledge import (
    category_pool,
    haversine_km,
    intercity,
    load_categories,
    load_city,
    load_dataset,
    to_clock,
    to_minutes,
    travel_min,
)

DATA = Path("data/japan_travel_dataset.json")


def test_time_conversions_and_distance():
    assert to_minutes("09:35") == 575
    assert to_clock(574.6) == "09:35"
    with pytest.raises(ValueError):
        to_minutes("24:00")
    distance = haversine_km((0, 0), (0, 1))
    assert distance == pytest.approx(111.19, rel=0.01)
    assert travel_min((0, 0), (0, 1), 20, 1.3) == pytest.approx(distance * 3.9)


def test_master_dataset_loads_and_ids_are_unique():
    cities = load_dataset(DATA)
    assert len(cities) == 12
    assert sum(len(city.places) for city in cities.values()) == 135
    ids = [place.id for city in cities.values() for place in city.places]
    assert len(ids) == len(set(ids))
    assert cities["tokyo"].verified is False
    assert len(load_categories(DATA)) == 58
    assert load_city(DATA, "tokyo") == cities["tokyo"]
    with pytest.raises(ValueError, match="Unknown city_id"):
        load_city(DATA, "not-a-city")


def test_intercity_is_symmetric_and_tokyo_kyoto_is_expected():
    cities = load_dataset(DATA)
    cfg = Config()
    forward = intercity(cities["tokyo"], cities["kyoto"], cfg)
    reverse = intercity(cities["kyoto"], cities["tokyo"], cfg)
    assert forward.km == pytest.approx(reverse.km)
    assert forward.minutes == pytest.approx(reverse.minutes)
    assert forward.minutes == pytest.approx(179, abs=2)
    assert (forward.from_city, forward.to_city) == ("tokyo", "kyoto")


def test_category_pool_is_scoped_counted_and_sorted():
    cities, labels = load_dataset(DATA), load_categories(DATA)
    pool = category_pool(cities, labels, ["tokyo", "kyoto", "osaka"])
    assert pool
    assert pool == sorted(pool, key=lambda item: (-item["count"], item["label"]))
    assert all(set(item) == {"id", "label", "count"} for item in pool)
    assert sum(item["count"] for item in pool) == 44
    assert all(item["id"] in labels for item in pool)
    with pytest.raises(ValueError, match="Unknown city_id"):
        category_pool(cities, labels, ["unknown"])


@pytest.mark.parametrize("mutate, message", [
    (lambda d: d.update(schema_version="1.0.0"), "schema_version"),
    (lambda d: d["cities"].append(dict(d["cities"][0])), "Duplicate city_id"),
    (lambda d: d["cities"][0]["places"][0].update(close="05:00"), "close must be after open"),
    (lambda d: d["cities"][0]["places"][0].update(attraction=11), "Scores out of range"),
    (lambda d: d["cities"][0]["places"][0].update(effort="extreme"), "Unknown effort"),
    (lambda d: d["cities"][0]["places"][0].update(duration_min=0), "Duration must be positive"),
    (lambda d: d["cities"][1]["places"][0].update(id=d["cities"][0]["places"][0]["id"]), "Duplicate place id"),
    (lambda d: d["cities"][0]["places"][0].update(category="unknown"), "Unknown category"),
    (lambda d: d["cities"][0]["places"][0].pop("area"), "Missing required field"),
])
def test_dataset_validation(tmp_path, mutate, message):
    data = json.loads(DATA.read_text(encoding="utf-8"))
    mutate(data)
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_dataset(path)
