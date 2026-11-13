from dataclasses import FrozenInstanceError

import pytest

from travelplanner.config import Config
from travelplanner.models import Place, Profile


def test_place_is_immutable_and_has_spec_default_value():
    place = Place("A", 0, 0, 5, 2, 30, 540, 600, "low")
    assert place.value == 0.0
    with pytest.raises(FrozenInstanceError):
        place.value = 7


def test_config_defaults_are_independent():
    first, second = Config(), Config()
    assert first.day_start_min == 540
    assert first.day_hours == {"youth": 10, "adult": 8, "senior": 6}
    assert first.travel_factor["senior"] == 1.3
    first.day_hours["adult"] = 1
    assert second.day_hours["adult"] == 8


def test_profile_fields():
    assert Profile("adult", 3).days == 3
