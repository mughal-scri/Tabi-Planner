# Roadmap.md: Japan Travel Planner

Phased build plan. Check a box only when the work exists and its tests pass. Phases are sized for short sessions, not calendar dates. Build in order; never code a later phase before the earlier one passes.

Design details are in `Design_Doc.md`. Status of the moment is in `AGENT_BOARD.md`.

---

## Phase 1: Foundation and data

Goal: package skeleton, shared types, config, the Tokyo data file, and M0 helpers.

- [x] P1.1 Repo scaffold: `travelplanner/`, `tests/`, `data/`, `results/`, `requirements.txt`, `pytest.ini`, `.gitignore`, `README.md`, `CHANGELOG.md`
- [x] P1.2 `models.py`: `Place`, `Profile`, `Stop`, `DayPlan`, `Plan`
- [x] P1.3 `config.py`: `Config` with the defaults in `Design_Doc.md` Section 5
- [x] P1.4 `knowledge.py`: `to_minutes`, `to_clock`, `haversine_km`, `travel_min`, `load_city` with validation
- [ ] P1.5 `data/tokyo.json`: 14 to 18 places from the seed list, `"verified": false`
- [x] P1.6 Tests: models/config and knowledge

P1.5 remains open: 13 named seed locations are present. The design calls for 14 to 18 and identifies the additional high-effort location as the owner's choice; it has not been invented.

Done when: `pytest -q` passes and `load_city("data/tokyo.json")` returns places and the start point.

## Phase 2: Expert system (M1)

Goal: age group to limits and filtered, valued candidates, with explanations.

- [ ] P2.1 `Rule` structure and `default_rules`
- [ ] P2.2 R1 (day length), R2 (senior filter), R3 (travel factor), R5 (souvenir boost), R4 (fit check)
- [ ] P2.3 `apply_rules` returning candidates, window, factor, `removed`, `fired`
- [ ] P2.4 Tests for each rule, rule order, and explanation fields

Done when: each age group gives the expected hours and filtered candidates on the Tokyo file.

## Phase 3: Search (M2 and M3)

Goal: A* and Greedy for one day, proven against a brute-force oracle.

- [ ] P3.1 Test helper: brute-force `brute_force_day` in `tests/` and a seeded random instance generator
- [ ] P3.2 `greedy.py`: `plan_day_greedy`
- [ ] P3.3 `astar.py`: `h_bound` and `plan_day` (including the goal re-queue at f = g)
- [ ] P3.4 Tests: A* equals brute force on 30 seeded instances; windows and waiting; budget never exceeded; goal re-queue regression; Greedy at most A*
- [ ] P3.5 Measure states and time at 10, 12, 15 candidates; compare with `Design_Doc.md` Section 13

Done when: A* matches the oracle on every seeded instance and a 15-candidate day finishes under 1 second.

## Phase 4: Trip pipeline and CLI

Goal: multi-day planning, formatted output, command-line entry point.

- [ ] P4.1 `planner.py`: `plan_trip` (rules once, day loop, remove used places, unused list, candidate cap)
- [ ] P4.2 `format_plan` with the sample layout, unverified-data note, not-scheduled reasons
- [ ] P4.3 `cli.py`: arguments, validation, exit code 2 on bad input
- [ ] P4.4 Tests: invariants on full plans for 1, 3, 5 days and all three age groups; CLI tests

Done when: `python -m travelplanner.cli --city tokyo --days 3 --age adult` prints a valid itinerary.

## Phase 5: Evaluation and report

Goal: the two experiments and the material for the report and viva.

- [ ] P5.1 `experiments.py`: E1 (A* vs Greedy) and E2 (rules on and off) as printed tables
- [ ] P5.2 Optional figures `results/fig_e1.png` and `results/fig_e2.png`
- [ ] P5.3 Verify the Tokyo data against official sources and set `"verified": true`
- [ ] P5.4 README: what it is, setup, run, test
- [ ] P5.5 Report notes: architecture, algorithm justification table, E1 and E2 results (use real numbers only)
- [ ] P5.6 Viva check: owner can answer the questions in `PROJECT_MEMORY.md` without notes

Done when: tests pass, tables exist, and the data is verified.

## Phase 6: Optional extras

Only after Phase 5 and only if there is time.

- [ ] P6.1 `data/kyoto.json` and `data/osaka.json` (data only; no code change expected)
- [ ] P6.2 Route plot (Matplotlib scatter with day colors)
- [ ] P6.3 Add a return-to-hotel check as a config flag (see `Future_Enhancements.md`)

---

## Definition of done (every phase)

1. Tests for the phase exist and pass; full suite passes.
2. `AGENT_BOARD.md` status table, repo map, and activity log updated.
3. `PROJECT_MEMORY.md` updated if project-wide state changed.
4. Roadmap boxes checked.
5. No scope added beyond the PRD.
