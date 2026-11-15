import pytest

from travelplanner.config import Config
from travelplanner.expert import apply_rules
from travelplanner.knowledge import load_dataset, to_clock
from travelplanner.models import Profile, Transfer
from travelplanner.planner import format_plan, plan_trip

DATA = "data/japan_travel_dataset.json"


def assert_plan_invariants(plan, cfg):
    cities = load_dataset(DATA)
    ids = []
    assert [day.day for day in plan.days] == list(range(1, len(plan.days) + 1))
    day_offset = 0
    for route_index, (city_id, day_count) in enumerate(plan.profile.route):
        city_days = plan.days[day_offset:day_offset + day_count]
        assert all(day.city_id == city_id for day in city_days)
        for city_day_index, day in enumerate(city_days):
            if route_index and city_day_index == 0:
                assert day.transfer is not None
            else:
                assert day.transfer is None
        day_offset += day_count
    for day in plan.days:
        city = cities[day.city_id]
        day_end = cfg.day_start_min + cfg.day_hours[plan.profile.age_group] * 60
        if day.stops:
            assert day.end_min <= day_end
        if day.transfer:
            assert isinstance(day.transfer, Transfer)
            assert day.start_min == pytest.approx(cfg.day_start_min + day.transfer.minutes)
        previous_start = day.start_min
        for stop in day.stops:
            assert stop.place.id in {place.id for place in city.places}
            assert stop.place.id not in ids
            ids.append(stop.place.id)
            assert stop.start_min >= stop.place.open_min
            assert stop.end_min <= stop.place.close_min
            assert stop.end_min <= day_end
            assert stop.start_min >= previous_start
            previous_start = stop.start_min
        assert day.value == pytest.approx(sum(stop.place.value for stop in day.stops))
    assert plan.total_value == pytest.approx(sum(day.value for day in plan.days))


@pytest.mark.parametrize("route", [(("tokyo", 1),), (("tokyo", 3),),
                                    (("tokyo", 2), ("kyoto", 2), ("osaka", 1))])
@pytest.mark.parametrize("age", ["youth", "adult", "senior"])
def test_plan_trip_invariants_for_routes_and_age_groups(route, age):
    cfg = Config()
    plan = plan_trip(DATA, Profile(age, route), cfg)
    assert_plan_invariants(plan, cfg)
    if age == "senior":
        assert all(stop.place.effort != "high" for day in plan.days for stop in day.stops)


def test_greedy_plan_and_single_city_route_equivalence():
    profile = Profile("adult", (("tokyo", 2),))
    route_plan = plan_trip(DATA, profile, algorithm="astar")
    single_plan = plan_trip(DATA, Profile("adult", (("tokyo", 2),)), algorithm="astar")
    greedy = plan_trip(DATA, profile, algorithm="greedy")
    assert route_plan == single_plan
    assert greedy.total_value <= route_plan.total_value
    assert_plan_invariants(greedy, Config())


def test_interests_are_soft_value_boosts_and_empty_is_unchanged():
    base = plan_trip(DATA, Profile("adult", (("tokyo", 1),)))
    empty = plan_trip(DATA, Profile("adult", (("tokyo", 1),), ()))
    interested = plan_trip(DATA, Profile("adult", (("tokyo", 1),),
                                        ("museum", "park", "garden")))
    assert base == empty
    base_matches = sum(stop.place.category in {"museum", "park", "garden"}
                       for day in base.days for stop in day.stops)
    interested_matches = sum(stop.place.category in {"museum", "park", "garden"}
                             for day in interested.days for stop in day.stops)
    assert interested_matches > base_matches


def test_long_transfer_empty_day_is_preserved_and_next_day_is_planned():
    plan = plan_trip(DATA, Profile("senior", (("sapporo", 1), ("nagasaki", 2))))
    arrival_day, following_day = plan.days[1], plan.days[2]
    assert arrival_day.transfer is not None
    assert arrival_day.stops == []
    assert arrival_day.start_min > Config().day_start_min + Config().day_hours["senior"] * 60
    assert following_day.transfer is None
    assert following_day.stops


def test_candidate_guard_is_recorded_and_keeps_best_value_density():
    cfg = Config(max_candidates_per_day=2)
    plan = plan_trip(DATA, Profile("adult", (("tokyo", 1),)), cfg)
    assert plan.days[0].approximate is True
    assert "candidate cap" in format_plan(plan)
    candidates = apply_rules(load_dataset(DATA)["tokyo"].places, "adult", (), cfg)["candidates"]
    expected = {place.id for place in sorted(
        candidates, key=lambda place: place.value / place.duration_min, reverse=True
    )[:2]}
    assert all(stop.place.id in expected for stop in plan.days[0].stops)


@pytest.mark.parametrize("profile,message", [
    (Profile("child", (("tokyo", 1),)), "age group"),
    (Profile("adult", ()), "(?i)route"),
    (Profile("adult", (("tokyo", 1), ("tokyo", 1))), "repeat"),
    (Profile("adult", (("unknown", 1),)), "Unknown city"),
    (Profile("adult", (("tokyo", 0),)), "(?i)days"),
    (Profile("adult", (("tokyo", 6),)), "(?i)days"),
    (Profile("adult", (("tokyo", 5), ("kyoto", 5), ("osaka", 1))), "total"),
    (Profile("adult", (("tokyo", 1),), ("not-a-category",)), "interest"),
    (Profile("adult", tuple((city, 1) for city in
                             ("tokyo", "kyoto", "osaka", "nara", "hiroshima", "sapporo"))), "cities"),
])
def test_plan_trip_rejects_invalid_profiles(profile, message):
    with pytest.raises(ValueError, match=message):
        plan_trip(DATA, profile)


def test_format_plan_includes_route_interests_transfers_and_unverified_note():
    plan = plan_trip(DATA, Profile("adult", (("tokyo", 1), ("kyoto", 1)), ("temple",)))
    output = format_plan(plan)
    assert "Tokyo" in output and "Kyoto" in output
    assert "Interests:" in output
    assert "Transfer: Tokyo -> Kyoto" in output
    assert "unverified" in output
    assert "Total value:" in output
    assert to_clock(plan.days[0].start_min) in output
