from dataclasses import FrozenInstanceError

import pytest

from travelplanner.config import Config
from travelplanner.models import City, Place, Profile, Transfer


def test_models_are_multi_city_and_place_is_immutable():
    place = Place("p1", "A", 0, 0, 5, 2, 30, 540, 600, "low", "temple")
    city = City("tokyo", "Tokyo", (0, 0), "Tokyo Station", (place,), False)
    profile = Profile("adult", (("tokyo", 2),), ("temple",))
    transfer = Transfer("tokyo", "kyoto", 400, 190)
    assert place.value == 0.0
    assert city.places == (place,)
    assert profile.route == (("tokyo", 2),)
    assert transfer.minutes == 190
    with pytest.raises(FrozenInstanceError):
        place.value = 7


def test_config_defaults_and_mutable_defaults_are_independent():
    first, second = Config(), Config()
    assert first.day_start_min == 540
    assert first.day_hours == {"youth": 10, "adult": 8, "senior": 6}
    assert first.travel_factor["senior"] == 1.3
    assert first.intercity_speed_kmh == 150
    assert first.intercity_buffer_min == 30
    assert first.interest_boost == 8
    assert first.max_candidates_per_day == 20
    assert (first.max_cities, first.max_days_per_city, first.max_total_days) == (5, 5, 10)
    first.day_hours["adult"] = 1
    assert second.day_hours["adult"] == 8
