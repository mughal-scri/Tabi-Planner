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
    souvenir_boost_threshold: int = 3
    souvenir_boost: float = 2.0
    max_candidates_per_day: int = 15
    max_days: int = 5
    senior_excluded_effort: tuple[str, ...] = ("high",)
