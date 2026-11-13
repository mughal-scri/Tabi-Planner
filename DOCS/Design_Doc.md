# Design_Doc.md: Japan Travel Planner

The authoritative technical spec. Implement from this file. Where it disagrees with `PRD.md`, this file wins; where it disagrees with the earlier `travel_planner_detailed_analysis.md`, this file wins (differences are logged as decisions D-008 and D-009 on the board).

**Contents:** 1. Architecture, 2. Repo layout, 3. Conventions, 4. Data model, 5. Config, 6. M0 Knowledge base, 7. M1 Expert system, 8. M2 A* planner, 9. M3 Greedy baseline, 10. Trip planner and CLI, 11. Tests, 12. Evaluation, 13. Reference numbers, 14. Algorithm justification, 15. Worked example

---

## 1. Architecture

A single-city itinerary planner. One request flows through four small modules.

```
user input (city, days, age group)
        |
   [M0 knowledge]  load places, distances, travel time
        |
   [M1 expert]     age group -> day length, travel factor; filter places; set values
        |
   for each day:
   [M2 A*]         best ordered plan for the day from the remaining candidates
   (M3 Greedy      same interface, used only for comparison)
        |
   remove visited places, next day
        |
   itinerary text (+ optional figure)
```

**Agent type:** utility-based. **Environment:** fully observable, single-agent, deterministic, sequential, static, discrete. The agent maximizes total plan value (utility) under a time limit. This is the Tourist Trip Design Problem (an Orienteering Problem).

---

## 2. Repo layout

Mark each line "(planned)" on the board until it exists.

```
DOCS/                          PRD, Design_Doc, Tech_Stack_DOC, Roadmap, Future_Enhancements,
                               RULES, AGENT_BOARD, PROJECT_MEMORY
travelplanner/__init__.py      version 0.1.0
travelplanner/config.py        Config dataclass (all tunables)
travelplanner/models.py        Place, Profile, Stop, DayPlan, Plan
travelplanner/knowledge.py     M0: load_city, haversine_km, travel_min, to_minutes, to_clock
travelplanner/expert.py        M1: Rule, default_rules, apply_rules
travelplanner/astar.py         M2: h_bound, plan_day (A*, maximization form)
travelplanner/greedy.py        M3: plan_day_greedy
travelplanner/planner.py       plan_trip (multi-day loop), format_plan
travelplanner/cli.py           command-line entry point
travelplanner/experiments.py   E1 and E2, optional figures
data/tokyo.json                hand-written places (Kyoto, Osaka optional)
tests/test_models_config.py
tests/test_knowledge.py
tests/test_expert.py
tests/test_astar.py            includes a brute-force oracle (tests only)
tests/test_greedy.py
tests/test_planner.py          invariants over full plans
tests/test_cli.py
results/                       figures and tables (not read by agents)
README.md, CHANGELOG.md, requirements.txt, pytest.ini, .gitignore
```

Module sizes (planning numbers): knowledge 30 to 40 lines, expert 40 to 50, astar 50 to 60, greedy about 20, planner and cli 60 to 80 together.

---

## 3. Conventions (do not re-derive)

- **Time** is minutes since midnight as numbers (`540` = 09:00). Travel times are floats; round only when printing (nearest minute).
- **Coordinates** are `(lat, lon)` in degrees. Distance is the haversine great-circle distance in km with R = 6371.0.
- **Travel time** (minutes) = `haversine_km / speed_kmh * 60 * factor`. Default speed 20 km/h. `factor` is 1.0, or 1.3 for seniors. The factor applies to travel only, never to visit durations.
- **Value** of a place is computed once by the expert system and never recomputed in search. Search uses `place.value` only.
- A day starts at `day_start_min` (540) at the city's start point. It ends when the last visit ends; the return to the hotel is not planned.
- Arriving before a place opens means waiting until it opens. A visit is feasible only if `start + duration <= close` and `end <= day_end`.
- No global random state anywhere. Core code uses no randomness. Experiments use a passed `random.Random(seed)`.
- Heap entries carry an integer tie-breaker counter so Python never compares dataclasses or tuples of paths.

---

## 4. Data model

