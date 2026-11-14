# Roadmap.md: Japan Travel Planner

Phased build plan. Check a box only when the work exists and its tests pass. Phases are sized for short sessions, not calendar dates. Build in order; never code a later phase before the earlier one passes.

Design details are in `Design_Doc.md`. Status of the moment is in `AGENT_BOARD.md`.

---

## Phase 1: Foundation and data (multi-city)

Goal: package skeleton, shared types, config, the master dataset, and M0 helpers, including city-to-city transfers.

P1.1 to P1.4 and P1.6 were completed in the earlier single-city form (11 tests). P1.5 and P1.7 to P1.9 migrate that work to the multi-city design in `Design_Doc.md` Sections 4 to 6. Do P1.5 first.

- [x] P1.1 Repo scaffold: `travelplanner/`, `tests/`, `data/`, `results/`, `requirements.txt`, `pytest.ini`, `.gitignore`, `README.md`, `CHANGELOG.md`
- [x] P1.2 `models.py`: first version (single-city form)
- [x] P1.3 `config.py`: first version (single-city form)
- [x] P1.4 `knowledge.py`: first version (`to_minutes`, `to_clock`, `haversine_km`, `travel_min`, single-city `load_city`)
- [x] P1.5 Add `data/japan_travel_dataset.json` (owner-supplied, 12 cities, 135 places, `"verified": false`) and retire `data/tokyo.json`
- [x] P1.6 Tests: models/config and knowledge (single-city form)
- [x] P1.7 Migrate `models.py` and `config.py`: add `City`, `Transfer`; `Place` gains `id`, `area`, `location_scope`, `category`; `Profile.route` replaces `days` and `Profile.interests` is added; `DayPlan` gains `city_id`, `start_min`, `transfer`; `Plan` per Section 4; `Config` gains the intercity, `max_cities`, `max_days_per_city`, `max_total_days`, `interest_boost` (8.0) fields and cap 20 (remove `max_days`)
- [x] P1.8 Migrate `knowledge.py`: `load_dataset`, `load_city(path, city_id)`, `intercity`, `load_categories`, `category_pool`, with the validation in Section 4.1
- [x] P1.9 Update tests: dataset loading (12 cities, 135 unique place ids, 58 categories, category pool), validation errors, `intercity` (symmetric; Tokyo to Kyoto about 179 min), Config limits; drop the `tokyo.json` tests

Done when: `load_dataset("data/japan_travel_dataset.json")` returns 12 cities and 135 places, `intercity` gives the expected transfer, and `pytest -q` passes.

## Phase 2: Expert system (M1)

Goal: age group to limits and filtered, valued candidates, with explanations.

- [x] P2.1 `Rule` structure and `default_rules`
- [x] P2.2 R1 (day length), R2 (senior filter), R3 (travel factor), R5 (souvenir boost), R6 (interest boost), R4 (fit check)
- [x] P2.3 `apply_rules(places, age_group, interests, cfg)` returning candidates, window, factor, `removed`, `fired`
- [x] P2.4 Tests for each rule (R6 with and without interests), rule order, and explanation fields

Done when: each age group gives the expected hours and filtered candidates on the Tokyo data from the master dataset.

## Phase 3: Search (M2 and M3)

Goal: A* and Greedy for one day, proven against a brute-force oracle.

- [ ] P3.1 Test helper: brute-force `brute_force_day` in `tests/` and a seeded random instance generator
- [ ] P3.2 `greedy.py`: `plan_day_greedy`
- [ ] P3.3 `astar.py`: `h_bound` and `plan_day` (including the goal re-queue at f = g)
- [ ] P3.4 Tests: A* equals brute force on 30 seeded instances; windows and waiting; late `day_start`; budget never exceeded; goal re-queue regression; Greedy at most A*
- [ ] P3.5 Measure states and time at 10, 15, 20 candidates and on every city of the real dataset; compare with `Design_Doc.md` Section 13

Done when: A* matches the oracle on every seeded instance and every day on the real dataset finishes under 1 second.

