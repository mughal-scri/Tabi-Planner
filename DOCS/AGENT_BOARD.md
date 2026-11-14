# AGENT_BOARD.md: Japan Travel Planner

The shared whiteboard. Every agent reads this before starting and updates it before stopping (protocol: `RULES.md` Section 8). Newest log entries go at the top of the Activity Log.

**Last updated:** 2026-11-14 by Codex (Phase 3 search)

---

## 1. Quick start

1. Read `DOCS/RULES.md`, this board, and `DOCS/PROJECT_MEMORY.md`. Do not scan the repository.
2. Work the first unchecked task in `DOCS/Roadmap.md`. Use only that module's section in `DOCS/Design_Doc.md`, its source file, and its test file.
3. Test first for rules and search. Run `.venv/bin/pytest -q` before you stop.
4. Update this board (log, status, repo map), `Roadmap.md` checkboxes, and `PROJECT_MEMORY.md` if project-wide facts changed.

**Project in one line:** a command-line Japan travel planner for one city or an ordered multi-city route. An expert system (R1 to R6) sets limits by age group and boosts places in the user's chosen interest categories; A* (maximization form) plans each day to maximize value; city-to-city transfers shift the first day in a new city; Greedy is the comparison baseline. Data: `data/japan_travel_dataset.json` (12 cities, 135 places, unverified).

## 2. Current status

| Phase | Module or task | Status | Tests | Last touched | Notes |
|---|---|---|---|---|---|
| Docs | Eight-document set | UPDATED | n/a | 2026-11-13 | Rewritten for multi-city trips and the master dataset (decisions D-013 to D-017) |
| 1 | Foundation and data (multi-city) | DONE | 15 passed | 2026-11-14 | P1.1 to P1.9 complete; master dataset preserved, loader validates its schema |
| 2 | `expert.py` (M1) | DONE | 22 passed | 2026-11-14 | R1-R6, ordered execution, candidate values, removal/fired explanations |
| 3 | `greedy.py` and `astar.py` (M3, M2) | DONE | 88 passed | 2026-11-14 | Oracle verified on 30 seeded cases; all 36 real city/age runs under 1 sec |
| 4 | `planner.py` and `cli.py` | NOT STARTED | 0 | n/a | |
| 4B | Interests and local web UI (`server.py`, `web/`) | NOT STARTED | 0 | n/a | Build after Phase 4; bubble pool, three-step flow |
| 5 | `experiments.py`, report material | NOT STARTED | 0 | n/a | E1, E2, E3 |
| 6 | Optional extras | NOT STARTED | 0 | n/a | Only after Phase 5 |

Full-suite test count: **88 passed** (`python3 -m pytest -q`). `.venv/bin/pytest` is unavailable in this workspace.

## 3. Repo map

Items marked "(planned)" do not exist yet. Remove the mark when the file is created.

```
DOCS/                          eight markdown docs (exist)
travelplanner/__init__.py      version 0.1.0
travelplanner/config.py        Config dataclass (multi-city limits and transfer/interests tunables)
travelplanner/models.py        Place, City, Profile, Transfer, Stop, DayPlan, Plan
travelplanner/knowledge.py     M0 helpers; dataset/city/category loaders and transfer calculations
travelplanner/expert.py        M1 ordered expert rules and per-city `apply_rules`
travelplanner/astar.py         M2 A* day search and fractional-knapsack upper bound
travelplanner/greedy.py        M3 greedy value-per-minute baseline
travelplanner/planner.py       (planned)
travelplanner/cli.py           (planned)
travelplanner/server.py        (planned) local web server and JSON API, stdlib only
travelplanner/experiments.py   (planned)
data/japan_travel_dataset.json owner-supplied master dataset, 12 cities, 135 places, verified=false
tests/test_models_config.py
tests/test_knowledge.py
tests/test_server.py        (planned)
web/index.html, web/styles.css, web/app.js   (planned) single-page UI, plain HTML/CSS/JS
results/                       output directory
README.md, CHANGELOG.md, requirements.txt, pytest.ini, .gitignore
```

## 4. Commands

```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
.venv/bin/pytest -q
.venv/bin/pytest -q tests/test_astar.py
python -m travelplanner.cli --route tokyo:3,kyoto:2,osaka:2 --age adult   # Phase 4
python -m travelplanner.cli --city tokyo --days 3 --age adult             # Phase 4, single city
python -m travelplanner.server                                      # Phase 4B, http://127.0.0.1:8000
python -m travelplanner.experiments                                 # Phase 5
```

## 5. Conventions (short form; full list in `Design_Doc.md` Section 3)