```python
@dataclass(frozen=True)
class Place:
    name: str
    lat: float
    lon: float
    attraction: int        # 1..10, our own judgement
    souvenir: int          # 0..5
    duration_min: int
    open_min: int          # minutes since midnight
    close_min: int
    effort: str            # "low" | "medium" | "high"
    tags: tuple = ()
    value: float = 0.0     # set by the expert system (R5); default = attraction + souvenir

@dataclass(frozen=True)
class Profile:
    age_group: str         # "youth" | "adult" | "senior"
    days: int              # 1..5

@dataclass(frozen=True)
class Stop:
    place: Place
    travel_min: float
    arrive_min: float
    start_min: float       # after any waiting
    end_min: float

@dataclass
class DayPlan:
    day: int               # 1-based
    stops: list            # list[Stop]
    value: float
    end_min: float
    expanded: int          # search states expanded (0 for greedy)

@dataclass
class Plan:
    city: str
    profile: Profile
    days: list             # list[DayPlan]
    total_value: float
    unused: list           # names of places not scheduled
    algorithm: str         # "astar" | "greedy"
    verified_data: bool
```

### 4.1 JSON schema (`data/<city>.json`)

```json
{
  "city": "Tokyo",
  "verified": false,
  "start": {"name": "Tokyo Station", "lat": 35.6812, "lon": 139.7671},
  "places": [
    {"name": "Senso-ji", "lat": 35.7148, "lon": 139.7967,
     "attraction": 9, "souvenir": 2, "duration_min": 90,
     "open": "06:00", "close": "17:00", "effort": "low", "tags": ["temple"]}
  ]
}
```

`open` and `close` are `"HH:MM"` strings converted to minutes on load. A place open all day uses `"00:00"` to `"23:59"`. If `verified` is false, the CLI prints one line saying the data is placeholder and must be checked.

### 4.2 Tokyo seed list

Coordinates are approximate. Scores, durations, and hours are placeholders for the owner to set and verify against official tourism pages before the demo. Aim for 14 to 18 places.

| Place | Approx. lat, lon | Type | Suggested effort | Souvenir potential |
|---|---|---|---|---|
| Senso-ji | 35.7148, 139.7967 | temple | low | medium |
| Nakamise-dori | 35.7118, 139.7963 | souvenir street | low | high |
| Meiji Shrine | 35.6764, 139.6993 | shrine | medium | low |
| Takeshita Street (Harajuku) | 35.6716, 139.7050 | shopping | low | high |
| Shibuya Crossing | 35.6595, 139.7005 | landmark | low | low |
| Akihabara | 35.6984, 139.7731 | shopping | low | high |
| Ueno Park | 35.7156, 139.7745 | park, museums | medium | medium |
| Tsukiji Outer Market | 35.6655, 139.7707 | market | low | medium |
| Imperial Palace East Gardens | 35.6852, 139.7528 | garden | medium | low |
| Shinjuku Gyoen | 35.6852, 139.7100 | garden | medium | low |
| Tokyo Tower | 35.6586, 139.7454 | viewpoint | low | medium |
| Tokyo Skytree | 35.7101, 139.8107 | viewpoint | low | medium |
| Odaiba waterfront (evening window) | 35.6267, 139.7760 | night view | low | low |
| One high-effort place for the senior rule (for example a hike) | owner's choice | hike | high | low |

---

## 5. Config

All tunables live in one dataclass. No magic numbers elsewhere.

```python
@dataclass
class Config:
    day_start_min: int = 540                 # 09:00
    day_hours: dict = {"youth": 10, "adult": 8, "senior": 6}
    speed_kmh: float = 20.0
    travel_factor: dict = {"youth": 1.0, "adult": 1.0, "senior": 1.3}
    souvenir_boost_threshold: int = 3
    souvenir_boost: float = 2.0
    max_candidates_per_day: int = 15         # guard against slow search
    max_days: int = 5
    senior_excluded_effort: tuple = ("high",)
```

(`dict` defaults use `field(default_factory=...)` in code.)

---

## 6. M0 Knowledge base (`knowledge.py`)

```python
def to_minutes(hhmm: str) -> int
def to_clock(minutes: float) -> str                  # "09:35", rounded to nearest minute
def haversine_km(a: tuple, b: tuple) -> float
def travel_min(a: tuple, b: tuple, speed_kmh: float, factor: float = 1.0) -> float
def load_city(path: str) -> tuple[dict, list[Place]]  # (meta incl. start, verified), places
```

`load_city` validates and raises `ValueError` with a clear message for: missing field, `close <= open`, score out of range, unknown effort label, duplicate place name.

---

## 7. M1 Expert system (`expert.py`)

Forward chaining over a small fact dictionary. Rules are plain data: a name, a condition on the facts, and an action that writes new facts or filters places. The loop applies rules in order until no rule changes anything (two passes at most with these rules).

