# Project Memory: Japan Travel Planner

**Purpose:** the compact, current handoff for a new agent. Read this after `RULES.md` and `AGENT_BOARD.md`; do **not** scan the repository to learn project state. This is a memory aid, not a replacement for `Design_Doc.md`.

**Snapshot:** 2026-11-14. Phases 1 and 2 are complete for the multi-city planner. The master dataset, data layer, expert rules R1-R6, and their tests are implemented. Full suite: 22 passed with `python3 -m pytest -q`.

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
| Documentation set | **Complete, updated for multi-city** | Eight markdown files; decisions D-013 to D-018 |
| Phase 1 foundation and data | **Complete** | P1.1-P1.9 done; 15 tests pass; dataset remains unverified |
| Phase 2 expert system | **Complete** | R1-R6 implemented; expert coverage included in 22 passing tests |
| Phase 3 search (A*, Greedy) | Not started | Logic is prototype-verified in `Design_Doc.md` Section 8.6 |
| Phase 4 pipeline (multi-city) and CLI | Not started | |
| Phase 4B interests UI (bubble pool, local web page) | Not started | Build after Phase 4; `server.py`, `web/` |
| Phase 5 evaluation and report | Not started | |
| Phase 6 optional extras | Not started | Only after Phase 5 |

**What the project is:** a travel planner for Japan (command line and a local web page). Input: an ordered route (1 to 5 cities, 1 to 5 days each, at most 10 days; for example `tokyo:3,kyoto:2,osaka:2`) or a single city with days, plus an age group (youth, adult, senior), and optionally interest categories picked as bubbles (for example shrines, markets). Output: a day-by-day itinerary that maximizes total value (attractions plus souvenirs) within each day's time limit and opening hours, with a transfer between consecutive cities. An expert system sets limits by age group and boosts places in the chosen categories (R6); A* searches each day; Greedy is the comparison baseline. Utility-based agent; no learning. Data: `data/japan_travel_dataset.json` (12 cities, 135 places, unverified).

---

## Planned surface: use these contracts

Implemented files are listed in the current repo map in `AGENT_BOARD.md`. The rows below show current or planned multi-city contracts (`Design_Doc.md` Sections 4 to 6 and 10).

| File | Main entry points |
|---|---|
| `travelplanner/models.py` | `Place` (adds `id`, `area`, `location_scope`), `City`, `Profile` (`age_group`, `route`), `Transfer`, `Stop`, `DayPlan` (adds `city_id`, `start_min`, `transfer`), `Plan` |
| `travelplanner/config.py` | `Config()` (all tunables, including `intercity_speed_kmh`, `intercity_buffer_min`, `max_cities`, `max_days_per_city`, `max_total_days`, `max_candidates_per_day` = 20) |
| `travelplanner/knowledge.py` | `to_minutes`, `to_clock`, `haversine_km`, `travel_min`, `load_dataset(path)`, `load_city(path, city_id)`, `intercity(a, b, cfg)`, `load_categories(path)`, `category_pool(cities, labels, city_ids)` |
| `travelplanner/expert.py` | `Rule`, `default_rules`, `apply_rules(places, age_group, interests, cfg)` (returns candidates, day window, travel factor, `removed`, `fired`; runs once per city) |
| `travelplanner/astar.py` | `h_bound`, `plan_day(candidates, start, day_start_min, day_end_min, speed_kmh, factor)` returns `(stops, value, expanded)` |
| `travelplanner/greedy.py` | `plan_day_greedy` with the same signature as `plan_day` |
| `travelplanner/planner.py` | `plan_trip(dataset_path, profile, cfg, algorithm)` (multi-city), `format_plan(plan)` |
| `travelplanner/cli.py` | `python -m travelplanner.cli --route tokyo:3,kyoto:2 --age adult [--interests shrine,market] [--algorithm astar\|greedy] [--data PATH]`, or `--city tokyo --days 3` for one city |
| `travelplanner/server.py` | Local API on 127.0.0.1: `GET /api/cities`, `GET /api/categories?cities=`, `POST /api/plan`, plus the three static files in `web/`; `plan_to_dict(plan)` in `planner.py` |
| `web/index.html`, `web/styles.css`, `web/app.js` | Three-step page: trip, interest bubble pool, itinerary; plain HTML, CSS, and JavaScript; no drop-downs |
| `travelplanner/experiments.py` | E1 (A* vs Greedy), E2 (rules on and off), E3 (interest boost 0 versus 8) |

---

## Facts that must not be re-derived

