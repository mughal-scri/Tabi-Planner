# PRD.md: Japan Travel Planner

Product requirements for the Introduction to AI course project. Technical detail is in `Design_Doc.md`.

---

## 1. Overview

A command-line **travel plan suggester for Japan, covering one city or several**. The user gives an ordered route (for example Tokyo for 3 days, then Kyoto for 2, then Osaka for 2), their age group, and optionally the kinds of places they enjoy, picked from a pool of category bubbles (for example Shinto shrines, markets and food streets, museums). The system returns a day-by-day itinerary that visits as much value as possible (attractions plus souvenir stops) within each day's time limit, respecting opening hours and what the traveller can reasonably handle. When the route changes city, it adds the transfer time, so the first day in the new city starts later.

It runs from the command line or from a small local web page. It is deliberately small: the user supplies the city order, the data is one owner-supplied JSON file (12 cities, 135 places), there is no live data and no map API, and there are exactly two AI techniques (an expert system and A* search).

**Project context:** group project (pair) for Introduction to Artificial Intelligence.

## 2. Goals

1. A working, correct itinerary planner that runs end to end from the command line.
2. A clear, defensible choice of search algorithm (A*) with a baseline (Greedy) that shows why.
3. An expert system that turns the traveller's age group into limits and filters, with an explanation of what was removed and why.
4. Multi-city trips: chain cities in a user-given order with a computed city-to-city transfer between them.
5. Preferences: let the user pick interest categories as bubbles and steer the plan toward them without changing the search algorithm.
6. A simple, accessible local web page for the whole flow (trip, interests, itinerary); the CLI keeps working.
7. Minimal effort and minimal explaining: small codebase, simple interfaces, two people can work in parallel.

## 3. Non-goals

- Choosing or ordering the cities automatically (the user supplies the order; see `Future_Enhancements.md`).
- Real train or flight schedules, fares, or transport-mode choice; hotel booking.
- Budget and nightlife; restaurant listings (the dataset has food markets and food streets, not restaurants).
- Hard filtering by interest (preferences are a soft value boost).
- Live data, web APIs, real maps, or real transit times (inside or between cities).
- A hosted or public website, user accounts, or a mobile app. The web page is local only (`127.0.0.1`), plain HTML, CSS, and JavaScript, with no framework. A matplotlib figure is optional.
- Machine learning or any learned model.

## 4. Users

| User | Need |
|---|---|
| Traveller (simulated by the CLI user) | A sensible day-by-day plan for a short stay |
| Course instructor | A clear AI justification, working demo, and viva-ready explanation |
| Project partner | A small interface so they can build their part without learning everything |

## 5. User stories

- As a traveller, I give a city, number of days, and age group and get an itinerary.
- As a traveller, I pick the kinds of places I enjoy from a pool of bubbles (no drop-down), skip if I have no preference, and the plan leans toward them.
- As a traveller visiting several cities, I give an ordered route (for example `tokyo:3,kyoto:2,osaka:2`) and get one itinerary with the transfers between cities.
- As a senior traveller, I get fewer hours per day, slower travel assumptions, and no high-effort places.
- As a traveller who likes souvenirs, I get souvenir stops weighted into the plan.
- As the instructor, I can run the same input with Greedy and A* and see the comparison.
- As the instructor, I can ask why a place was left out and get a rule-based answer.

## 6. Functional requirements

| ID | Requirement |
|---|---|
| FR-1 | Accept a route (1 to 5 cities, 1 to 5 days each, at most 10 days in total) or a single city with days, and an age group (youth, adult, senior), via the command line |
| FR-2 | Load all cities and places from the master JSON dataset (`data/japan_travel_dataset.json`), with validation and clear errors |
| FR-3 | Apply expert-system rules R1 to R6 (day length, senior filter, travel factor, fit check, souvenir boost, interest boost) |
| FR-4 | Record which places each rule removed or changed, for explanation |
| FR-5 | Plan each day with A*, maximizing total value under the day's time limit and opening hours |
| FR-6 | Plan days in sequence; places used on one day are not repeated on a later day, and each city has its own place pool |
| FR-7 | Offer Greedy as an alternative algorithm with the same interface (`--algorithm greedy`) |
| FR-8 | Print the itinerary: per day, ordered stops with arrival and start times, durations, souvenir marks, day value, trip totals, and places not scheduled with the reason |
| FR-9 | Warn when the data file is marked unverified |
| FR-10 | Provide an experiment runner for E1 (A* vs Greedy) and E2 (rules on and off) |
| FR-11 | Between consecutive route cities, compute the transfer (straight-line anchor distance at 150 km/h plus a 30-minute buffer) and start the first day in the new city later by that amount |
| FR-12 | Reject invalid routes (unknown or repeated city, too many cities or days) and unknown interests with a clear message and exit code 2 |
| FR-13 | Accept optional interests (category ids) in the CLI (`--interests`) and the web UI; empty means no preference |
| FR-14 | Rule R6 adds a fixed bonus to the value of every place in a selected category; the search algorithm is unchanged |
| FR-15 | Provide a local web page with three steps: trip (cities, days, age group), interests (bubble pool), itinerary |
| FR-16 | The interest pool shows only categories that exist in the chosen cities, as toggle bubbles (each with an on/off state), multi-select, with Clear and Skip; no drop-down anywhere |
| FR-17 | Provide a local JSON API for the page (cities, category pool, plan); it binds to localhost only |