| ID | If | Then |
|---|---|---|
| R1 | `age_group` is youth, adult, or senior | `day_hours` = 10, 8, or 6; `day_end_min = day_start_min + 60*day_hours` |
| R2 | `age_group` is senior | remove places whose effort is in `senior_excluded_effort` |
| R3 | `age_group` is senior | `travel_factor = 1.3` (otherwise 1.0) |
| R5 | `souvenir >= souvenir_boost_threshold` | place `value = attraction + souvenir + souvenir_boost`; otherwise `attraction + souvenir` |
| R4 | `min(close, day_end) - max(open, day_start) < duration` | remove the place (it can never fit) |

Order is R1, R2, R3, R5, R4 (R4 needs the day window from R1). The numbering matches the earlier analysis file.

```python
def default_rules(cfg: Config) -> list[Rule]
def apply_rules(places, profile, cfg) -> dict
# returns {"candidates": [Place with value set], "day_start_min": int, "day_end_min": int,
#          "travel_factor": float, "removed": {name: rule_id}, "fired": [rule ids]}
```

`removed` and `fired` exist so tests and the report can show why a place was dropped (explanation).

Multi-day: the day window is the same every day, so run `apply_rules` once per trip (all five rules). Do not re-run it per day.

---

## 8. M2 A* planner (`astar.py`)

### 8.1 Problem for one day

- **State:** (location, time_now, visited set). Start state is (start point, `day_start_min`, empty).
- **Action:** go to an unvisited place `p`. Arrival = `time_now + travel_min`. Visit starts at `max(arrival, open)`, ends at `start + duration`. Feasible only if `end <= close` and `end <= day_end`.
- **g:** total `value` of visited places (positive, so adding a place always improves a plan).
- **Goal:** a state with no feasible action.
- **Objective:** maximize g.

### 8.2 Heuristic (admissible for maximization)

`h(state)` is an upper bound on extra value still collectable:

1. Take unvisited places with `duration <= remaining` and `close - duration >= time_now`, where `remaining = day_end - time_now`.
2. Sort by `value / duration` descending.
3. Fill `remaining` with whole places, then the last one fractionally. Sum the values. Ignore travel time and waiting.

Ignoring travel and waiting only makes the bound looser, so it never underestimates. `f = g + h`. Expand the state with the **highest f**.

### 8.3 Correctness requirement: goal test at f = g

A terminal state's queue priority was computed as `g + h` with `h > 0`, which overestimates it. If the search returned the first terminal state it pops, it could return a plan that is not optimal. **When a popped state has no feasible extension, push it back with priority `g` and an `is_goal` flag; return only when a goal-flagged entry is popped.** At that point every other open state has `f <= g`, so the plan is optimal. (A prototype without this step matched brute force on only 11 of 40 instances.)

### 8.4 Pruning

Key a visited-state table by `(location, visited_set)` storing the smallest `time_now` seen. Skip a state if the same key was already expanded at an earlier or equal time. This is valid because `g` depends only on the visited set and arriving earlier is never worse (you can always wait).

### 8.5 Interface

```python
def h_bound(now, day_end, unvisited) -> float
def plan_day(candidates, start, day_start_min, day_end_min, speed_kmh, factor) -> tuple[list[Stop], float, int]
# returns (stops, value, expanded); stops may be empty
```

`start` is `(lat, lon)`. Candidates must already carry `value`.

### 8.6 Reference implementation (prototype-verified, dict version)

Port to `Place` attributes and `Stop` objects. Keep the logic identical, in particular the goal re-queue. This version was checked against brute force (40 of 40 random 8-place instances) and against the heuristic bound at every reachable state of one instance (326 states, 0 violations).

