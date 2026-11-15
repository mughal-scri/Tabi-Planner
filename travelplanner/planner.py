"""Multi-city trip orchestration and readable itinerary formatting."""

from pathlib import Path

from .astar import plan_day
from .config import Config
from .expert import apply_rules
from .greedy import plan_day_greedy
from .knowledge import intercity, load_categories, load_dataset, to_clock
from .models import DayPlan, Plan, Profile


DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data" / "japan_travel_dataset.json"


def plan_trip(
    dataset_path: str | Path,
    profile: Profile,
    cfg: Config = Config(),
    algorithm: str = "astar",
) -> Plan:
    """Plan the requested ordered route one city and one day at a time."""
    if profile.age_group not in cfg.day_hours or profile.age_group not in cfg.travel_factor:
        raise ValueError(f"Unknown age group {profile.age_group!r}")
    if algorithm not in {"astar", "greedy"}:
        raise ValueError("algorithm must be 'astar' or 'greedy'")
    if not profile.route:
        raise ValueError("Route must contain at least one city")
    if len(profile.route) > cfg.max_cities:
        raise ValueError(f"Route exceeds the maximum of {cfg.max_cities} cities")

    seen_cities: set[str] = set()
    total_days = 0
    for entry in profile.route:
        if not isinstance(entry, (tuple, list)) or len(entry) != 2:
            raise ValueError("Each route entry must be a (city_id, days) pair")
        city_id, days = entry
        if not isinstance(city_id, str) or not city_id:
            raise ValueError("Route city ids must be non-empty strings")
        if city_id in seen_cities:
            raise ValueError(f"Route cannot repeat city {city_id!r}")
        seen_cities.add(city_id)
        if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= cfg.max_days_per_city:
            raise ValueError(f"Days for {city_id!r} must be from 1 to {cfg.max_days_per_city}")
        total_days += days
    if total_days > cfg.max_total_days:
        raise ValueError(f"Route exceeds the maximum of {cfg.max_total_days} total days")
    if any(not isinstance(interest, str) for interest in profile.interests):
        raise ValueError("Interests must be category id strings")

    cities = load_dataset(dataset_path)
    labels = load_categories(dataset_path)
    for city_id, _ in profile.route:
        if city_id not in cities:
            raise ValueError(f"Unknown city {city_id!r}")
    unknown_interests = set(profile.interests) - labels.keys()
    if unknown_interests:
        raise ValueError(f"Unknown interest category id(s): {', '.join(sorted(unknown_interests))}")

    rule_results = {}
    remaining_by_city = {}
    removed: dict[str, dict[str, str]] = {}
    for city_id, _ in profile.route:
        city = cities[city_id]
        result = apply_rules(city.places, profile.age_group, profile.interests, cfg)
        rule_results[city_id] = result
        remaining_by_city[city_id] = list(result["candidates"])
        removed[city_id] = result["removed"]

    days: list[DayPlan] = []
    previous_city = None
    global_day = 0
    all_visited: set[str] = set()
    for city_id, number_of_days in profile.route:
        city = cities[city_id]
        result = rule_results[city_id]
        for city_day in range(number_of_days):
            global_day += 1
            transfer = intercity(previous_city, city, cfg) if city_day == 0 and previous_city else None
            day_start = result["day_start_min"] + (transfer.minutes if transfer else 0)
            day_end = result["day_end_min"]

            remaining = remaining_by_city[city_id]
            approximate = len(remaining) > cfg.max_candidates_per_day
            if approximate:
                candidates = sorted(
                    enumerate(remaining),
                    key=lambda item: (-item[1].value / item[1].duration_min, item[0]),
                )[:cfg.max_candidates_per_day]
                candidates = [place for _, place in candidates]
            else:
                candidates = remaining

            search = plan_day if algorithm == "astar" else plan_day_greedy
            stops, value, expanded = search(
                candidates, city.start, day_start, day_end, cfg.speed_kmh,
                result["travel_factor"],
            )
            visited_today = {stop.place.id for stop in stops}
            all_visited.update(visited_today)
            remaining_by_city[city_id] = [
                place for place in remaining if place.id not in visited_today
            ]
            end_min = stops[-1].end_min if stops else day_start
            days.append(DayPlan(
                day=global_day,
                city_id=city_id,
                stops=stops,
                value=value,
                start_min=day_start,
                end_min=end_min,
                expanded=expanded,
                transfer=transfer,
                approximate=approximate,
            ))
        previous_city = city

    unused = {
        city_id: [place.name for place in cities[city_id].places if place.id not in all_visited]
        for city_id, _ in profile.route
    }
    return Plan(
        profile=profile,
        days=days,
        total_value=sum(day.value for day in days),
        unused=unused,
        removed=removed,
        algorithm=algorithm,
        verified_data=all(cities[city_id].verified for city_id, _ in profile.route),
        city_names={city_id: cities[city_id].name for city_id, _ in profile.route},
        city_start_names={city_id: cities[city_id].start_name for city_id, _ in profile.route},
        interest_labels={interest: labels[interest] for interest in profile.interests},
        souvenir_boost_threshold=cfg.souvenir_boost_threshold,
    )


