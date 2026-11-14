# Design_Doc.md: Japan Travel Planner

The authoritative technical spec. Implement from this file. Where it disagrees with `PRD.md`, this file wins; where it disagrees with the earlier `travel_planner_detailed_analysis.md`, this file wins (differences are logged as decisions D-008 and D-009 on the board). `travel_planner_detailed_analysis.md` describes the earlier single-city scope and is outdated; do not implement from it.

**Contents:** 1. Architecture, 2. Repo layout, 3. Conventions, 4. Data model, 5. Config, 6. M0 Knowledge base, 7. M1 Expert system, 8. M2 A* planner, 9. M3 Greedy baseline, 10. Trip planner (multi-city) and CLI, 11. Tests, 12. Evaluation, 13. Reference numbers, 14. Algorithm justification, 15. Worked example, 16. Interests and the web UI

---

## 1. Architecture

A multi-city itinerary planner with optional interest preferences. The user supplies an **ordered route** (for example Tokyo 3 days, Kyoto 2 days, Osaka 2 days), an age group, and optionally some **interest categories** picked as bubbles. One request flows through four small modules. Two front ends (the CLI and a local web page) both call the same `plan_trip`.

```
user input (route = ordered cities with days each, age group, interests = category ids, may be empty)
        |
   [M0 knowledge]  load the master dataset; distances, travel times, city-to-city transfers, category pool
        |
   for each city in the route:
   [M1 expert]     age group -> day length, travel factor; filter places; set values incl. interest boost (once per city)
        |
   for each day in that city:
   [M2 A*]         best ordered plan for the day from the city's remaining places
                   (the first day in a new city starts late by the transfer time)
   (M3 Greedy      same interface, used only for comparison)
        |
   remove visited places, next day; at a city change add the transfer
        |
   Plan -> itinerary text (CLI) or JSON (web UI)
```

**Two levels.** City level: the user gives the order and days; the system computes the transfer between consecutive cities. Day level: A* chooses and orders the places for each day. There is no search at the city level in the core build (see Section 14 and `Future_Enhancements.md`).

**Preferences are values, not a new algorithm.** Selected interest categories add a bonus to the value of matching places (rule R6). The search, the heuristic, and their correctness are unchanged.

**Agent type:** utility-based. **Environment:** fully observable, single-agent, deterministic, sequential, static, discrete. The agent maximizes total plan value (utility) under a time limit per day. Each day is a Tourist Trip Design Problem (an Orienteering Problem).

---

## 2. Repo layout

Mark each line "(planned)" on the board until it exists.

```
DOCS/                          PRD, Design_Doc, Tech_Stack_DOC, Roadmap, Future_Enhancements,
                               RULES, AGENT_BOARD, PROJECT_MEMORY
travelplanner/__init__.py      version 0.1.0
travelplanner/config.py        Config dataclass (all tunables)
travelplanner/models.py        Place, City, Profile, Transfer, Stop, DayPlan, Plan
travelplanner/knowledge.py     M0: load_dataset, load_city, haversine_km, travel_min, intercity, to_minutes, to_clock
travelplanner/expert.py        M1: Rule, default_rules, apply_rules
travelplanner/astar.py         M2: h_bound, plan_day (A*, maximization form)
travelplanner/greedy.py        M3: plan_day_greedy
travelplanner/planner.py       plan_trip (multi-city, multi-day loop), format_plan
travelplanner/cli.py           command-line entry point
travelplanner/server.py        local web server and JSON API (standard library only)
travelplanner/experiments.py   E1 and E2, optional figures
data/japan_travel_dataset.json owner-supplied master dataset (12 cities, 135 places, schema 2.0.0)
web/index.html, web/styles.css, web/app.js   single-page UI, plain HTML/CSS/JS, no build step
tests/test_models_config.py
tests/test_knowledge.py
tests/test_expert.py
tests/test_astar.py            includes a brute-force oracle (tests only)
tests/test_greedy.py
tests/test_planner.py          invariants over full single- and multi-city plans
tests/test_cli.py
tests/test_server.py
results/                       figures and tables (not read by agents)
README.md, CHANGELOG.md, requirements.txt, pytest.ini, .gitignore
```

`data/tokyo.json` (the 13-place single-city seed file) is obsolete and is replaced by the master dataset.

