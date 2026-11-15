"""Command-line interface for the Japan travel planner."""

import argparse
import sys

from .planner import DEFAULT_DATA, format_plan, plan_trip
from .models import Profile


def _parse_route(value: str) -> tuple[tuple[str, int], ...]:
    entries = []
    for item in value.split(","):
        parts = item.strip().split(":")
        if len(parts) != 2 or not parts[0]:
            raise ValueError(f"Invalid route item {item!r}; expected city:days")
        try:
            days = int(parts[1])
        except ValueError as exc:
            raise ValueError(f"Invalid day count in route item {item!r}") from exc
        entries.append((parts[0], days))
    if not entries:
        raise ValueError("Route must contain at least one city")
    return tuple(entries)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan a value-focused Japan itinerary")
    route_group = parser.add_mutually_exclusive_group()
    route_group.add_argument("--route", help="ordered route, for example tokyo:3,kyoto:2")
    route_group.add_argument("--city", help="one city (use with --days)")
    parser.add_argument("--days", type=int, help="number of days for --city")
    parser.add_argument("--age", required=True, choices=("youth", "adult", "senior"))
    parser.add_argument("--interests", default="", help="comma-separated category ids")
    parser.add_argument("--algorithm", choices=("astar", "greedy"), default="astar")
    parser.add_argument("--data", default=str(DEFAULT_DATA), help="master dataset JSON path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.route is None and args.city is None:
        parser.error("one of --route or --city is required")
    if args.city is not None and args.days is None:
        parser.error("--city requires --days")
    if args.route is not None and args.days is not None:
        parser.error("--days can only be used with --city")

    try:
        route = _parse_route(args.route) if args.route is not None else ((args.city, args.days),)
        interests = tuple(item.strip() for item in args.interests.split(",") if item.strip())
        plan = plan_trip(args.data, Profile(args.age, route, interests), algorithm=args.algorithm)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(format_plan(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