- Minutes since midnight for all times; `(lat, lon)` for coordinates; haversine km.
- Travel minutes = km / speed * 60 * factor; factor applies to travel only.
- Value is set once by the expert system (R5 souvenir boost, R6 interest boost) and never recomputed in search.
- Interests = category ids from the dataset's root `categories` (58). R6 adds `interest_boost` (8.0) to a matching place's value; empty interests change nothing. Exact id match.
- Transfer between cities = anchor-to-anchor km / 150 km/h * 60 + 30 min; it delays the start of the first day in the new city. Place `id` is the cross-trip key.
- All tunables in `Config`. Standard library only in the package.
- No global randomness; experiments use a seeded `random.Random`.

## 6. Open issues

| ID | Issue | Owner | Status |
|---|---|---|---|
| OI-1 | Confirm with the instructor that this project is acceptable, and what the report and viva require | Owner | Open |
| OI-2 | Which cities are in scope | Owner | Closed: the master dataset has 12 cities and the user supplies the route (D-013, D-015) |
| OI-5 | Interest bubbles match one exact category id (58 fine-grained ids, for example `temple` and `temple_garden` are separate). Decide whether to keep that or group related categories into broader bubbles (FE-13) | Owner | Open, default is exact (D-019) |
| OI-3 | Verify the dataset (hours, coordinates, durations) against official sources for the cities used in the demo; scores are editorial estimates | Owner | Open |
| OI-4 | Choose the additional high-effort Tokyo seed place | Owner | Closed: obsolete, the dataset has 18 Tokyo places |

## 7. Decisions

| ID | Decision | Date |
|---|---|---|
| D-001 | One city per trip; no multi-city travel. **Superseded by D-013** | 2026-11-13 |
| D-002 | Final AI model is a utility-based agent: expert system plus A* search; no learning component | 2026-11-13 |
| D-003 | A* is used in maximization form with an admissible upper bound (fractional knapsack ignoring travel); terminal states are re-queued at f = g before the goal test | 2026-11-13 |
| D-004 | Greedy is the baseline for comparison only | 2026-11-13 |
| D-005 | Travel time inside a city is straight-line distance at 20 km/h (times 1.3 for seniors); no map API. City-to-city time is in D-014 | 2026-11-13 |
| D-006 | The day ends at the last visit; no return-to-hotel leg | 2026-11-13 |
| D-007 | Days are planned in sequence; places used on one day are removed for later days; each city has its own pool | 2026-11-13 |
| D-008 | `plan_day` takes `day_start_min` and `day_end_min` instead of the earlier analysis file's `budget_min`, because opening windows need absolute times. This supersedes the analysis file | 2026-11-13 |
| D-009 | Per-day candidate guard of 20 (was 15; keep the best by value per minute), because search time grows quickly beyond that; the day is then approximate and the rules log records it. Raised so Tokyo's 18 places fit | 2026-11-13 |
| D-010 | Value = attraction + souvenir, plus 2 if souvenir is 3 or more | 2026-11-13 |
| D-011 | Package uses only the Python standard library; Matplotlib only for optional figures | 2026-11-13 |
| D-012 | Place data is flagged `"verified": false` until the owner confirms it | 2026-11-13 |
| D-013 | Trips are multi-city: the user supplies an ordered route (1 to 5 cities, 1 to 5 days each, at most 10 days). No automatic city selection or ordering in the core build | 2026-11-13 |
| D-014 | City-to-city transfer = anchor-to-anchor haversine km / 150 km/h * 60 + 30 min. It is taken on the first day in the new city, in the morning: that day's start becomes 09:00 plus the transfer. The day end does not move | 2026-11-13 |
| D-015 | The owner-supplied master dataset `data/japan_travel_dataset.json` (schema 2.0.0, 12 cities, 135 places) replaces `data/tokyo.json` and the per-city file design. The loader iterates `data["cities"]` | 2026-11-13 |
| D-016 | A city may appear at most once in a route; place `id` is the cross-trip key | 2026-11-13 |
| D-017 | A day with no schedulable place is still listed with no stops; planning never stops early (a long transfer day can be empty while the next day is full) | 2026-11-13 |
| D-018 | `apply_rules(places, age_group, interests, cfg)` takes an age group and the interests (not a profile) and runs once per city in the route | 2026-11-13 |
| D-019 | Interest preferences: the user may select dataset category ids (optional, multi-select). Rule R6 adds `interest_boost` = 8.0 to the value of every place in a selected category. It is a soft boost, not a filter, and A* is unchanged. Boost 4 barely changed plans and 8 clearly did (`Design_Doc.md` Section 13.2). Matching is exact on category id | 2026-11-13 |
| D-020 | A local web UI is in scope: one page, plain HTML, CSS, and JavaScript in `web/`, served by a standard-library `http.server` on 127.0.0.1 with a small JSON API. Three steps (trip, interests, itinerary). Interests are toggle bubbles in a pool, never a drop-down. Built in Phase 4B after the CLI works | 2026-11-13 |
| D-021 | The `autonomous-ui-architect` skill is applied to `web/` within this stack: tokens, states, accessibility, validation loop yes; React, Tailwind, shadcn/ui, TypeScript no. `Tech_Stack_DOC.md` wins on conflicts | 2026-11-13 |
| D-022 | The bubble pool shows only categories that have at least one place in the chosen cities; bubble size follows the place count (tiers 1, 2 to 3, 4 or more) | 2026-11-13 |