## 7. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-1 | One day of planning finishes in under 1 second on the real dataset (up to 20 candidates per day) |
| NFR-2 | A 10-day, multi-city plan finishes in under 5 seconds |
| NFR-3 | Fully deterministic: same input gives the same itinerary |
| NFR-4 | Core uses only the Python standard library |
| NFR-5 | Runs offline |
| NFR-6 | Every plan satisfies the invariants in `Design_Doc.md` Section 11 |
| NFR-7 | Code is small and readable: about 450 lines of Python in the package plus about 400 lines of web page, excluding tests |
| NFR-8 | The web page is accessible: keyboard operable, visible focus, contrast of at least 4.5:1 for text, selection not shown by color alone, reduced-motion respected, works from 360 px wide |
| NFR-9 | The web page works offline: no CDN, no web fonts, no calls to any server other than localhost |

## 8. Success criteria

- A* returns the brute-force optimum on all seeded small test instances.
- A* is greater than or equal to Greedy on every profile in E1.
- No senior plan contains a high-effort place; no plan breaks opening hours or the time limit.
- Selecting interests raises the share of stops in the selected categories on the calibration cases (`Design_Doc.md` Section 13.2); selecting none leaves plans unchanged.
- The web page completes the whole flow and passes the manual checklist in `Design_Doc.md` Section 16.4.
- Every multi-city plan has a transfer at each city change, with the first day in the new city starting at 09:00 plus the transfer time.
- `pytest -q` passes.
- The owner can explain the project in under two minutes using the 30-second brief and the justification table in `Design_Doc.md`.

## 9. Course fit

| Course topic | Where it appears |
|---|---|
| Agent types and PEAS | Utility-based agent; PEAS and environment properties in `Design_Doc.md` Section 1 |
| Informed search | A* in maximization form with an admissible bound; Greedy baseline |
| Uninformed search | Justified as not suitable (BFS, DFS, UCS) |
| Knowledge-based systems | Expert system R1 to R6 with forward chaining and explanations; preferences as a rule |
| Local search, GA, adversarial, CSP | Justified as not needed; listed in Future_Enhancements |

The final AI model is the utility-based agent combining the expert system and A*. There is no learning component.

## 10. Deliverables

1. Working package `travelplanner`, the master dataset `data/japan_travel_dataset.json`, and the local web page in `web/`.
2. Tests passing.
3. E1 and E2 results (table, optional figures).
4. Short report built from `Design_Doc.md` (architecture, algorithm justification, results).
5. Repo docs: README, CHANGELOG, this doc set.

## 11. Assumptions and risks

| Item | Note |
|---|---|
| Dataset is owner-supplied (generated with ChatGPT) | Scores are editorial estimates, hours are broad planning windows, and coordinates are approximate pins; the file carries `"verified": false` until the owner checks it against official sources |
| City-to-city time is a straight-line proxy | Anchor distance at 150 km/h plus a buffer; rough for long hops (Tokyo to Sapporo is really a flight); accepted and stated in the report |
| Straight-line distance understates real travel | Accepted for scope; stated in the report |
| Day ends at the last place | No return-to-hotel leg; accepted |
| Candidate count can grow | Guard of 20 per day keeps the search fast; documented as approximate when it triggers (Tokyo has 18 places, so it does not trigger on the current data) |
| Fine-grained categories | The dataset has 58 categories and matching is exact, so a user may need to pick several related bubbles; grouping is a future enhancement |
| UI adds scope | The page is built after the core CLI works (Roadmap Phase 4B); the CLI and the tests do not depend on it |
| Later days may be thin | Cities have 8 to 18 places, so a third or later day in one city may have few or no stops; empty days are still listed |

## 12. Open items for the owner

- Confirm with the instructor that this project is acceptable, and what the report and viva must contain.
- Verify the dataset (hours, coordinates, durations) against official sources and set `verified` when done; scores remain editorial estimates unless you retune them.