- Time is minutes since midnight (`540` = 09:00). Day starts 09:00; day length is 10, 8, or 6 hours for youth, adult, senior (rule R1). The day ends at the last visit; no return to the hotel.
- Travel minutes = haversine km / 20 km/h * 60 * factor. Factor is 1.0, or 1.3 for seniors, applied to travel only.
- Value = attraction + souvenir, plus 2 if souvenir is 3 or more (R5), plus 8 if the place's category is one of the user's selected interests (R6). Computed once by the expert system.
- Expert rules and order: R1 day length, R2 senior removes high-effort places, R3 travel factor, R5 souvenir boost, R4 removes places that can never fit. `removed` and `fired` record why.
- A* is a maximization search per day. State is (location, time, visited set). `h` is a fractional-knapsack upper bound on remaining value that ignores travel and waiting. Expand highest `f = g + h`.
- **A* goal test:** re-queue a terminal state at priority `g` with a goal flag and return only when a goal entry is popped. Prune by `(location, visited set)` keeping the smallest time.
- Arriving before opening means waiting. Feasible only if `start + duration <= close` and `end <= day_end`.
- Days are planned in sequence; used places are removed; each city has its own pool and appears at most once in a route. Place `id` is the cross-trip key. Candidate guard is 20 per day (keep best value per minute).
- **Interests:** category ids from the dataset's root `categories` (58 id and label pairs; each place has one `category`). The bubble pool shows only categories present in the chosen cities. R6 adds `interest_boost` = 8.0 to matching places' values (exact id match; empty interests change nothing). Soft boost, not a filter; A* unchanged.
- **Web UI:** one page, plain HTML, CSS, and JavaScript; stdlib `http.server` on 127.0.0.1; tokens in `:root`; no drop-down, no CDN, no `innerHTML` with API data; checklist in `Design_Doc.md` Section 16.4. Built in Phase 4B after the CLI works.
- **City-to-city transfer** = anchor-to-anchor haversine km / 150 km/h * 60 + 30 min. It is taken on the first day in the new city: that day starts at 09:00 plus the transfer; the day end does not move. A day with nothing schedulable is still listed (no early stop).
- Dataset: root `cities` array, each city has `start` (anchor) and `places`; planner uses only the fields listed in `Design_Doc.md` Section 4.1. It is unverified; never edit its content without the owner.
- Heap entries include an integer tie-breaker. No global randomness; experiments use a seeded `random.Random`.
- Standard library only in the package. Matplotlib only for optional figures.

---

## Commands

```bash
.venv/bin/pytest -q                      # currently 22 (Phases 1 and 2 complete)
python -m travelplanner.cli --route tokyo:3,kyoto:2,osaka:2 --age adult
python -m travelplanner.cli --city tokyo --days 3 --age adult
python -m travelplanner.server          # Phase 4B, http://127.0.0.1:8000
python -m travelplanner.experiments
```

Test plan (targets, not results): models/config, knowledge, expert, A* (brute-force oracle), Greedy, planner invariants, CLI. See `Design_Doc.md` Section 11.

---

## Current handoff

Next task is **Phase 3, search (M2 and M3)**: add the tests-only brute-force oracle and seeded instances, then implement Greedy and A* with the goal re-queue requirement. Phase 2 exposes `default_rules` and `apply_rules(places, age_group, interests, cfg)` in `travelplanner.expert`; Phase 1 exposes dataset/category loaders and transfer helpers in `travelplanner.knowledge`.

Items needing the owner (do not guess): OI-1 instructor approval of the project, and OI-3 verification of the dataset's hours, coordinates, and durations (scores are editorial estimates). OI-5 (exact versus grouped interest categories) is open with a default. OI-2 and OI-4 are closed.

---

## Viva questions the owner should be able to answer

| Question | Short answer |
|---|---|
| What does it do? | Chooses and orders places to visit each day, across one or several cities, to maximize value within the time limit |
| Why is it AI? | A utility-based agent picks the best plan, using an expert system and A* search |
| Why A*? | The goal is maximum value under a time limit; A* with an optimistic bound finds the optimum on small candidate sets and is explainable |
| Why not UCS, BFS, DFS? | They minimize cost or ignore value; this is a maximization problem |
| What is the heuristic? | The most extra value still possible in the remaining time, ignoring travel. It is never too low, so A* stays optimal |
| Why a Greedy baseline? | To show on real runs that greedy can miss better combinations |
| Why an expert system? | Age-group handling is knowledge, not search; it also shrinks the search space and explains removals |
| Why not GA or Hill Climbing? | Unnecessary at this size; future work for large cities |
| How are multiple cities handled? | The user gives the order and days; the planner adds a transfer time (distance at 150 km/h plus 30 min) that delays the first day in the new city, then plans each day with A* |
| Why not search over cities too? | Out of scope for the core build; the user chooses the route. Automatic city choice is a listed future enhancement |
| How do preferences work? | The user picks category bubbles; rule R6 adds a fixed bonus to the value of places in those categories, so A* naturally prefers them when they fit the time; it is a soft boost, not a filter |
| Why a web page? | It gives the bubble selector with no extra tools: plain HTML, CSS, and JavaScript served by the Python standard library; the CLI still works |
| Where does the data come from? | An owner-supplied dataset (generated with ChatGPT); scores are editorial estimates; hours and coordinates are checked against official sources before the demo |

---

## Known limits and non-issues

- Straight-line travel time understates real transit times; accepted for scope.
- Later days can be thin: cities have 8 to 18 places; expected, and empty days are listed.
- The 20-candidate guard makes a day approximate when it triggers; it is logged. Tokyo's 18 places do not trigger it.
- Interest matching is exact on 58 fine-grained categories; users may need several bubbles for one idea (FE-13).
- City-to-city time is a rough straight-line proxy (Tokyo to Sapporo is really a flight); accepted.
- Days are optimized one at a time, so total value is a sum of daily optima; accepted.
- The `Design_Doc.md` Section 13 numbers come from prototypes (synthetic data and the real dataset), not this project's results.
- `plan_day` takes `day_start_min` and `day_end_min`; this supersedes the earlier analysis file (decision D-008).

## Maintenance rule

Update this file only for project-wide facts: phase status, implemented public interfaces, verified test count, next task, contracts, or a cross-cutting gotcha. Put chronological work in `AGENT_BOARD.md` and task completion in `Roadmap.md`.
