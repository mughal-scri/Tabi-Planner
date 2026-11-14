"""Shared immutable input models and mutable plan result models."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Place:
    id: str
    name: str
    lat: float
    lon: float
    attraction: int
    souvenir: int
    duration_min: int
    open_min: int
    close_min: int
    effort: str
    category: str
    area: str = ""
    location_scope: str = "city"
    tags: tuple[str, ...] = ()
    value: float = 0.0


@dataclass(frozen=True)
class City:
    city_id: str
    name: str
    start: tuple[float, float]
    start_name: str
    places: tuple[Place, ...]
    verified: bool
    region: str = ""


@dataclass(frozen=True)
class Profile:
    age_group: str
    route: tuple[tuple[str, int], ...]
    interests: tuple[str, ...] = ()


@dataclass(frozen=True)
class Transfer:
    from_city: str
    to_city: str
    km: float
    minutes: float


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
    city_id: str
    stops: list[Stop]
    value: float
    start_min: float
    end_min: float
    expanded: int
    transfer: Transfer | None = None
    approximate: bool = False


@dataclass
class Plan:
    profile: Profile
    days: list[DayPlan]
    total_value: float
    unused: dict[str, list[str]] = field(default_factory=dict)
    removed: dict[str, dict[str, str]] = field(default_factory=dict)
    algorithm: str = "astar"
    verified_data: bool = False
    city_names: dict[str, str] = field(default_factory=dict)
    city_start_names: dict[str, str] = field(default_factory=dict)
    category_labels: dict[str, str] = field(default_factory=dict)
    souvenir_boost_threshold: int = 3
