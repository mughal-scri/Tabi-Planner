"""Ordered expert-rule pass for traveller-specific planning limits."""

from dataclasses import dataclass, replace
from typing import Callable

from .config import Config
from .models import Place


@dataclass(frozen=True)
class Rule:
    rule_id: str
    condition: Callable[[dict], bool]
    action: Callable[[dict], bool]


def default_rules(cfg: Config) -> list[Rule]:
    """Return the ordered M1 rule pipeline; each rule reports whether it changed facts."""

    def matches_interest(place: Place, interests: frozenset[str]) -> bool:
        return place.category in interests or bool(set(place.tags).intersection(interests))

    def set_day_window(facts: dict) -> bool:
        end = cfg.day_start_min + 60 * cfg.day_hours[facts["age_group"]]
        changed = facts.get("day_end_min") != end
        facts["day_end_min"] = end
        return changed

    def filter_senior(facts: dict) -> bool:
        if facts["age_group"] != "senior":
            return False
        removed = False
        for place in tuple(facts["candidates"]):
            if place.effort in cfg.senior_excluded_effort:
                facts["candidates"].remove(place)
                facts["removed"][place.name] = "R2"
                removed = True
        return removed

    def set_travel_factor(facts: dict) -> bool:
        factor = cfg.travel_factor[facts["age_group"]]
        changed = facts.get("travel_factor") != factor
        facts["travel_factor"] = factor
        return changed

    def souvenir_bonus(facts: dict) -> bool:
        changed = False
        for index, place in enumerate(facts["candidates"]):
            if place.souvenir >= cfg.souvenir_boost_threshold:
                facts["candidates"][index] = replace(
                    place, value=place.value + cfg.souvenir_boost
                )
                changed = True
        return changed

    def interest_bonus(facts: dict) -> bool:
        changed = False
        for index, place in enumerate(facts["candidates"]):
            if matches_interest(place, facts["interests"]):
                facts["candidates"][index] = replace(
                    place, value=place.value + cfg.interest_boost
                )
                changed = True
        return changed

    def fit_check(facts: dict) -> bool:
        changed = False
        start, end = cfg.day_start_min, facts["day_end_min"]
        for place in tuple(facts["candidates"]):
            available = min(place.close_min, end) - max(place.open_min, start)
            if available < place.duration_min:
                facts["candidates"].remove(place)
                facts["removed"][place.name] = "R4"
                changed = True
        return changed

    always = lambda _facts: True
    has_souvenir = lambda facts: any(
        p.souvenir >= cfg.souvenir_boost_threshold for p in facts["candidates"]
    )
    has_interest = lambda facts: any(
        matches_interest(p, facts["interests"]) for p in facts["candidates"]
    )
    has_nonfitting = lambda facts: any(
        min(p.close_min, facts["day_end_min"])
        - max(p.open_min, cfg.day_start_min) < p.duration_min
        for p in facts["candidates"]
    )
    is_senior = lambda facts: facts["age_group"] == "senior"

    return [
        Rule("R1", always, set_day_window),
        Rule("R2", is_senior, filter_senior),
        Rule("R3", always, set_travel_factor),
        Rule("R5", has_souvenir, souvenir_bonus),
        Rule("R6", has_interest, interest_bonus),
        Rule("R4", has_nonfitting, fit_check),
    ]


def apply_rules(
    places: list[Place] | tuple[Place, ...],
    age_group: str,
    interests: tuple[str, ...] | list[str],
    cfg: Config,
) -> dict:
    """Run M1's rules once in order for one city's places and return explanations."""
    if age_group not in cfg.day_hours or age_group not in cfg.travel_factor:
        raise ValueError(f"Unknown age_group {age_group!r}")
    if any(not isinstance(interest, str) for interest in interests):
        raise ValueError("interests must contain category id strings")

    facts = {
        "age_group": age_group,
        "interests": frozenset(interests),
        "candidates": [replace(place, value=place.attraction + place.souvenir) for place in places],
        "removed": {},
    }
    fired: list[str] = []
    for rule in default_rules(cfg):
        if rule.condition(facts):
            rule.action(facts)
            fired.append(rule.rule_id)

    return {
        "candidates": facts["candidates"],
        "day_start_min": cfg.day_start_min,
        "day_end_min": facts["day_end_min"],
        "travel_factor": facts["travel_factor"],
        "removed": facts["removed"],
        "fired": fired,
    }
