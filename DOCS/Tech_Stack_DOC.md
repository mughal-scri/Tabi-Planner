# Tech_Stack_DOC.md: Japan Travel Planner

Keep the stack as small as the project. Nothing outside this list without the owner's approval.

---

## 1. Summary

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.10 or newer | Course language; dataclasses, type hints, `heapq` in the standard library |
| Core libraries | Standard library only: `heapq`, `math`, `json`, `dataclasses`, `itertools`, `argparse`, `http.server`, `random` (experiments only), `urllib` and `threading` (server tests only) | No install friction; nothing to explain |
| Data | One master JSON dataset (`data/japan_travel_dataset.json`, about 250 KB, 12 cities and 135 places), owner-supplied | No API keys, offline, loads in milliseconds with `json` |
| Testing | `pytest` | Standard, small |
| Figures (optional) | Matplotlib | Only for E1 and E2 charts or an optional route plot |
| Command-line interface | `argparse` | Quick runs, scripting, and experiments |
| Web UI | One page of plain HTML, CSS, and JavaScript in `web/` (no framework, no build step, no CDN, system fonts, inline SVG icons), served by the standard library `http.server` on `127.0.0.1` with a four-route JSON API | Gives the interest-bubble selector with zero setup; works offline; small enough to explain |

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
python -m travelplanner.cli --route tokyo:3,kyoto:2,osaka:2 --age adult      # multi-city
python -m travelplanner.cli --city tokyo --days 3 --age senior --algorithm greedy
python -m travelplanner.experiments                    # E1, E2, and E3 tables
python -m travelplanner.server                         # local web UI at http://127.0.0.1:8000
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
- No global random state; no outbound network calls (the server listens on localhost only); no file writes outside `results/`.
- Web code: tokens in `:root`, no hard-coded colors, no `innerHTML` with API data, no drop-down menus; accessibility and responsive rules are in `Design_Doc.md` Section 16.3.
- If figures are generated, use the non-interactive Matplotlib backend (`Agg`) so tests run headless.

## 5. Explicitly not used

| Technology | Why not |
|---|---|
| Google Maps or any routing API | Needs keys and network; straight-line travel time is enough |
| React, Next.js, Vite, Tailwind, shadcn/ui, TypeScript | The page is small; plain HTML, CSS, and JavaScript with no build step keeps setup at zero. The UI skill assumes that stack; where it conflicts with this document, this document wins |
| Flask, FastAPI, any server framework | `http.server` is enough for four routes |
| CDN scripts, web fonts, icon libraries | The page must work offline; use system fonts and inline SVG |
| NumPy, pandas | No heavy numeric work or tables |
| Any ML library | No learned model in this project |
| Database | One master JSON file is enough |

## 6. Optional later additions

A map view, a rewrite of the page in React and Tailwind, and real travel times are listed in `Future_Enhancements.md`. They are not part of this build.

## 7. Skills for the web UI

The local web page is approved (Roadmap Phase 4B). Apply the `autonomous-ui-architect` skill's principles to it: central design tokens, no magic numbers, hover and focus states on everything interactive, WCAG contrast and semantics, reduced-motion and dark-mode support, and its run-fix-repeat check before calling the UI done. Do not use its React, Tailwind, shadcn/ui, or TypeScript requirements; this document's stack (Section 1) wins. `senior-developer-skill` applies to all code work.
