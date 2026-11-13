# Tech_Stack_DOC.md: Japan Travel Planner

Keep the stack as small as the project. Nothing outside this list without the owner's approval.

---

## 1. Summary

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.10 or newer | Course language; dataclasses, type hints, `heapq` in the standard library |
| Core libraries | Standard library only: `heapq`, `math`, `json`, `dataclasses`, `itertools`, `argparse`, `random` (experiments only) | No install friction; nothing to explain |
| Data | One JSON file per city, hand-written | No API keys, offline, easy to edit |
| Testing | `pytest` | Standard, small |
| Figures (optional) | Matplotlib | Only for E1 and E2 charts or an optional route plot |
| Interface | Command line (`argparse`) | The project is about the AI, not the UI |

NumPy is not needed. The search is pure Python and runs in well under a second per day.

## 2. Dependencies

`requirements.txt`:

```
pytest
matplotlib      # optional, only for experiments figures
```

Pin exact versions in `requirements.txt` when the environment is first created, and keep them pinned.

## 3. Setup and commands

```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements.txt

pytest -q                                              # all tests
pytest -q tests/test_astar.py                          # one module
python -m travelplanner.cli --city tokyo --days 3 --age adult
python -m travelplanner.cli --city tokyo --days 3 --age senior --algorithm greedy
python -m travelplanner.experiments                    # E1 and E2 tables
```

`pytest.ini`:

```
[pytest]
pythonpath = .
```

## 4. Conventions

- Style: PEP 8, type hints on public functions, docstrings only where the contract is not obvious.
- Immutable dataclasses (`frozen=True`) for data that should not change after load.
- One `Config` dataclass for every tunable.
- No global random state; no network calls; no file writes outside `results/`.
- If figures are generated, use the non-interactive Matplotlib backend (`Agg`) so tests run headless.

## 5. Explicitly not used

| Technology | Why not |
|---|---|
| Google Maps or any routing API | Needs keys and network; straight-line travel time is enough |
| Web framework or React | Out of scope; the CLI is the interface |
| NumPy, pandas | No heavy numeric work or tables |
| Any ML library | No learned model in this project |
| Database | One JSON file per city is enough |

## 6. Optional later additions

Folium or a web page for a map view, a small web UI, and real travel times are listed in `Future_Enhancements.md`. They are not part of this build.

## 7. If a UI is ever added

The project workflow for UI work (the `autonomous-ui-architect` skill) only applies if a UI is approved. For the CLI build it does not apply. `senior-developer-skill` applies to all code work.
