# AGENT_BOARD.md: Japan Travel Planner

The shared whiteboard. Every agent reads this before starting and updates it before stopping (protocol: `RULES.md` Section 8). Newest log entries go at the top of the Activity Log.

**Last updated:** 2026-11-13 by Codex

---

## 1. Quick start

1. Read `DOCS/RULES.md`, this board, and `DOCS/PROJECT_MEMORY.md`. Do not scan the repository.
2. Work the first unchecked task in `DOCS/Roadmap.md`. Use only that module's section in `DOCS/Design_Doc.md`, its source file, and its test file.
3. Test first for rules and search. Run `.venv/bin/pytest -q` before you stop.
4. Update this board (log, status, repo map), `Roadmap.md` checkboxes, and `PROJECT_MEMORY.md` if project-wide facts changed.

**Project in one line:** a command-line Japan travel planner. An expert system (R1 to R5) sets limits by age group; A* (maximization form) plans each day to maximize value; Greedy is the comparison baseline.

## 2. Current status

| Phase | Module or task | Status | Tests | Last touched | Notes |
|---|---|---|---|---|---|
| Docs | Eight-document set | DONE | n/a | 2026-11-13 | PRD, Design_Doc, Tech_Stack_DOC, Roadmap, Future_Enhancements, RULES, AGENT_BOARD, PROJECT_MEMORY |
| 1 | Scaffold, models, config | DONE | 11 passed | 2026-11-13 | P1.1 to P1.4 and P1.6 complete |
| 1 | `knowledge.py` (M0) and `data/tokyo.json` | IN PROGRESS | 11 passed | 2026-11-13 | 13 seed places; owner choice needed for the 14th high-effort entry; data remains unverified |
| 2 | `expert.py` (M1) | NOT STARTED | 0 | n/a | Rules R1 to R5 |
| 3 | `greedy.py` and `astar.py` (M3, M2) | NOT STARTED | 0 | n/a | Prototype-verified A* logic is in `Design_Doc.md` Section 8.6 |
| 4 | `planner.py` and `cli.py` | NOT STARTED | 0 | n/a | |
| 5 | `experiments.py`, report material | NOT STARTED | 0 | n/a | |
| 6 | Optional extras | NOT STARTED | 0 | n/a | Only after Phase 5 |

Full-suite test count: **11 passed** (`python3 -m pytest -q`).

## 3. Repo map

Items marked "(planned)" do not exist yet. Remove the mark when the file is created.

```
DOCS/                          eight markdown docs (exist)
travelplanner/__init__.py      version 0.1.0
travelplanner/config.py        Config dataclass
travelplanner/models.py        Place, Profile, Stop, DayPlan, Plan
travelplanner/knowledge.py     M0 helpers and city loader
travelplanner/expert.py        (planned)
travelplanner/astar.py         (planned)
travelplanner/greedy.py        (planned)
travelplanner/planner.py       (planned)
travelplanner/cli.py           (planned)
travelplanner/experiments.py   (planned)
data/tokyo.json                13 placeholder seed places, verified=false
tests/test_models_config.py
tests/test_knowledge.py
results/                       output directory
README.md, CHANGELOG.md, requirements.txt, pytest.ini, .gitignore
```

## 4. Commands

```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
.venv/bin/pytest -q
.venv/bin/pytest -q tests/test_astar.py
python -m travelplanner.cli --city tokyo --days 3 --age adult      # Phase 4
python -m travelplanner.experiments                                 # Phase 5
```

## 5. Conventions (short form; full list in `Design_Doc.md` Section 3)

- Minutes since midnight for all times; `(lat, lon)` for coordinates; haversine km.
- Travel minutes = km / speed * 60 * factor; factor applies to travel only.
- Value is set once by the expert system (R5) and never recomputed in search.
- All tunables in `Config`. Standard library only in the package.
- No global randomness; experiments use a seeded `random.Random`.

## 6. Open issues

| ID | Issue | Owner | Status |
|---|---|---|---|
| OI-1 | Confirm with the instructor that this project is acceptable, and what the report and viva require | Owner | Open |
| OI-2 | Decide which cities are in scope (Tokyo first; Kyoto and Osaka optional) | Owner | Open |
| OI-3 | Set scores, durations, and opening hours for the Tokyo places and verify coordinates and hours from official sources | Owner | Open |
| OI-4 | Choose the additional high-effort Tokyo seed place required to reach the 14-place minimum | Owner | Open |

## 7. Decisions

| ID | Decision | Date |
|---|---|---|
| D-001 | One city per trip; no multi-city travel | 2026-11-13 |
| D-002 | Final AI model is a utility-based agent: expert system plus A* search; no learning component | 2026-11-13 |
| D-003 | A* is used in maximization form with an admissible upper bound (fractional knapsack ignoring travel); terminal states are re-queued at f = g before the goal test | 2026-11-13 |
| D-004 | Greedy is the baseline for comparison only | 2026-11-13 |
| D-005 | Travel time is straight-line distance at 20 km/h (times 1.3 for seniors); no map API | 2026-11-13 |
| D-006 | The day ends at the last visit; no return-to-hotel leg | 2026-11-13 |
| D-007 | Days are planned in sequence; places used on one day are removed for later days | 2026-11-13 |
| D-008 | `plan_day` takes `day_start_min` and `day_end_min` instead of the earlier analysis file's `budget_min`, because opening windows need absolute times. This supersedes the analysis file | 2026-11-13 |
| D-009 | Per-day candidate guard of 15 (keep the best by value per minute), because search time grows quickly beyond that; the day is then approximate and the rules log records it | 2026-11-13 |
| D-010 | Value = attraction + souvenir, plus 2 if souvenir is 3 or more | 2026-11-13 |
| D-011 | Package uses only the Python standard library; Matplotlib only for optional figures | 2026-11-13 |
| D-012 | Place data is hand-written and flagged `"verified": false` until the owner confirms it | 2026-11-13 |

## 8. Gotchas

- **A* goal test:** a terminal state's queue priority is `g + h`, which overestimates it. Re-queue it with priority `g` and an `is_goal` flag, and return only when a goal entry is popped. Without this the first version matched brute force on only 11 of 40 instances.
- **Pruning key:** `(location, visited set)` with the smallest time seen is valid because value depends only on the visited set and arriving earlier is never worse (waiting is allowed).
- **Heap ties:** include an integer counter in heap entries; never compare dataclasses or path tuples.
- **Window check:** a visit is feasible only if `start + duration <= close` and `end <= day_end`, where `start = max(arrival, open)`.
- **Senior factor:** applies to travel time only, never to visit durations.
- **Expert rule order:** R1, R2, R3, R5, R4. R4 needs the day window from R1.
- **Prototype numbers are not results:** the figures in `Design_Doc.md` Section 13 came from random synthetic data. Do not quote them as this project's results.
- **Thin later days:** with a small data file, later days may have few or no stops. This is expected; the output should say so.

## 9. Activity log (newest first)

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