```python
def step(cur_pos, now, p, speed, factor):
    arr = now + travel(cur_pos, (p['lat'], p['lon']), speed, factor)
    start = max(arr, p['open'])
    end = start + p['dur']
    return None if end > p['close'] else (start, end)

def h_bound(now, day_end, unvisited):
    rem = day_end - now
    if rem <= 0: return 0.0
    items = sorted(((p['value']/p['dur'], p['value'], p['dur']) for p in unvisited
                    if p['dur'] <= rem and p['close'] - p['dur'] >= now), reverse=True)
    tot = 0.0
    for r, v, d in items:
        if rem <= 0: break
        if d <= rem: tot += v; rem -= d
        else: tot += r * rem; rem = 0
    return tot

def astar_day(cands, start, day_start, day_end, speed, factor):
    n = len(cands); cnt = itertools.count(); expanded = 0
    startpos = (start['lat'], start['lon'])
    pos = lambda i: startpos if i < 0 else (cands[i]['lat'], cands[i]['lon'])
    unv = lambda mask: [cands[i] for i in range(n) if not mask >> i & 1]
    # entry: (-f, tiebreak, is_goal, g, now, loc, mask, path)
    heap = [(-h_bound(day_start, day_end, unv(0)), next(cnt), 0, 0.0, day_start, -1, 0, ())]
    best = {}
    while heap:
        negf, _, is_goal, g, now, loc, mask, path = heapq.heappop(heap)
        if is_goal:
            return g, path, expanded
        key = (loc, mask)
        if key in best and best[key] <= now: continue
        best[key] = now; expanded += 1
        ext = False
        for j in range(n):
            if mask >> j & 1: continue
            r = step(pos(loc), now, cands[j], speed, factor)
            if r is None or r[1] > day_end: continue
            ext = True
            ng = g + cands[j]['value']; nm = mask | 1 << j
            if (j, nm) in best and best[(j, nm)] <= r[1]: continue
            nf = ng + h_bound(r[1], day_end, unv(nm))
            heapq.heappush(heap, (-nf, next(cnt), 0, ng, r[1], j, nm, path + ((j, r[0], r[1]),)))
        if not ext:   # terminal: re-queue at its true value, test the goal at f = g
            heapq.heappush(heap, (-g, next(cnt), 1, g, now, loc, mask, path))
    return 0.0, (), expanded
```

### 8.7 Complexity

Worst case about `n * 2^n` states. The expert system and `max_candidates_per_day` (15) keep `n` small. See Section 13 for measured numbers.

---

## 9. M3 Greedy baseline (`greedy.py`)

Same signature and return as `plan_day`. From the current position, among feasible unvisited places choose the one with the highest `value / (end - now)` (value per minute including travel and waiting); go there; repeat until none is feasible. Ties break by lower index. Used only for comparison and the viva.

```python
def plan_day_greedy(candidates, start, day_start_min, day_end_min, speed_kmh, factor) -> tuple[list[Stop], float, int]
```

---

## 10. Trip planner and CLI (`planner.py`, `cli.py`)

```python
def plan_trip(city_path: str, profile: Profile, cfg: Config = Config(), algorithm: str = "astar") -> Plan
def format_plan(plan: Plan) -> str
```

`plan_trip`:

1. `load_city`, then `apply_rules` once.
2. For `day` in `1..profile.days`: take the remaining candidates. If more than `max_candidates_per_day`, keep the top ones by `value / duration` (guard; log it in `fired`, and note it makes that day approximate). Call `plan_day` (or the greedy version). If the stops are empty, stop planning further days. Otherwise remove the visited places from the remaining pool.
3. Fill `Plan.unused` with names of places never scheduled (including rule-removed ones).

Input validation: `days` in `1..max_days`, `age_group` in the three labels, city file must exist; otherwise raise `ValueError` with a plain message (the CLI prints it and exits with code 2).

`format_plan` sample (times illustrative):

```
Japan Travel Planner | Tokyo | 3 days | adult | algorithm: A*
Note: place data is unverified placeholder data.

Day 1 (09:00 to 16:50, value 41)
  09:00  Start: Tokyo Station
  09:35  Senso-ji (90 min)
  11:20  Nakamise-dori (45 min)  [souvenirs]
  ...
Total value: 118 | Places visited: 11 | Not scheduled: Mount X (removed by R2)
```

CLI:

```
python -m travelplanner.cli --city tokyo --days 3 --age adult [--algorithm astar|greedy] [--data-dir data]
```

---

## 11. Tests

Test-first for search. Use `pytest`; no plotting backend needed for core tests.

| File | Must check |
|---|---|
| `test_models_config` | Config defaults, dataclass immutability, dict defaults not shared |
| `test_knowledge` | haversine known pair (Tokyo Station to Senso-ji about 5 km, tolerance 0.3), clock round trip, load errors, travel factor |
| `test_expert` | R1 hours for each age; R2 removes high effort for seniors only; R3 factor; R4 removes a place that cannot fit; R5 value boost; `removed` and `fired` filled; rule order |
| `test_astar` | Equals brute-force optimum on 30 seeded random instances of 7 places; `h` never below the optimum at the root on the same instances; never exceeds budget; respects windows; waiting works (place opens after arrival); goal re-queue regression test (instance where first terminal pop is suboptimal); empty candidates give empty plan; deterministic |
| `test_greedy` | Valid plan; value less than or equal to A* on 30 instances |
| `test_planner` | Invariants below; 1, 3, 5 days; senior plan has no high-effort place; unused list correct; invalid input errors |
| `test_cli` | Runs with valid arguments; exit code 2 on invalid input; output contains the totals line |