Module sizes (planning numbers): knowledge 60 to 80 lines, expert 50 to 60, astar 50 to 60, greedy about 20, planner and cli 110 to 140 together, server about 100; web UI about 400 lines across the three files.

---

## 3. Conventions (do not re-derive)

- **Time** is minutes since midnight as numbers (`540` = 09:00). Travel times are floats; round only when printing (nearest minute).
- **Coordinates** are `(lat, lon)` in degrees. Distance is the haversine great-circle distance in km with R = 6371.0.
- **Travel time** (minutes) = `haversine_km / speed_kmh * 60 * factor`. Default speed 20 km/h. `factor` is 1.0, or 1.3 for seniors. The factor applies to travel only, never to visit durations.
- **Value** of a place is computed once by the expert system and never recomputed in search. Search uses `place.value` only.
- A day starts at `day_start_min` (540) at the city's start point (its **anchor**, normally the main station). It ends when the last visit ends; the return to the hotel is not planned.
- **City-to-city transfer:** minutes = `haversine_km(anchor_a, anchor_b) / intercity_speed_kmh * 60 + intercity_buffer_min` (150 km/h plus a 30-minute buffer by default). It is taken on the **first day in the new city**, in the morning: that day's start becomes `day_start_min + transfer minutes`. The day end does not move, so arrival days have fewer stops. The transfer does not depend on the age group.
- A city may appear at most once in a route. Place pools are independent per city, so no place can repeat across the trip. Place `id` is unique across the dataset and is the key used for tracking.
- **Interests** are category ids from the dataset's root `categories` list. A place matches an interest when `place.category` equals a selected id exactly. An empty interest set means no preference.
- The web UI never uses a drop-down (`<select>`) for choices; it uses toggle bubbles and chips (Section 16.3).
- Arriving before a place opens means waiting until it opens. A visit is feasible only if `start + duration <= close` and `end <= day_end`.
- No global random state anywhere. Core code uses no randomness. Experiments use a passed `random.Random(seed)`.
- Heap entries carry an integer tie-breaker counter so Python never compares dataclasses or tuples of paths.

---

## 4. Data model

```python
@dataclass(frozen=True)
class Place:
    id: str                # unique across the dataset, e.g. "tokyo-senso-ji"
    name: str
    lat: float
    lon: float
    attraction: int        # 1..10, editorial estimate
    souvenir: int          # 0..5 (the dataset uses 1..5)
    duration_min: int
    open_min: int          # minutes since midnight
    close_min: int
    effort: str            # "low" | "medium" | "high"
    category: str          # category id, e.g. "shrine"; one of the root categories
    area: str = ""         # neighbourhood, shown in the output
    location_scope: str = "city"    # "city" | "nearby_day_trip"
    tags: tuple = ()
    value: float = 0.0     # set by the expert system (R5, R6); default = attraction + souvenir

@dataclass(frozen=True)
class City:
    city_id: str           # "tokyo"
    name: str              # "Tokyo"
    start: tuple           # (lat, lon) anchor
    start_name: str        # "Tokyo Station"
    places: tuple          # tuple[Place, ...]
    verified: bool

@dataclass(frozen=True)
class Profile:
    age_group: str         # "youth" | "adult" | "senior"
    route: tuple           # ((city_id, days), ...) in visiting order; days 1..max_days_per_city
    interests: tuple = ()  # category ids the user selected; may be empty

@dataclass(frozen=True)
class Transfer:
    from_city: str
    to_city: str
    km: float              # anchor-to-anchor great-circle distance
    minutes: float         # includes the buffer

@dataclass(frozen=True)
class Stop:
    place: Place
    travel_min: float
    arrive_min: float
    start_min: float       # after any waiting
    end_min: float

@dataclass
class DayPlan:
    day: int               # 1-based trip day
    city_id: str
    stops: list            # list[Stop]; may be empty
    value: float
    start_min: float       # day_start_min plus the transfer on a city's first day
    end_min: float         # last stop end, or start_min if no stops
    expanded: int          # search states expanded (0 for greedy)
    transfer: object       # Transfer on the first day in a new city, otherwise None
    approximate: bool      # True when the per-day candidate guard was applied

@dataclass
class Plan:
    profile: Profile
    days: list             # list[DayPlan] in trip order
    total_value: float
    unused: dict           # city_id -> names of places never scheduled (includes rule-removed)
    removed: dict          # city_id -> {place name: rule id} from the expert system
    algorithm: str         # "astar" | "greedy"
    verified_data: bool    # True only if every route city is verified
    city_names: dict       # city_id -> display name, retained for formatting
    city_start_names: dict # city_id -> anchor name, retained for formatting
    interest_labels: dict  # selected category id -> display label
    souvenir_boost_threshold: int # formatting threshold for the [souvenirs] tag
```

