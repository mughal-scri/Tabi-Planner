"""Shared data models for the travel planner."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Place:
    name: str
    lat: float
    lon: float
    attraction: int
    souvenir: int
    duration_min: int
    open_min: int
    close_min: int
    effort: str
    tags: tuple[str, ...] = ()
    value: float = 0.0


@dataclass(frozen=True)
class Profile:
    age_group: str
    days: int


@dataclass(frozen=True)
class Stop:
    place: Place
    travel_min: float
    arrive_min: float
    start_min: float
    end_min: float


@dataclass
class DayPlan:
    day: int
    stops: list[Stop]
    value: float
    end_min: float
    expanded: int


@dataclass
class Plan:
    city: str
    profile: Profile
    days: list[DayPlan]
    total_value: float
    unused: list[str] = field(default_factory=list)
    algorithm: str = "astar"
    verified_data: bool = False
