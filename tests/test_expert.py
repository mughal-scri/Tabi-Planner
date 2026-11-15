import pytest

from travelplanner.config import Config
from travelplanner.knowledge import load_city
from travelplanner.models import Place
from travelplanner.expert import apply_rules, default_rules


def place(name="Place", *, effort="low", duration=60, open_min=540, close_min=1080,
          souvenir=2, category="temple"):
    return Place(name.lower(), name, 35.0, 139.0, 7, souvenir, duration,
                 open_min, close_min, effort, category)


@pytest.mark.parametrize("age,hours,factor", [
    ("youth", 10, 1.0), ("adult", 8, 1.0), ("senior", 6, 1.3),
])
def test_r1_day_window_and_r3_travel_factor(age, hours, factor):
    result = apply_rules([place()], age, (), Config())
    assert result["day_start_min"] == 540
    assert result["day_end_min"] == 540 + hours * 60
    assert result["travel_factor"] == factor


def test_r2_removes_high_effort_only_for_seniors():
    places = [place("easy"), place("hard", effort="high")]
    senior = apply_rules(places, "senior", (), Config())
    adult = apply_rules(places, "adult", (), Config())
    assert [p.name for p in senior["candidates"]] == ["easy"]
    assert senior["removed"] == {"hard": "R2"}
    assert [p.name for p in adult["candidates"]] == ["easy", "hard"]


def test_r4_removes_place_that_cannot_fit_and_respects_equality_boundary():
    result = apply_rules([place("too long", duration=361), place("fits", duration=360)],
                         "senior", (), Config())
    assert [p.name for p in result["candidates"]] == ["fits"]
    assert result["removed"] == {"too long": "R4"}


def test_r5_and_r6_additive_values_and_empty_interests_do_nothing():
    places = [place("base", souvenir=2), place("souvenir", souvenir=3),
              place("interest", souvenir=2, category="shrine")]
    baseline = apply_rules(places, "adult", (), Config())
    preferred = apply_rules(places, "adult", ("shrine",), Config())
    assert [p.value for p in baseline["candidates"]] == [9, 12, 9]
    assert [p.value for p in preferred["candidates"]] == [9, 12, 17]


def test_rule_order_explanations_and_age_group_interface():
    rules = default_rules(Config())
    assert [rule.rule_id for rule in rules] == ["R1", "R2", "R3", "R5", "R6", "R4"]
    city = load_city("data/japan_travel_dataset.json", "tokyo")
    result = apply_rules(city.places, "senior", ("temple",), Config())
    assert result["fired"] == ["R1", "R2", "R3", "R5", "R6", "R4"]
    assert result["removed"]
    assert all(reason in {"R2", "R4"} for reason in result["removed"].values())
    assert all(p.value >= p.attraction + p.souvenir for p in result["candidates"])
    with pytest.raises(ValueError, match="age_group"):
        apply_rules(city.places, "child", (), Config())