### 4.1 Master dataset schema (`data/japan_travel_dataset.json`)

The owner-supplied file (generated with ChatGPT, schema 2.0.0) has a top-level `cities` array. The loader iterates `data["cities"]` and then each `city["places"]`.

```json
{
  "dataset_name": "Japan Sightseeing and City Attraction Dataset",
  "schema_version": "2.0.0",
  "verified": false,
  "cities": [
    {"city": "Tokyo", "city_id": "tokyo", "region": "Kanto", "verified": false,
     "start": {"name": "Tokyo Station", "lat": 35.6812, "lon": 139.7671},
     "places": [
       {"id": "tokyo-senso-ji", "name": "Senso-ji", "lat": 35.7148, "lon": 139.7967,
        "attraction": 9, "souvenir": 2, "duration_min": 90,
        "open": "06:00", "close": "17:00", "effort": "low",
        "tags": ["temple"], "area": "Asakusa", "location_scope": "city"}
     ]}
  ]
}
```

**Fields the planner uses:** root `categories` (`id`, `label`); per city `city`, `city_id`, `start` (`name`, `lat`, `lon`), `verified`; per place `id`, `name`, `lat`, `lon`, `attraction`, `souvenir`, `duration_min`, `open`, `close`, `effort`, `category`, `tags`, `area`, `location_scope`. `open` and `close` are `"HH:MM"` strings converted to minutes on load; an all-day place is `"00:00"` to `"23:59"`.

**Fields the planner ignores** (kept in the file): `description`, `subcategory`, `best_time_of_day`, `best_seasons`, `setting`, `family_friendly`, `cost_type`, `admission_*`, `hours_status`, `hours_note`, `coordinates_status`, `municipality`, `source_ids`, `extra_note`, and the root `source_registry`.

**Validation (raise `ValueError` with a clear message):** schema version does not start with `2.`; `cities` missing or empty; duplicate `city_id`; duplicate place `id` anywhere in the file; a missing required field; `close <= open`; `attraction` outside 1..10; `souvenir` outside 0..5; unknown effort label; non-positive duration; a place `category` that is not in the root `categories`.

