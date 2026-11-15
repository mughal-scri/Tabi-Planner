"""Planner tunables."""

from dataclasses import dataclass, field


@dataclass
class Config:
    day_start_min: int = 540
    day_hours: dict[str, int] = field(
        default_factory=lambda: {"youth": 10, "adult": 8, "senior": 6}
    )
    speed_kmh: float = 20.0
    travel_factor: dict[str, float] = field(
        default_factory=lambda: {"youth": 1.0, "adult": 1.0, "senior": 1.3}
    )
    intercity_speed_kmh: float = 150.0
    intercity_buffer_min: int = 30
    souvenir_boost_threshold: int = 3
    souvenir_boost: float = 2.0
    interest_boost: float = 8.0
    max_candidates_per_day: int = 20
    max_cities: int = 5
    max_days_per_city: int = 5
    max_total_days: int = 10
    senior_excluded_effort: tuple[str, ...] = ("high",)
