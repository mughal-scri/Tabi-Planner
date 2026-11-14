import pytest

from test_astar import random_instance
from travelplanner.astar import plan_day
from travelplanner.greedy import plan_day_greedy


@pytest.mark.parametrize("seed", range(30))
def test_greedy_never_exceeds_optimal_astar(seed):
    places = random_instance(300 + seed)
    args = (places, (35.0, 139.0), 540, 1020, 20.0, 1.0)
    _, optimal, _ = plan_day(*args)
    stops, value, expanded = plan_day_greedy(*args)
    assert value <= optimal
    assert value == pytest.approx(sum(stop.place.value for stop in stops))
    assert expanded == 0
    assert all(stop.end_min <= 1020 for stop in stops)


def test_greedy_can_return_an_empty_plan():
    assert plan_day_greedy([], (35.0, 139.0), 540, 600, 20.0, 1.0) == ([], 0.0, 0)
