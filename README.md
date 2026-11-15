# Tabi-Planner

A Japan travel planner for one city or an ordered multi-city route. An expert system adjusts daily limits and place values for the traveller; A* is designed to build high-value daily itineraries within opening hours and travel time. A Greedy baseline supports comparison. The project works offline and uses an owner-supplied, unverified dataset.

## Setup

Python 3.10 or newer is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Current progress

Phases 1 to 3 are complete: multi-city data models, configuration, dataset helpers, traveller-specific expert rules, A* search, and a Greedy baseline are in place. The dataset contains 12 cities and 135 places. Its scores are estimates, its hours are planning windows, and its coordinates are approximate; it remains unverified. The multi-city planner and CLI are next.

## Tests

```bash
pytest -q
```

## Planned CLI

Once the planner and CLI phases are complete:

```bash
python -m travelplanner.cli --route tokyo:3,kyoto:2 --age adult
python -m travelplanner.cli --city tokyo --days 3 --age adult
```