**Plan invariants (assert on every full plan in tests):** each day's last `end_min <= day_end`; each stop's `start_min >= open` and `end_min <= close`; no place appears twice across all days; stops are in time order; the total equals the sum of day values; the sum of travel and visits is consistent with the clock.

**Oracle:** the brute-force recursive search lives in `tests/` only (`brute_force_day`), never in the package.

---

## 12. Evaluation (`experiments.py`)

Seeded, headless, no network.

| ID | Experiment | Setup | Metrics | Expected |
|---|---|---|---|---|
| E1 | A* vs Greedy | About 10 profiles: days 1 to 3 times youth, adult, senior, on the real Tokyo file | Total value, runtime, nodes expanded | A* is greater than or equal to Greedy on every profile; both under 1 second per day |
| E2 | Expert rules on/off | Same profiles; "off" skips R2, R3, R4 and uses the default day length | Nodes expanded, time, number of rule violations in the plan (high-effort place for a senior, a visit outside its window) | Rules shrink the search; violations are zero with rules on |

Outputs a printed table, plus optional `results/fig_e1.png` (value bars) and `results/fig_e2.png` (nodes bars) using Matplotlib. Figures are optional; tables are enough for the report.

---

## 13. Reference numbers (prototype on synthetic data)

Prototype setup: random places in a box around Tokyo (35.60 to 35.75 N, 139.65 to 139.85 E), durations 30 to 120 min, values 5 to 14, varied opening windows, start 09:00, 8-hour day, 20 km/h. Real Tokyo data will differ; use these as sanity targets only.

| Check | Result |
|---|---|
| A* equals brute-force optimum (8 places, 40 random instances) | 40 of 40 |
| Greedy below A* | average 5.3%, worst 21.4%, strictly worse on 23 of 40 |
| Heuristic at the root below the true optimum | 0 of 40 violations |

Search size and time (A*, average and maximum over seeded instances):

| Candidates | States expanded avg / max | Time avg / max |
|---|---|---|
| 10 | 459 / 1,325 | 0.006 s / 0.017 s |
| 12 | 747 / 1,939 | 0.015 s / 0.036 s |
| 15 | 2,467 / 4,915 | 0.08 s / 0.18 s |
| 18 | 4,931 / 11,080 | 0.24 s / 0.71 s |
| 20 | 9,741 / 31,150 | 0.58 s / 1.79 s |

This is why `max_candidates_per_day` is 15.

---

## 14. Algorithm justification

| Algorithm | Verdict |
|---|---|
| BFS, DFS | Uninformed and blind to values; the number of orderings explodes. Not used. |
| UCS | Minimizes path cost; our objective is to maximize collected value, so cost does not apply. |
| Greedy best-first | Fast, but locally best choices can waste the day. **Baseline only.** |
| **A\*** | **Chosen.** Optimal with an admissible bound, explainable, fast on small candidate sets. |
| Hill Climbing, GA | Not needed at this size. Possible if a city grows to 40+ places. |
| Minimax | There is no opponent. |
| CSP | Opening windows could be constraints, but the search already checks them. |
| Learning model | The data is fixed and hand-written; there is nothing to learn from. |

---

## 15. Worked example (illustrative numbers)

Value = attraction + souvenir, +2 if souvenir >= 3.

| Place | Attraction | Souvenir | Boost | Value | Visit (min) |
|---|---|---|---|---|---|
| Senso-ji | 9 | 2 | 0 | 11 | 90 |
| Nakamise-dori | 5 | 5 | +2 | 12 | 45 |
| Meiji Shrine | 8 | 1 | 0 | 9 | 75 |
| Akihabara | 6 | 4 | +2 | 12 | 90 |
| Shibuya Crossing | 7 | 1 | 0 | 8 | 30 |

Greedy chases the best value per minute at each step and can cross the city for a high-ratio place, leaving too little time for the next. A* compares whole orderings through its best-case bound, so it can choose a tighter route that fits another place. E1 shows this on real runs; do not claim a specific gap until E1 has been run.