**Meaning of the data (from the file's own policy fields):** scores are editorial estimates, not ratings; `open` and `close` are broad planning windows, not live schedules; coordinates are approximate map pins; `duration_min` excludes travel and waiting. The file excludes nightclubs, bars, adult venues, and casinos by policy, so the planner needs no preference inputs for them. Six places are flagged `nearby_day_trip` (outside the named city, commonly visited from it); the planner treats them like any other place and the straight-line travel time naturally penalizes them.

### 4.2 Cities in the dataset (`verified: false` everywhere)

| city_id | City | Region | Places | Anchor |
|---|---|---|---|---|
| `tokyo` | Tokyo | Kanto | 18 | Tokyo Station |
| `kyoto` | Kyoto | Kansai | 14 | Kyoto Station |
| `osaka` | Osaka | Kansai | 12 | Osaka Station |
| `nara` | Nara | Kansai | 10 | Kintetsu-Nara Station |
| `hiroshima` | Hiroshima | Chugoku | 10 | Hiroshima Station |
| `sapporo` | Sapporo | Hokkaido | 12 | Sapporo Station |
| `fukuoka` | Fukuoka | Kyushu | 11 | Hakata Station |
| `yokohama` | Yokohama | Kanto | 10 | Yokohama Station |
| `kanazawa` | Kanazawa | Hokuriku | 10 | Kanazawa Station |
| `nagoya` | Nagoya | Chubu | 10 | Nagoya Station |
| `nagasaki` | Nagasaki | Kyushu | 10 | Nagasaki Station |
| `takayama` | Takayama | Chubu | 8 | Takayama Station |

Total 135 places. With 8 to 18 places per city, a city supports about 2 to 3 full days; beyond that, later days thin out (see Section 13).

---

## 5. Config

All tunables live in one dataclass. No magic numbers elsewhere.

```python
@dataclass
class Config:
    day_start_min: int = 540                 # 09:00
    day_hours: dict = {"youth": 10, "adult": 8, "senior": 6}
    speed_kmh: float = 20.0                  # inside a city
    travel_factor: dict = {"youth": 1.0, "adult": 1.0, "senior": 1.3}
    intercity_speed_kmh: float = 150.0       # city-to-city, straight-line proxy for rail
    intercity_buffer_min: int = 30           # boarding, transfers, getting to the anchor
    souvenir_boost_threshold: int = 3
    souvenir_boost: float = 2.0
    interest_boost: float = 8.0              # added to a place's value when its category is selected
    max_candidates_per_day: int = 20         # guard against slow search
    max_cities: int = 5
    max_days_per_city: int = 5
    max_total_days: int = 10
    senior_excluded_effort: tuple = ("high",)
```

(`dict` defaults use `field(default_factory=...)` in code. The earlier `max_days` is replaced by the three limits above.)

---

## 6. M0 Knowledge base (`knowledge.py`)

```python
def to_minutes(hhmm: str) -> int
def to_clock(minutes: float) -> str                      # "09:35", rounded to nearest minute
def haversine_km(a: tuple, b: tuple) -> float
def travel_min(a: tuple, b: tuple, speed_kmh: float, factor: float = 1.0) -> float
def load_dataset(path: str) -> dict[str, City]           # city_id -> City, in file order; validates (Section 4.1)
def load_city(path: str, city_id: str) -> City           # convenience; ValueError if the city is unknown
def intercity(a: City, b: City, cfg: Config) -> Transfer # km from anchors, minutes with buffer
def load_categories(path: str) -> dict[str, str]         # category id -> label, from the root `categories` (58 entries)
def category_pool(cities: dict[str, City], labels: dict[str, str], city_ids: list[str]) -> list[dict]
# [{"id", "label", "count"}] for categories with at least one place in those cities,
# sorted by count descending, then label
```

`load_dataset` reads the file once; `plan_trip` calls it once per run. The earlier `load_city(path)` that read a single-city file is replaced by these functions.

---

## 7. M1 Expert system (`expert.py`)

Forward chaining over a small fact dictionary. Rules are plain data: a name, a condition on the facts, and an action that writes new facts or filters places. The loop applies rules in order until no rule changes anything (two passes at most with these rules).

| ID | If | Then |
|---|---|---|
| R1 | `age_group` is youth, adult, or senior | `day_hours` = 10, 8, or 6; `day_end_min = day_start_min + 60*day_hours` |
| R2 | `age_group` is senior | remove places whose effort is in `senior_excluded_effort` |
| R3 | `age_group` is senior | `travel_factor = 1.3` (otherwise 1.0) |
| R5 | `souvenir >= souvenir_boost_threshold` | add `souvenir_boost` to the place's value (base value is `attraction + souvenir`) |
| R6 | `place.category` is in the user's interests | add `interest_boost` to the place's value (does nothing when interests are empty) |
| R4 | `min(close, day_end) - max(open, day_start) < duration` | remove the place (it can never fit) |

Order is R1, R2, R3, R5, R6, R4 (R4 needs the day window from R1). R1 to R5 keep the earlier numbering; R6 is new. Final value = `attraction + souvenir` + R5 bonus + R6 bonus.

```python
def default_rules(cfg: Config) -> list[Rule]
def apply_rules(places, age_group, interests, cfg) -> dict
# returns {"candidates": [Place with value set], "day_start_min": int, "day_end_min": int,
#          "travel_factor": float, "removed": {name: rule_id}, "fired": [rule ids]}
```

`removed` and `fired` exist so tests and the report can show why a place was dropped (explanation).

Multi-day and multi-city: the day window is the same every day and in every city, so run `apply_rules` once **per city** in the route (all six rules, same age group and interests). Do not re-run it per day. R4 uses the nominal day start; a late arrival day is handled by the search itself, which simply finds fewer feasible places.

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

Worst case about `n * 2^n` states. The expert system and `max_candidates_per_day` (20) keep `n` small. See Section 13 for measured numbers.

---

## 9. M3 Greedy baseline (`greedy.py`)

Same signature and return as `plan_day`. From the current position, among feasible unvisited places choose the one with the highest `value / (end - now)` (value per minute including travel and waiting); go there; repeat until none is feasible. Ties break by lower index. Used only for comparison and the viva.

```python
def plan_day_greedy(candidates, start, day_start_min, day_end_min, speed_kmh, factor) -> tuple[list[Stop], float, int]
```

---

## 10. Trip planner (multi-city) and CLI (`planner.py`, `cli.py`)

```python
def plan_trip(dataset_path: str, profile: Profile, cfg: Config = Config(), algorithm: str = "astar") -> Plan
def format_plan(plan: Plan) -> str
```

`plan_trip`:

1. **Validate** the input: age group is one of the three labels; every interest is a known category id, the route is non-empty, has at most `max_cities` entries, no repeated city, every `city_id` exists in the dataset, each city's days are in `1..max_days_per_city`, and the total days are at most `max_total_days`. Otherwise raise `ValueError` with a plain message (the CLI prints it and exits with code 2).
2. `load_dataset` once.
3. For each `(city_id, n_days)` in route order: run `apply_rules(city.places, age_group, interests, cfg)` once for that city to get its candidates, day window, and travel factor.
4. For each day in the city (trip day numbers run across cities):
   - If this is the city's first day and there is a previous city, compute `transfer = intercity(previous, this, cfg)` and set `day_start = day_start_min + transfer.minutes`; otherwise `day_start = day_start_min`.
   - Take the city's remaining candidates. If more than `max_candidates_per_day`, keep the top ones by `value / duration` (a guard; record it, and note it makes that day approximate).
   - Call `plan_day` (or the greedy version) with the city's anchor, `day_start`, the day end, `speed_kmh`, and the travel factor.
   - Remove the visited places from that city's remaining pool and append a `DayPlan`. **A day with no schedulable place is still listed, with no stops.** Do not stop early: a long transfer day can be empty while the next day is full.
5. Fill `Plan.unused` and `Plan.removed` per city, and set `verified_data` to true only if every route city is verified.

`format_plan` sample (all numbers illustrative):

```
Japan Travel Planner | Route: Tokyo 3d -> Kyoto 2d | adult | algorithm: A*
Interests: Shinto shrines, Markets and food streets
Note: place data is unverified; check hours and coordinates before relying on it.

Day 1 | Tokyo (09:00 to 16:50, value 41)
  09:00  Start: Tokyo Station
  09:35  Senso-ji, Asakusa (90 min)  [matches interest]
  11:20  Nakamise-dori (45 min)  [souvenirs]
  ...
Day 4 | Kyoto
  Transfer: Tokyo -> Kyoto, 372 km, about 2h 59m
  11:59  Start: Kyoto Station
  ...
Total value: 262 | Trip: 5 days, 2 cities | Places visited: 21
Not scheduled: Tokyo: Mount X (removed by R2); Kyoto: ...
```

Places with `location_scope == "nearby_day_trip"` are marked `[day trip]`, and places in a selected category are marked `[matches interest]`.

```python
def plan_to_dict(plan: Plan) -> dict      # JSON-safe form used by the web API (Section 16.2)
```

CLI:

```
python -m travelplanner.cli --route tokyo:3,kyoto:2,osaka:2 --age adult [--interests shrine,market] [--algorithm astar|greedy] [--data data/japan_travel_dataset.json]
python -m travelplanner.server [--port 8000] [--data data/japan_travel_dataset.json]   # web UI at http://127.0.0.1:8000
python -m travelplanner.cli --city tokyo --days 3 --age adult        # same as --route tokyo:3
```

`--route` and `--city/--days` are mutually exclusive; one of them is required.

---

## 11. Tests

Test-first for search. Use `pytest`; no plotting backend needed for core tests.

| File | Must check |
|---|---|
| `test_models_config` | Config defaults, dataclass immutability, dict defaults not shared, `Profile.route` shape |
| `test_knowledge` | Dataset loads (12 cities, 135 places, all place ids unique, anchors present); haversine known pair (Tokyo Station to Senso-ji about 5 km, tolerance 0.3); `intercity` is symmetric and Tokyo to Kyoto is about 179 minutes (tolerance 5); clock round trip; load errors (unknown city, duplicate id, wrong schema version, `close <= open`, bad score, place category not in the root list); `load_categories` returns 58 id-label pairs; `category_pool` for Tokyo lists only categories present there, sorted by count then label, and counts add up; travel factor |
| `test_expert` | R1 hours for each age; R2 removes high-effort places for seniors only; R3 factor; R4 removes a place that cannot fit; R5 value boost; R6 interest boost, and no change when interests are empty; `removed` and `fired` filled; rule order; `apply_rules` takes an age group, not a profile |
| `test_astar` | Equals brute-force optimum on 30 seeded random instances of 7 places; `h` never below the optimum at the root on the same instances; never exceeds budget; respects windows; waiting works (place opens after arrival); goal re-queue regression test (instance where the first terminal pop is suboptimal); empty candidates give an empty plan; a late `day_start` yields a feasible, smaller plan; deterministic |
| `test_greedy` | Valid plan; value less than or equal to A* on 30 instances |
| `test_planner` | Invariants below on single- and multi-city plans (1, 3, 5 days); senior plans have no high-effort place; first day of each later city starts at `day_start_min` plus the transfer; empty days are listed; route validation errors (duplicate city, unknown city, too many cities, too many days, bad age group, unknown interest id); selecting interests raises the number of stops in those categories on a seeded case (Tokyo, museum + park + garden); an empty interest set gives the same plan as before; `--city tokyo --days 3` and `--route tokyo:3` give the same plan |
| `test_cli` | Runs with `--route`, with `--city/--days`, and with `--interests`; exit code 2 on invalid input; output contains the totals line and a transfer line for a two-city route |
| `test_server` | Start the server on an ephemeral port in a thread and call it with `urllib`: `/` and the two static files return 200 and nothing else on disk is served (path traversal returns 404); `/api/cities` lists 12 cities; `/api/categories?cities=tokyo` matches `category_pool`; `/api/plan` returns the same itinerary as `plan_trip` for the same input; bad input (unknown city, unknown interest, bad JSON, oversized body) returns 400 with an `error` field; no network access other than localhost |

**Plan invariants (assert on every full plan in tests):** each day's last `end_min <= day_end`; each stop's `start_min >= open` and `end_min <= close`; every stop belongs to its day's city; no place `id` appears twice across the whole trip; stops are in time order and start no earlier than the day's `start_min`; the first day in every city after the first carries a `Transfer` and its `start_min` equals `day_start_min + transfer.minutes`; the total equals the sum of day values; trip days are numbered 1..N with no gaps.

**Oracle:** the brute-force recursive search lives in `tests/` only (`brute_force_day`), never in the package.

---

## 12. Evaluation (`experiments.py`)

Seeded, headless, no network. All experiments use the real master dataset.

| ID | Experiment | Setup | Metrics | Expected |
|---|---|---|---|---|
| E1 | A* vs Greedy | Day 1 of every city (12) times youth, adult, senior (36 runs); plus two sample multi-city routes (for example Tokyo 3, Kyoto 2, Osaka 2) | Total value, runtime, nodes expanded | A* is greater than or equal to Greedy on every run; each day under 1 second |
| E2 | Expert rules on/off | Tokyo and Kyoto, 1 to 3 days, all age groups; "off" skips R2, R3, R4 and uses the default day length | Nodes expanded, time, number of rule violations in the plan (high-effort place for a senior, a visit outside its window) | Rules shrink the search; violations are zero with rules on |
| E3 | Interest preferences | Six cases (for example Kyoto shrine + temple, Tokyo market + shopping district, Tokyo museum + park + garden), adult, 1 day, `interest_boost` 0 versus 8 | Stops in the selected categories out of all stops; total base value (without R6) | The matching share never drops and rises when matching places fit; base value drops only slightly |

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

This is why `max_candidates_per_day` is 20: the synthetic worst case at 20 candidates is about 1.8 s, and the real dataset is far below that (next table). Tokyo's 18 places fit under the cap without approximation.

### 13.1 Real dataset (prototype, same rules and A* logic as this spec)

Setup: owner dataset, adult unless stated, 20 km/h inside cities, rules R1 to R5 applied (R6 was calibrated separately, Section 13.2), days planned in sequence. These are prototype numbers; re-measure in the real code before putting them in the report.

| Check | Result |
|---|---|
| Candidates after the rules, adult | 8 to 17 per city (Tokyo 17, Takayama 8) |
| Largest search on any day (adult, 3 days per city) | 1,347 states (Kanazawa); slowest day 0.05 s (Kyoto) |
| A* vs Greedy, day 1, 12 cities x 3 age groups | Greedy below A* on average 5.8%, worst 19.2%, strictly worse in 26 of 36; Greedy never beat A* |
| Thin later days, adult, 3 days in one city | Tokyo 6, 4, 4 stops; Kyoto 7, 5, 2; Nara 6, 4, 0; Takayama 7, 1, 0 |

City-to-city transfer examples (anchor to anchor, 150 km/h plus 30 min):

| Transfer | km | Minutes |
|---|---|---|
| Kyoto to Osaka | 40 | 46 |
| Osaka to Nara | 30 | 42 |
| Tokyo to Nagoya | 268 | 137 |
| Tokyo to Kyoto | 372 | 179 |
| Osaka to Hiroshima | 279 | 141 |
| Fukuoka to Nagasaki | 106 | 72 |
| Tokyo to Sapporo | 833 | 363 (in reality a flight; the straight-line rail proxy is rough) |

Sample multi-city run (adult, Tokyo 3, Kyoto 2, Osaka 2): the Kyoto arrival day started at 11:59 with 4 stops, the Osaka arrival day at 09:46 with 6 stops, and the other days had 3 to 6 stops.

### 13.2 Interest boost calibration (prototype, real dataset)

Adult, one day. Each cell is stops in the selected categories out of all stops. The last row of the first table is the number of matching places that exist in the city.

| Case (selected categories) | Boost 0 | Boost 4 | Boost 8 |
|---|---|---|---|
| Kyoto: shrine, temple | 4/7 | 4/7 | 4/7 |
| Tokyo: market, shopping district | 2/6 | 2/6 | 3/5 |
| Tokyo: museum, park, garden | 0/6 | 1/6 | 2/6 |
| Osaka: market, shopping district, aquarium | 2/6 | 2/6 | 2/6 |
| Tokyo: viewpoint | 1/6 | 1/6 | 2/5 |
| Hiroshima: memorial park, museum | 1/6 | 2/6 | 2/6 |
| Matching places available | 5, 3, 5, 3, 2, 2 (in the order above) | | |

A boost of 4 barely changes plans, and 8 changes them clearly without turning the preference into a hard filter (a selected place still has to fit the day). That is why `interest_boost` is 8. The slowest case with a boost of 10 (Tokyo, adult) took 0.11 s. Matching is by exact category id; related categories such as `temple` and `temple_garden` are separate bubbles.

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
| Preference handling | Done as a rule (R6, a value boost), not a separate algorithm or a hard filter, so A* and its bound stay unchanged. |
| Search over cities | The user supplies the city order and days, so the core needs no city-level search. Choosing or ordering cities automatically is an optional enhancement. |

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

### Multi-city example (prototype output, illustrative)

Route Tokyo 3, Kyoto 2, Osaka 2, adult. Days 1 to 3 are normal Tokyo days from 09:00. The Tokyo to Kyoto transfer is 179 minutes, so day 4 (Kyoto's first day) starts at 11:59 and plans fewer places; day 5 is a full Kyoto day. Kyoto to Osaka is 46 minutes, so day 6 starts at 09:46. A* plans each day independently from the city's remaining places, so total value is the sum of the daily optima, not a global optimum across days.

---

## 16. Interests and the web UI

### 16.1 Interests (categories)

- **Source:** the root `categories` of the dataset: 58 id and label pairs. Every place's `category` is one of these ids.
- **Pool for a request:** `category_pool(cities, labels, route_city_ids)` returns only the categories that have at least one place in the chosen cities, sorted by count and then label. For Tokyo, Kyoto, and Osaka together this is 25 of the 58.
- **Selection:** optional and multiple. Empty means no preference; R6 then does nothing.
- **Effect:** R6 adds `interest_boost` (8.0) to the value of every place in a selected category. It is a soft preference: a matching place still has to fit the time and opening windows, and strong non-matching places can still be chosen. A* and its heuristic are unchanged (`h` uses the boosted values).
- **Matching:** exact on category id. The categories are fine-grained (`temple`, `temple_garden`, `temple_museum`), so choosing several related bubbles is expected. Grouping related categories is a future enhancement.
- Calibration is in Section 13.2.

### 16.2 Local API (`server.py`)

Standard library `http.server` only. Binds to `127.0.0.1` (default port 8000). JSON only; no CORS; no outside network calls. The dataset is loaded once at startup.

| Route | Method | Purpose |
|---|---|---|
| `/`, `/styles.css`, `/app.js` | GET | The three files in `web/` (a fixed whitelist; anything else is 404) |
| `/api/cities` | GET | `[{"id", "name", "region", "places", "verified"}]` for every city, in file order |
| `/api/categories?cities=tokyo,kyoto` | GET | The bubble pool for those cities (all cities if omitted); 400 for an unknown city |
| `/api/plan` | POST | Body `{"age_group", "route": [{"city_id", "days"}], "interests": [ids], "algorithm": "astar"}`; returns `plan_to_dict(plan)`; 400 with `{"error": "..."}` for any `ValueError` |

Request bodies are limited to 64 KB. `plan_to_dict` returns a JSON-safe dictionary:

```
{ "profile": {...}, "algorithm", "total_value", "verified_data",
  "days": [ {"day", "city_id", "city_name",
             "transfer": {"from", "to", "km", "minutes"} or null,
             "start", "end", "value",
             "stops": [ {"id", "name", "area", "category", "category_label",
                         "arrive", "start", "end", "travel_min", "duration_min",
                         "souvenir", "matches_interest", "day_trip"} ]} ],
  "unused": {...}, "removed": {...} }
```

Times are `"HH:MM"` strings (rounded to the nearest minute).

### 16.3 Web UI (`web/`)

A single page in three steps. Plain HTML, CSS, and JavaScript; no framework, no build step, no CDN, a system font stack, so it works offline.

**Step 1, Your trip.** City chips: click to add a city to the route in click order, click again to remove it. Each chosen city has a days stepper (minus and plus buttons, 1 to 5). The route summary shows the order with move-up and move-down buttons. Age group is three chips (single choice). Continue is enabled when there is at least one city and an age group, and the limits are respected (the page explains the limits instead of failing silently).

**Step 2, What do you enjoy?** The bubble pool. Each category is a round or pill bubble (`<button type="button" aria-pressed>`) in a wrapping pool; click toggles it. Bubble size follows the place count (three tiers: 1, 2 to 3, 4 or more). A selected bubble is filled with the accent color and shows a check mark (never color alone). A counter shows how many are selected; Clear, Skip, and Continue buttons sit below. Choosing nothing is allowed. **There is no drop-down (`<select>`) anywhere in the UI.**

**Step 3, Your itinerary.** Day cards grouped by city; a transfer row between cities; stop rows with time, name, area, and small tags (souvenir, day trip, matches your interests); the day's value; trip totals; the unverified-data banner; Back and Plan again buttons; loading and error states.

**Design requirements** (adapted from the `autonomous-ui-architect` skill to this stack):

- Design tokens (colors, spacing, radii, type scale, motion durations) are defined once in `:root` in `styles.css`; no hard-coded colors or magic numbers in rules.
- Light and dark themes through `prefers-color-scheme`. Text contrast at least 4.5:1, control borders and focus rings at least 3:1. Selected state is not conveyed by color alone.
- Every interactive element has hover, active, and `:focus-visible` states; touch targets are at least 44 px.
- Micro-interactions on bubble press and a gentle idle float in the pool. All motion is disabled under `prefers-reduced-motion: reduce`.
- CSS Grid and `gap` for layout; works from 360 px wide with no horizontal scrolling; `text-wrap: balance` on headings; logical properties where practical.
- No gray placeholder boxes; loading uses a status message and a simple skeleton.
- Semantics: `header` and `main` landmarks, a heading per step, `aria-live="polite"` for step changes and errors, a visible label for every control, a keyboard path through every step.
- JavaScript: one script, small functions, a single state object, `fetch` to the local API only, DOM built with `textContent` and element creation (never `innerHTML` with API data).

### 16.4 Manual UI checklist (the agent who builds the UI logs the result on the board)

1. Server starts; the page loads with no console errors and no network request leaves localhost.
2. Tab order works through all three steps; Space and Enter toggle bubbles; focus ring always visible.
3. Screen reader announces each bubble's name and pressed state, and announces step changes.
4. Works at 360 px, 768 px, and 1280 px widths; no horizontal scroll.
5. Light and dark themes both pass the contrast rule; reduced motion stops all animation.
6. Two-city route with interests produces an itinerary matching the CLI output for the same input.
7. Error cases show a clear message: no city selected, too many days, server stopped.
