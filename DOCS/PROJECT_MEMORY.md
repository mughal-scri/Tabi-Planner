# Project Memory: Japan Travel Planner

**Purpose:** the compact, current handoff for a new agent. Read this after `RULES.md` and `AGENT_BOARD.md`; do **not** scan the repository to learn project state. This is a memory aid, not a replacement for `Design_Doc.md`.

**Snapshot:** 2026-11-13. Documentation is complete. Phase 1 foundation, models/config, knowledge helpers, and tests are implemented; Tokyo seed data has 13 places and is still unverified. Test count: 11 passed.

---

## Read only what you need

1. Read `DOCS/RULES.md`, `DOCS/AGENT_BOARD.md`, and this file.
2. For a planned module, open only its section in `DOCS/Design_Doc.md`, its source file, and its matching test file.
3. For a bug, start with its test and implementation; open a direct dependency only if the failure requires it.
4. Before ending, update the board, this file if project-wide state changed, and the Roadmap checkboxes.

Authority order: owner instruction, `Design_Doc.md`, `PRD.md`, `Roadmap.md`, then this memory. If this file disagrees with code plus a passing test, correct this file and log it on the board.

---

## Current standing

| Area | State | Evidence |
|---|---|---|
| Documentation set | **Complete** | Eight markdown files exist |
| Phase 1 foundation and data | In progress | P1.1-P1.4, P1.6 implemented; owner choice for 14th high-effort seed place remains |
| Phase 2 expert system | Not started | |
| Phase 3 search (A*, Greedy) | Not started | Logic is prototype-verified in `Design_Doc.md` Section 8.6 |
| Phase 4 pipeline and CLI | Not started | |
| Phase 5 evaluation and report | Not started | |
| Phase 6 optional extras | Not started | Only after Phase 5 |

**What the project is:** a command-line travel planner for one Japanese city (Tokyo first). Input: city, days (1 to 5), age group (youth, adult, senior). Output: a day-by-day itinerary that maximizes total value (attractions plus souvenirs) within each day's time limit and opening hours. An expert system sets limits by age group; A* searches each day; Greedy is the comparison baseline. Utility-based agent; no learning.

---

## Planned surface: use these contracts

Implemented files are listed in the current repo map in `AGENT_BOARD.md`.

| File | Main entry points |
|---|---|
| `travelplanner/models.py` | `Place`, `Profile`, `Stop`, `DayPlan`, `Plan` |
| `travelplanner/config.py` | `Config()` (all tunables) |
| `travelplanner/knowledge.py` | `to_minutes`, `to_clock`, `haversine_km`, `travel_min`, `load_city` |
| `travelplanner/expert.py` | `Rule`, `default_rules`, `apply_rules` (returns candidates, day window, travel factor, `removed`, `fired`) |
| `travelplanner/astar.py` | `h_bound`, `plan_day(candidates, start, day_start_min, day_end_min, speed_kmh, factor)` returns `(stops, value, expanded)` |
| `travelplanner/greedy.py` | `plan_day_greedy` with the same signature as `plan_day` |
| `travelplanner/planner.py` | `plan_trip(city_path, profile, cfg, algorithm)`, `format_plan(plan)` |
| `travelplanner/cli.py` | `python -m travelplanner.cli --city tokyo --days 3 --age adult [--algorithm astar|greedy]` |
| `travelplanner/experiments.py` | E1 (A* vs Greedy) and E2 (rules on and off) |

---

## Facts that must not be re-derived

- Time is minutes since midnight (`540` = 09:00). Day starts 09:00; day length is 10, 8, or 6 hours for youth, adult, senior (rule R1). The day ends at the last visit; no return to the hotel.
- Travel minutes = haversine km / 20 km/h * 60 * factor. Factor is 1.0, or 1.3 for seniors, applied to travel only.
- Value = attraction + souvenir, plus 2 if souvenir is 3 or more (R5). Computed once by the expert system.
- Expert rules and order: R1 day length, R2 senior removes high-effort places, R3 travel factor, R5 souvenir boost, R4 removes places that can never fit. `removed` and `fired` record why.
- A* is a maximization search per day. State is (location, time, visited set). `h` is a fractional-knapsack upper bound on remaining value that ignores travel and waiting. Expand highest `f = g + h`.
- **A* goal test:** re-queue a terminal state at priority `g` with a goal flag and return only when a goal entry is popped. Prune by `(location, visited set)` keeping the smallest time.
- Arriving before opening means waiting. Feasible only if `start + duration <= close` and `end <= day_end`.
- Days are planned in sequence; used places are removed. Candidate guard is 15 per day (keep best value per minute).
- Heap entries include an integer tie-breaker. No global randomness; experiments use a seeded `random.Random`.
- Standard library only in the package. Matplotlib only for optional figures.

---

## Commands

```bash
.venv/bin/pytest -q                      # expect: 0 tests until code exists
python -m travelplanner.cli --city tokyo --days 3 --age adult
python -m travelplanner.experiments
```

Test plan (targets, not results): models/config, knowledge, expert, A* (brute-force oracle), Greedy, planner invariants, CLI. See `Design_Doc.md` Section 11.

---

## Current handoff

Next task is **Phase 1, P1.5**: the owner needs to choose the additional high-effort Tokyo seed place so the file reaches the planned 14-place minimum. Do not invent it. Then finish Phase 1 and proceed to Phase 2 (expert system), followed by Phase 3 (search, test-first).

Items needing the owner (do not guess): OI-1 instructor approval of the project, OI-2 which cities, OI-3 place scores, durations, hours, and verification, and OI-4 the additional high-effort Tokyo place.

---

## Viva questions the owner should be able to answer

| Question | Short answer |
|---|---|
| What does it do? | Chooses and orders places to visit each day to maximize value within the time limit |
| Why is it AI? | A utility-based agent picks the best plan, using an expert system and A* search |
| Why A*? | The goal is maximum value under a time limit; A* with an optimistic bound finds the optimum on small candidate sets and is explainable |
| Why not UCS, BFS, DFS? | They minimize cost or ignore value; this is a maximization problem |
| What is the heuristic? | The most extra value still possible in the remaining time, ignoring travel. It is never too low, so A* stays optimal |
| Why a Greedy baseline? | To show on real runs that greedy can miss better combinations |
| Why an expert system? | Age-group handling is knowledge, not search; it also shrinks the search space and explains removals |
| Why not GA or Hill Climbing? | Unnecessary at this size; future work for large cities |
| Where does the data come from? | Hand-written by us; scores are our judgement; checked against official sources |

---

## Known limits and non-issues

- Straight-line travel time understates real transit times; accepted for scope.
- Later days can be thin with a small data file; expected.
- The 15-candidate guard makes a day approximate when it triggers; it is logged.
- The `Design_Doc.md` Section 13 numbers come from random synthetic data, not this project's results.
- `plan_day` takes `day_start_min` and `day_end_min`; this supersedes the earlier analysis file (decision D-008).

## Maintenance rule

Update this file only for project-wide facts: phase status, implemented public interfaces, verified test count, next task, contracts, or a cross-cutting gotcha. Put chronological work in `AGENT_BOARD.md` and task completion in `Roadmap.md`.