## 8. Gotchas

- **A* goal test:** a terminal state's queue priority is `g + h`, which overestimates it. Re-queue it with priority `g` and an `is_goal` flag, and return only when a goal entry is popped. Without this the first version matched brute force on only 11 of 40 instances.
- **Pruning key:** `(location, visited set)` with the smallest time seen is valid because value depends only on the visited set and arriving earlier is never worse (waiting is allowed).
- **Heap ties:** include an integer counter in heap entries; never compare dataclasses or path tuples.
- **Window check:** a visit is feasible only if `start + duration <= close` and `end <= day_end`, where `start = max(arrival, open)`.
- **Senior factor:** applies to travel time only, never to visit durations.
- **Expert rule order:** R1, R2, R3, R5, R4. R4 needs the day window from R1.
- **Prototype numbers are not results:** the figures in `Design_Doc.md` Section 13 came from random synthetic data. Do not quote them as this project's results.
- **Thin later days:** cities have 8 to 18 places, so a third or later day in one city may have few or no stops. This is expected; empty days are listed.
- **Transfer shift:** the first day in a new city starts at `day_start_min + transfer minutes`; the day end is unchanged. The senior travel factor does not apply to the transfer.
- **Dataset schema:** the root has a `cities` array, so a loader that expects a single city object will fail. Souvenir scores in the file are 1 to 5, attraction 7 to 10. Many extra fields exist; ignore them (`Design_Doc.md` Section 4.1).
- **Interest pool:** build it from the chosen cities only (for example 25 of the 58 categories for Tokyo, Kyoto, and Osaka). Unknown interest ids are a `ValueError`. The category label comes from the root `categories` list.
- **Web UI:** no `<select>` anywhere; never put API data in `innerHTML`; the server binds to 127.0.0.1 only and serves a fixed file whitelist; the API returns `HH:MM` strings.
- **Stale analysis file:** `travel_planner_detailed_analysis.md` describes the old single-city scope; do not implement from it.
- **Late-start days:** R4 uses the nominal day start, so a late arrival day just finds fewer feasible places in the search; do not add a second filter for it.

## 9. Activity log (newest first)

### 2026-11-14 | Codex | Completed Phase 3 search
- Did: implemented Greedy and maximization-form A*, with the required terminal goal re-queue; added the tests-only brute-force oracle, seeded generator, and search regression/constraint coverage.
- Files: `travelplanner/astar.py`, `travelplanner/greedy.py`, `tests/test_astar.py`, `tests/test_greedy.py`, Roadmap and status docs.
- Verified: `python3 -m pytest -q` -> 88 passed; `git diff --check` passed. A* matched brute force on 30 seeded 7-place cases. 36 city/age runs finished below 1 second (maximum 0.270 s: Kyoto youth, 14 candidates, 10,300 expanded states).
- Notes: fixed-seed synthetic measurements: 10 candidates 286 states / 0.006 s; 15 candidates 5,164 / 0.145 s; 20 candidates 2,482 / 0.115 s. Timings vary by instance and machine. These are implementation measurements, distinct from Design_Doc Section 13 prototype figures.
- Next: Phase 4 multi-city planner and CLI.

### 2026-11-14 | Codex | Completed Phase 2 expert system
- Did: implemented ordered R1-R6 rules, base and boosted candidate values, senior and fit removals, and `fired`/`removed` explanations; added rule coverage tests.
- Files: `travelplanner/expert.py`, `tests/test_expert.py`, Roadmap and status docs.
- Verified: `python3 -m pytest -q` -> 22 passed. `.venv/bin/pytest` remains unavailable (no project venv).
- Notes: rules are applied once per call (the planner will call once per city); R4 checks the nominal day window as specified.
- Next: Phase 3, Greedy and A* search.

