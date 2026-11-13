# Tabi-Planner

A command-line AI travel planner for one Japanese city. It uses an expert system to adapt daily limits to the traveller and A* search to build a value-focused itinerary. It is designed to work offline.

## Setup

Python 3.10 or newer is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Current progress

The project is being built in roadmap order. The initial package foundation and Tokyo seed data are in place. One owner-selected high-effort seed place is still needed to reach the planned 14 to 18 entries. Place scores, durations, coordinates, and hours remain placeholders; `data/tokyo.json` is marked unverified.

## Tests

```bash
.venv/bin/pytest -q
```

## Planned CLI

Once the planner and CLI phases are complete:

```bash
python -m travelplanner.cli --city tokyo --days 3 --age adult
```
