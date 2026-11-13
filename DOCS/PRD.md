# PRD.md: Japan Travel Planner

Product requirements for the Introduction to AI course project. Technical detail is in `Design_Doc.md`.

---

## 1. Overview

A command-line **travel plan suggester for one Japanese city**. The user says which city they are in, how many days they stay, and their age group. The system returns a day-by-day itinerary that visits as much value as possible (attractions plus souvenir stops) within each day's time limit, respecting opening hours and what the traveller can reasonably handle.

It is deliberately small: one city per trip, a hand-written data file, no live data, no map API, and exactly two AI techniques (an expert system and A* search).

**Project context:** group project (pair) for Introduction to Artificial Intelligence.

## 2. Goals

1. A working, correct itinerary planner that runs end to end from the command line.
2. A clear, defensible choice of search algorithm (A*) with a baseline (Greedy) that shows why.
3. An expert system that turns the traveller's age group into limits and filters, with an explanation of what was removed and why.
4. Minimal effort and minimal explaining: small codebase, simple interfaces, two people can work in parallel.

## 3. Non-goals

- Multi-city trips, trains, flights, or hotel booking.
- Budget, food, nightlife, or interest preferences.
- Live data, web APIs, real maps, or real transit times.
- A web or mobile UI. A matplotlib figure is optional only.
- Machine learning or any learned model.

## 4. Users

| User | Need |
|---|---|
| Traveller (simulated by the CLI user) | A sensible day-by-day plan for a short stay |
| Course instructor | A clear AI justification, working demo, and viva-ready explanation |
| Project partner | A small interface so they can build their part without learning everything |

## 5. User stories

- As a traveller, I give a city, number of days, and age group and get an itinerary.
- As a senior traveller, I get fewer hours per day, slower travel assumptions, and no high-effort places.
- As a traveller who likes souvenirs, I get souvenir stops weighted into the plan.
- As the instructor, I can run the same input with Greedy and A* and see the comparison.
- As the instructor, I can ask why a place was left out and get a rule-based answer.

## 6. Functional requirements

| ID | Requirement |
|---|---|
| FR-1 | Accept city, days (1 to 5), and age group (youth, adult, senior) via the command line |
| FR-2 | Load places for the city from a hand-written JSON file, with validation and clear errors |
| FR-3 | Apply expert-system rules R1 to R5 (day length, senior filter, travel factor, fit check, souvenir boost) |
| FR-4 | Record which places each rule removed or changed, for explanation |
| FR-5 | Plan each day with A*, maximizing total value under the day's time limit and opening hours |
| FR-6 | Plan days in sequence; places used on one day are not repeated on a later day |
| FR-7 | Offer Greedy as an alternative algorithm with the same interface (`--algorithm greedy`) |
| FR-8 | Print the itinerary: per day, ordered stops with arrival and start times, durations, souvenir marks, day value, trip totals, and places not scheduled with the reason |
| FR-9 | Warn when the data file is marked unverified |
| FR-10 | Provide an experiment runner for E1 (A* vs Greedy) and E2 (rules on and off) |

## 7. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-1 | One day of planning finishes in under 1 second with up to 15 candidates |
| NFR-2 | A 5-day plan finishes in under 5 seconds |
| NFR-3 | Fully deterministic: same input gives the same itinerary |
| NFR-4 | Core uses only the Python standard library |
| NFR-5 | Runs offline |
| NFR-6 | Every plan satisfies the invariants in `Design_Doc.md` Section 11 |
| NFR-7 | Code is small and readable: about 250 lines in the package excluding tests |

## 8. Success criteria

- A* returns the brute-force optimum on all seeded small test instances.
- A* is greater than or equal to Greedy on every profile in E1.
- No senior plan contains a high-effort place; no plan breaks opening hours or the time limit.
- `pytest -q` passes.
- The owner can explain the project in under two minutes using the 30-second brief and the justification table in `Design_Doc.md`.

## 9. Course fit

| Course topic | Where it appears |
|---|---|
| Agent types and PEAS | Utility-based agent; PEAS and environment properties in `Design_Doc.md` Section 1 |
| Informed search | A* in maximization form with an admissible bound; Greedy baseline |
| Uninformed search | Justified as not suitable (BFS, DFS, UCS) |
| Knowledge-based systems | Expert system R1 to R5 with forward chaining and explanations |
| Local search, GA, adversarial, CSP | Justified as not needed; listed in Future_Enhancements |

The final AI model is the utility-based agent combining the expert system and A*. There is no learning component.

## 10. Deliverables

1. Working package `travelplanner` and `data/tokyo.json` (Kyoto and Osaka optional).
2. Tests passing.
3. E1 and E2 results (table, optional figures).
4. Short report built from `Design_Doc.md` (architecture, algorithm justification, results).
5. Repo docs: README, CHANGELOG, this doc set.

## 11. Assumptions and risks

| Item | Note |
|---|---|
| Place data is hand-written | Scores are our own judgement; coordinates and hours must be checked before the demo; the file carries `"verified": false` until then |
| Straight-line distance understates real travel | Accepted for scope; stated in the report |
| Day ends at the last place | No return-to-hotel leg; accepted |
| Candidate count can grow | Guard of 15 per day keeps the search fast; documented as approximate when it triggers |
| Later days may be thin | With few places, later days may have fewer stops; the output says so |

## 12. Open items for the owner

- Confirm with the instructor that this project is acceptable, and what the report and viva must contain.
- Decide which city or cities to include (Tokyo first).
- Set and verify the place data (scores, durations, hours).
