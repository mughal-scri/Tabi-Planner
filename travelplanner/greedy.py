"""Greedy value-per-minute baseline for a single day."""

from .knowledge import travel_min
from .models import Place, Stop


def plan_day_greedy(
    candidates: list[Place] | tuple[Place, ...],
    start: tuple[float, float],
    day_start_min: float,
    day_end_min: float,
    speed_kmh: float,
    factor: float,
) -> tuple[list[Stop], float, int]:
    """Repeatedly choose the feasible place with best value per elapsed minute."""
    remaining = list(enumerate(candidates))
    position = start
    now = day_start_min
    stops: list[Stop] = []
    total_value = 0.0

    while remaining:
        choices: list[tuple[float, int, int, Stop]] = []
        for offset, (original_index, place) in enumerate(remaining):
            travel = travel_min(position, (place.lat, place.lon), speed_kmh, factor)
            arrival = now + travel
            visit_start = max(arrival, place.open_min)
            visit_end = visit_start + place.duration_min
            if visit_end > place.close_min or visit_end > day_end_min:
                continue
            elapsed = visit_end - now
            score = place.value / elapsed
            choices.append((score, -original_index, offset,
                            Stop(place, travel, arrival, visit_start, visit_end)))

        if not choices:
            break
        _, _, chosen_offset, stop = max(choices, key=lambda item: (item[0], item[1]))
        remaining.pop(chosen_offset)
        stops.append(stop)
        total_value += stop.place.value
        position = (stop.place.lat, stop.place.lon)
        now = stop.end_min

    return stops, total_value, 0