## Phase 4: Trip pipeline (multi-city) and CLI

Goal: multi-city, multi-day planning, formatted output, command-line entry point.

- [ ] P4.1 `planner.py`: `plan_trip` (route and interest validation, rules once per city with the interests, transfer on each city's first day, day loop, remove used places, empty days still listed, unused and removed per city, candidate cap)
- [ ] P4.2 `format_plan` with the sample layout: per-day city heading, transfer lines, `[day trip]` and `[matches interest]` marks, interests line, unverified-data note, not-scheduled reasons
- [ ] P4.3 `cli.py`: `--route` and `--city/--days` (mutually exclusive), `--age`, `--interests`, `--algorithm`, `--data`; exit code 2 on bad input
- [ ] P4.4 Tests: invariants on full single- and multi-city plans (1, 3, 5 days, all age groups); route and interest validation errors; interests raise matching stops; single-city equivalence; CLI tests

Done when: `python -m travelplanner.cli --route tokyo:3,kyoto:2,osaka:2 --age adult` prints a valid itinerary with transfers, and `--city tokyo --days 3 --age adult` still works.

## Phase 4B: Interests and local web UI

Goal: a local web page where the user picks cities, days, age group, and interest bubbles, then sees the itinerary. Build only after Phase 4 passes. The CLI and its tests must keep working.

- [ ] P4B.1 `planner.py`: `plan_to_dict(plan)` (Design_Doc Section 16.2)
- [ ] P4B.2 `server.py`: `/`, `/styles.css`, `/app.js`, `/api/cities`, `/api/categories`, `/api/plan`; localhost only; 64 KB body limit; static whitelist
- [ ] P4B.3 `tests/test_server.py` (Design_Doc Section 11)
- [ ] P4B.4 `web/styles.css`: tokens in `:root`, light and dark themes, bubble pool, chips, cards, focus and reduced-motion rules
- [ ] P4B.5 `web/index.html` and `web/app.js`: Step 1 trip (city chips, days steppers, age chips), Step 2 interest bubble pool (toggle, counter, Clear, Skip, Continue), Step 3 itinerary (day cards, transfer rows, tags, totals, banner), loading and error states; no drop-down
- [ ] P4B.6 Manual UI checklist (Design_Doc Section 16.4) run and logged on the board

Done when: `python -m travelplanner.server` serves the page, the whole flow works in a browser, the server tests pass, and the checklist is logged.

## Phase 5: Evaluation and report

Goal: the two experiments and the material for the report and viva.

- [ ] P5.1 `experiments.py`: E1 (A* vs Greedy over 12 cities x 3 age groups, plus sample multi-city routes), E2 (rules on and off), and E3 (interest boost 0 versus 8) as printed tables
- [ ] P5.2 Optional figures `results/fig_e1.png` and `results/fig_e2.png`
- [ ] P5.3 Verify the dataset (hours, coordinates, durations) against official sources for the cities used in the demo and set their `verified` flags
- [ ] P5.4 README: what it is, setup, run, test
- [ ] P5.5 Report notes: architecture, algorithm justification table, E1 and E2 results (use real numbers only)
- [ ] P5.6 Viva check: owner can answer the questions in `PROJECT_MEMORY.md` without notes

Done when: tests pass, tables exist, and the demo cities' data is verified.

## Phase 6: Optional extras

Only after Phase 5 and only if there is time.

- [ ] P6.1 `suggest_city_order(city_ids, cfg)`: try every order of up to 6 chosen cities (first city fixed) and return the one with the smallest total transfer time; a `--auto-order` CLI flag
- [ ] P6.2 Route plot (Matplotlib scatter with day colors)
- [ ] P6.3 Add a return-to-hotel check as a config flag (see `Future_Enhancements.md`)

---

## Definition of done (every phase)

1. Tests for the phase exist and pass; full suite passes.
2. `AGENT_BOARD.md` status table, repo map, and activity log updated.
3. `PROJECT_MEMORY.md` updated if project-wide state changed.
4. Roadmap boxes checked.
5. No scope added beyond the PRD.