def _duration_text(minutes: float) -> str:
    rounded = int(minutes + 0.5)
    hours, remainder = divmod(rounded, 60)
    if hours and remainder:
        return f"{hours}h {remainder}m"
    if hours:
        return f"{hours}h"
    return f"{remainder}m"


def format_plan(plan: Plan) -> str:
    """Render a plan with route, transfers, place tags, totals, and caveats."""
    city_names = plan.city_names or {city_id: city_id.replace("_", " ").title()
                                     for city_id, _ in plan.profile.route}
    route = " -> ".join(f"{city_names[city_id]} {days}d"
                        for city_id, days in plan.profile.route)
    algorithm = "A*" if plan.algorithm == "astar" else "Greedy"
    lines = [
        f"Japan Travel Planner | Route: {route} | {plan.profile.age_group} | algorithm: {algorithm}"
    ]
    if plan.profile.interests:
        interests = ", ".join(
            plan.interest_labels.get(interest, interest) for interest in plan.profile.interests
        )
        lines.append(f"Interests: {interests}")
    if not plan.verified_data:
        lines.append("Note: place data is unverified; check hours and coordinates before relying on it.")

    for day in plan.days:
        city_name = city_names.get(day.city_id, day.city_id)
        if day.stops:
            heading = (f"Day {day.day} | {city_name} ({to_clock(day.start_min)} to "
                       f"{to_clock(day.end_min)}, value {day.value:g})")
        else:
            heading = f"Day {day.day} | {city_name}"
        if day.approximate:
            heading += " [approximate: candidate cap]"
        lines.append(heading)
        if day.transfer:
            from_name = city_names.get(day.transfer.from_city, day.transfer.from_city)
            to_name = city_names.get(day.transfer.to_city, day.transfer.to_city)
            lines.append(f"  Transfer: {from_name} -> {to_name}, {day.transfer.km:.0f} km, "
                         f"about {_duration_text(day.transfer.minutes)}")
        start_name = plan.city_start_names.get(day.city_id, f"{city_name} Station")
        lines.append(f"  {to_clock(day.start_min)}  Start: {start_name}")
        for stop in day.stops:
            place = stop.place
            location = f", {place.area}" if place.area else ""
            marks = []
            if place.location_scope == "nearby_day_trip":
                marks.append("day trip")
            if place.category in plan.profile.interests:
                marks.append("matches interest")
            if place.souvenir >= plan.souvenir_boost_threshold:
                marks.append("souvenirs")
            suffix = f"  [{'] ['.join(marks)}]" if marks else ""
            lines.append(f"  {to_clock(stop.start_min)}  {place.name}{location} "
                         f"({place.duration_min} min){suffix}")

    places_visited = sum(len(day.stops) for day in plan.days)
    total_days = sum(days for _, days in plan.profile.route)
    lines.append(f"Total value: {plan.total_value:g} | Trip: {total_days} days, "
                 f"{len(plan.profile.route)} cities | Places visited: {places_visited}")

    not_scheduled = []
    for city_id, _ in plan.profile.route:
        reasons = plan.removed.get(city_id, {})
        descriptions = [f"{name} (removed by {reasons[name]})" if name in reasons
                       else name for name in plan.unused.get(city_id, [])]
        if descriptions:
            not_scheduled.append(f"{city_names.get(city_id, city_id)}: "
                                 + ", ".join(descriptions))
    if not_scheduled:
        lines.append("Not scheduled: " + "; ".join(not_scheduled))
    return "\n".join(lines)
