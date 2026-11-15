"""A* search for a maximum-value day itinerary."""

import heapq
import itertools

from .knowledge import travel_min
from .models import Place, Stop


def _h_bound(now: float, day_end: float, ordered: tuple[Place, ...], mask: int | None = None) -> float:
    """Fractional knapsack bound over places in descending value/time order."""
    remaining = day_end - now
    if remaining <= 0:
        return 0.0
    total = 0.0
    for index, place in enumerate(ordered):
        if mask is not None and mask & (1 << index):
            continue
        if place.close_min - place.duration_min < now:
            continue
        ratio = place.value / place.duration_min
        value, duration = place.value, place.duration_min
        if remaining <= 0:
            break
        if duration <= remaining:
            total += value
            remaining -= duration
        else:
            total += ratio * remaining
            remaining = 0
    return total


def h_bound(now: float, day_end: float, unvisited: list[Place] | tuple[Place, ...]) -> float:
    """Return an admissible fractional-knapsack upper bound on remaining value."""
    ordered = tuple(sorted(unvisited, key=lambda p: p.value / p.duration_min, reverse=True))
    return _h_bound(now, day_end, ordered)


def plan_day(
    candidates: list[Place] | tuple[Place, ...],
    start: tuple[float, float],
    day_start_min: float,
    day_end_min: float,
    speed_kmh: float,
    factor: float,
) -> tuple[list[Stop], float, int]:
    """Find the highest-value feasible ordered plan for one day."""
    places = tuple(candidates)
    n = len(places)
    ordered = tuple(sorted(
        enumerate(places),
        key=lambda item: item[1].value / item[1].duration_min,
        reverse=True,
    ))
    ordered_places = tuple(place for _, place in ordered)
    ordered_to_original = tuple(index for index, _ in ordered)
    counter = itertools.count()
    expanded = 0

    def position(location: int) -> tuple[float, float]:
        if location < 0:
            return start
        place = places[location]
        return place.lat, place.lon

    def bound(now: float, mask: int) -> float:
        ordered_mask = 0
        for rank, original in enumerate(ordered_to_original):
            if mask & (1 << original):
                ordered_mask |= 1 << rank
        return _h_bound(now, day_end_min, ordered_places, ordered_mask)

    # Entry: negative f, tie-breaker, is_goal, g, now, location, mask, path.
    heap = [(-bound(day_start_min, 0), next(counter), False,
             0.0, day_start_min, -1, 0, ())]
    best: dict[tuple[int, int], float] = {}
    while heap:
        _, _, is_goal, value, now, location, mask, path = heapq.heappop(heap)
        if is_goal:
            return list(path), value, expanded

        key = (location, mask)
        if key in best and best[key] <= now:
            continue
        best[key] = now
        expanded += 1
        extended = False

        for index, place in enumerate(places):
            bit = 1 << index
            if mask & bit:
                continue
            pos = position(location)
            travel = travel_min(pos, (place.lat, place.lon), speed_kmh, factor)
            arrival = now + travel
            visit_start = max(arrival, place.open_min)
            visit_end = visit_start + place.duration_min
            if visit_end > place.close_min or visit_end > day_end_min:
                continue

            extended = True
            next_value = value + place.value
            next_mask = mask | bit
            next_key = (index, next_mask)
            if next_key in best and best[next_key] <= visit_end:
                continue
            stop = Stop(place, travel, arrival, visit_start, visit_end)
            priority = next_value + bound(visit_end, next_mask)
            heapq.heappush(heap, (-priority, next(counter), False, next_value,
                                  visit_end, index, next_mask, path + (stop,)))

        if not extended:
            # A terminal's optimistic priority is not its true value. Requeue
            # it at f=g, and only return it when that goal entry is popped.
            heapq.heappush(heap, (-value, next(counter), True, value,
                                  now, location, mask, path))

    return [], 0.0, expanded