### 2026-11-14 | Codex | Completed Phase 1 multi-city migration
- Did: migrated models/config and M0 to the owner-supplied master dataset; added schema validation, category pools, and intercity transfers; replaced single-city tests.
- Files: `travelplanner/models.py`, `config.py`, `knowledge.py`, `tests/`, Roadmap and status docs. Master dataset was already present; obsolete Tokyo seed was already retired.
- Verified: `python3 -m pytest -q` -> 15 passed. `.venv/bin/pytest -q` unavailable (no project venv).
- Notes: retained dataset content unchanged and unverified. Full documented validation paths covered for schema, duplicates, scores, effort, duration, category, time window, and required fields.
- Next: Phase 2 expert system (M1).

### 2026-11-13 | Claude | Added interest preferences (category bubbles) and the local web UI to the docs
- Did: added optional interest categories (rule R6, `interest_boost` 8.0), the bubble-pool selector, and a local web UI with a small JSON API, across PRD, Design_Doc (new Section 16, E3, Section 13.2), Tech_Stack_DOC, Roadmap (Phase 4B), RULES, Future_Enhancements, this board, and PROJECT_MEMORY.
- Files: the eight markdown docs. No repo code changed.
- Verified: prototype on the real dataset calibrated the boost: with 8, matching stops rose in 4 of 6 cases (for example Tokyo museum + park + garden 0 of 6 to 2 of 6) and never fell; with 4 the change was small. Prototype numbers only; no repo tests changed (11 passed, single-city form).
- Notes: this is a real scope increase (about 450 Python lines plus about 400 web lines). The UI is isolated in Phase 4B, so the core can ship without it. OI-5 asks the owner whether exact category matching is acceptable.
- Next: unchanged, P1.5 then P1.7 to P1.9.

### 2026-11-13 | Claude | Extended the docs to multi-city trips and the master dataset
- Did: reviewed the Codex edits (Phase 1 status only; Design_Doc unchanged) and the owner's `japan_travel_dataset.json` (12 cities, 135 places, schema 2.0.0, all unverified). Updated PRD, Design_Doc, Roadmap, Tech_Stack_DOC, Future_Enhancements, RULES, this board, and PROJECT_MEMORY for multi-city routes, inter-city transfers, and the dataset. Added P1.7 to P1.9 to migrate the Phase 1 code; closed OI-2 and OI-4.
- Files: the eight markdown docs. No repo code changed.
- Verified: prototype outside the repo on the real dataset: A* beat or matched Greedy in 36 of 36 day-1 runs (Greedy strictly worse in 26); slowest day 0.05 s; a Tokyo 3, Kyoto 2, Osaka 2 route ran with transfers of 179 and 46 minutes. Numbers are in `Design_Doc.md` Section 13.1 and are prototype results only. Repo test count is unchanged (11 passed, single-city form).
- Notes: Phase 1 code still has the single-city `Profile`, `Place`, and loader, and `data/tokyo.json`; they need the migration in P1.5 and P1.7 to P1.9 before Phase 2.
- Next: P1.5, add the master dataset to `data/` and retire `data/tokyo.json`; then P1.7 to P1.9.

### 2026-11-13 | Codex | Started Phase 1 foundation
- Did: created package scaffold, shared models/config, M0 helpers, Tokyo placeholder data, and 11 tests. P1.1-P1.4 and P1.6 are complete.
- Files: `travelplanner/`, `tests/`, `data/tokyo.json`, setup files, Phase 1 status docs.
- Verified: `.venv/bin/python -m pytest -q` -> 11 passed.
- Notes: data has 13 seed places. The 14th high-effort place is explicitly the owner's choice; kept unfilled rather than inventing data. `verified` remains false. Dependency installation could not reach PyPI, so the venv uses available system packages; Matplotlib is not installed.
- Next: owner selects high-effort seed place; then finish P1.5 and proceed with Phase 2.

### 2026-11-13 | Claude | Created the eight-document set
- Did: wrote PRD, Design_Doc, Tech_Stack_DOC, Roadmap, Future_Enhancements, RULES, AGENT_BOARD, PROJECT_MEMORY for the Japan Travel Planner. Prototyped the planner outside the repo to check the spec.
- Files: the eight markdown docs only. No repo code exists yet.
- Verified: prototype A* matched a brute-force oracle on 40 of 40 random 8-place instances; the heuristic bound was never below the optimum; greedy was below A* on 23 of 40. A first prototype version without the goal re-queue matched on only 11 of 40, which led to D-003 and the Section 8.3 requirement. Timing numbers are in `Design_Doc.md` Section 13. Test count in the repo: 0.
- Notes: Tokyo seed coordinates are approximate; scores, durations, and hours are placeholders (OI-3). Open items OI-1 and OI-2 need the owner.
- Next: P1.1, create the repo scaffold.

## 10. Archive

(Empty. Compact the oldest log entries here as a few summary lines once the log passes about 15 entries.)
