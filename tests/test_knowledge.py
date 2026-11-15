import json

import pytest

from travelplanner.knowledge import haversine_km, load_city, to_clock, to_minutes, travel_min

DATA = "data/tokyo.json"


def test_time_conversions():
    assert to_minutes("09:35") == 575
    assert to_clock(574.6) == "09:35"
    with pytest.raises(ValueError):
        to_minutes("24:00")


def test_distance_and_travel_time():
    distance = haversine_km((0, 0), (0, 1))
    assert distance == pytest.approx(111.19, rel=0.01)
    assert travel_min((0, 0), (0, 1), 20, 1.3) == pytest.approx(distance * 3.9)


def test_tokyo_data_loads_unverified():
    meta, places = load_city(DATA)
    assert meta["city"] == "Tokyo"
    assert meta["verified"] is False
    assert meta["start"]["name"] == "Tokyo Station"
    assert len(places) == 13


@pytest.mark.parametrize("mutate, message", [
    (lambda d: d["places"][0].update(close="06:00"), "close must be after open"),
    (lambda d: d["places"][0].update(attraction=11), "Scores out of range"),
    (lambda d: d["places"][0].update(effort="extreme"), "Unknown effort"),
    (lambda d: d["places"].append(dict(d["places"][0])), "Duplicate place"),
    (lambda d: d["places"][0].pop("duration_min"), "Missing required field"),
])
def test_load_city_validation(tmp_path, mutate, message):
    with open(DATA, encoding="utf-8") as source:
        city = json.load(source)
    mutate(city)
    path = tmp_path / "city.json"
    path.write_text(json.dumps(city), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_city(path)
