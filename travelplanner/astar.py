"""A* search for a maximum-value day itinerary."""

import heapq
import itertools

from .knowledge import travel_min
from .models import Place, Stop


def h_bound(now: float, day_end: float, unvisited: list[Place] | tuple[Place, ...]) -> float:
    """Return a fractional-knapsack upper bound on value still collectable."""
    remaining = day_end - now
    if remaining <= 0:
        return 0.0
    items = sorted(
        ((place.value / place.duration_min, place.value, place.duration_min)
         for place in unvisited
         if place.duration_min <= remaining and place.close_min - place.duration_min >= now),
        reverse=True,
    )
    total = 0.0
    for ratio, value, duration in items:
        if remaining <= 0:
            break
        if duration <= remaining:
            total += value
            remaining -= duration
        else:
            total += ratio * remaining
            remaining = 0
    return total


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
    counter = itertools.count()
    expanded = 0

    def position(location: int) -> tuple[float, float]:
        if location < 0:
            return start
        place = places[location]
        return place.lat, place.lon

    def unvisited(mask: int) -> list[Place]:
        return [places[i] for i in range(n) if not mask & (1 << i)]

    # Entry: negative f, tie-breaker, is_goal, g, now, location, mask, path.
    heap = [(-h_bound(day_start_min, day_end_min, places), next(counter), False,
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
            priority = next_value + h_bound(visit_end, day_end_min, unvisited(next_mask))
            heapq.heappush(heap, (-priority, next(counter), False, next_value,
                                  visit_end, index, next_mask, path + (stop,)))

        if not extended:
            # A terminal's optimistic priority is not its true value. Requeue
            # it at f=g, and only return it when that goal entry is popped.
            heapq.heappush(heap, (-value, next(counter), True, value,
                                  now, location, mask, path))

    return [], 0.0, expanded
