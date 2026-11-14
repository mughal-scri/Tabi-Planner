"""A* correctness tests and a small brute-force oracle (tests only)."""

import random

import pytest

from travelplanner.astar import h_bound, plan_day
from travelplanner.models import Place


def make_place(i, x, *, duration=45, opening=540, closing=1000, value=10):
    return Place(str(i), f"P{i}", 35.0, 139.0 + x * 0.01, 1, 1, duration,
                 opening, closing, "low", "temple", value=float(value))


def random_instance(seed, count=7):
    rng = random.Random(seed)
    places = []
    for i in range(count):
        duration = rng.randrange(25, 91, 5)
        opening = rng.randrange(510, 661, 15)
        closing = rng.randrange(max(opening + duration, 780), 1081, 15)
        places.append(make_place(i, rng.uniform(-0.15, 0.15), duration=duration,
                                 opening=opening, closing=closing, value=rng.randrange(5, 31)))
    return places


def brute_force_day(candidates, start, day_start_min, day_end_min, speed_kmh, factor):
    """Enumerate every feasible visit order, returning the optimal value."""
    from travelplanner.knowledge import travel_min

    best = 0.0

    def visit(position, now, remaining, value):
        nonlocal best
        best = max(best, value)
        for index, place in enumerate(remaining):
            distance = travel_min(position, (place.lat, place.lon), speed_kmh, factor)
            arrival = now + distance
            visit_start = max(arrival, place.open_min)
            end = visit_start + place.duration_min
            if end <= place.close_min and end <= day_end_min:
                visit((place.lat, place.lon), end,
                      remaining[:index] + remaining[index + 1:], value + place.value)

    visit(start, day_start_min, tuple(candidates), 0.0)
    return best


@pytest.mark.parametrize("seed", range(30))
def test_astar_matches_brute_force_on_seeded_instances(seed):
    places = random_instance(seed)
    expected = brute_force_day(places, (35.0, 139.0), 540, 1020, 20.0, 1.0)
    stops, value, _ = plan_day(places, (35.0, 139.0), 540, 1020, 20.0, 1.0)
    assert value == pytest.approx(expected)
    assert sum(stop.place.value for stop in stops) == pytest.approx(value)
    assert all(stop.end_min <= 1020 and stop.end_min <= stop.place.close_min for stop in stops)


def test_heuristic_is_an_upper_bound_at_root():
    places = random_instance(128)
    optimum = brute_force_day(places, (35.0, 139.0), 540, 1020, 20.0, 1.0)
    assert h_bound(540, 1020, places) >= optimum


def test_waiting_for_opening_and_empty_candidates():
    later = make_place(1, 0, duration=30, opening=600, closing=700, value=11)
    stops, value, _ = plan_day([later], (35.0, 139.0), 540, 660, 20.0, 1.0)
    assert value == 11
    assert stops[0].arrive_min < stops[0].start_min == 600
    assert plan_day([], (35.0, 139.0), 540, 660, 20.0, 1.0)[:2] == ([], 0.0)


def test_late_start_respects_budget_and_reduces_feasible_plan():
    places = [make_place(i, i * 0.01, duration=90, closing=900, value=10) for i in range(4)]
    early = plan_day(places, (35.0, 139.0), 540, 900, 20.0, 1.0)
    late = plan_day(places, (35.0, 139.0), 720, 900, 20.0, 1.0)
    assert late[1] <= early[1]
    assert all(stop.end_min <= 900 for stop in late[0])


def test_goal_requeue_returns_optimal_terminal_plan():
    # The first-terminal-pop variant returns 48 for this case; the true optimum is 66.
    data = [
        (138.99954, 40, 570, 1005, 15),
        (139.00055, 40, 540, 870, 26),
        (139.00036, 90, 570, 810, 18),
        (139.00045, 60, 660, 990, 7),
    ]
    places = [Place(str(i), f"P{i}", 35.0, lon, 1, 1, duration, opening,
                    closing, "low", "temple", value=float(value))
              for i, (lon, duration, opening, closing, value) in enumerate(data)]
    result = plan_day(places, (35.0, 139.0), 540, 900, 20.0, 1.0)
    assert result[1] == 66
    assert result[1] == brute_force_day(places, (35.0, 139.0), 540, 900, 20.0, 1.0)


def test_search_is_deterministic():
    places = random_instance(73)
    first = plan_day(places, (35.0, 139.0), 540, 1020, 20.0, 1.0)
    second = plan_day(places, (35.0, 139.0), 540, 1020, 20.0, 1.0)
    assert first == second
