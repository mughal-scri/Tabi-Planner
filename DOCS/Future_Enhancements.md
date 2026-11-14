# Future_Enhancements.md: Japan Travel Planner

**Everything in this file is out of scope for the course build.** Agents must not implement any of it without an explicit owner instruction. It exists so good ideas are kept without growing the project.

---

## 1. Ideas by effort

| ID | Enhancement | Effort | Benefit | Notes |
|---|---|---|---|---|
| FE-01 | Automatic city order for a chosen set of cities | Small | Less user effort; shorter transfers | Try every order of up to 6 cities (first city fixed) and keep the smallest total transfer time; also optional Phase 6 task P6.1 |
| FE-02 | Route plot of each day | Small | Visual demo | Matplotlib scatter with day colors and arrows |
| FE-03 | Return-to-hotel constraint | Small | More realistic days | Add the return leg to the feasibility check and to `h`; config flag |
| FE-04 | Verified opening days (weekday closures) | Small to medium | Fewer impossible plans | Add a `closed_days` field and a start weekday input |
| FE-05 | Preferences beyond categories (pace, walking tolerance, time-of-day habits) | Medium | More personal plans | Category interests already exist (rule R6); these would be further expert-system rules that adjust `value` or the day length |
| FE-06 | Budget limit | Medium | Cost-aware plans | Second constraint in search; the bound needs a cost term |
| FE-07 | Hill Climbing or GA for large cities | Medium | Scales past 20 candidates | Start from the Greedy plan and improve; compare with A* on small cases |
| FE-08 | Real travel times from a transit or maps source, inside and between cities | Medium | More accurate schedules | Replace `travel_min` and `intercity`; keep the interfaces; could add rail versus flight choice and fares |
| FE-09 | Choose which cities to visit from a total number of days | Large | Fully automatic trips | A city-level search above the day-level A*: pick and order cities to maximize total value minus transfer time |
| FE-10 | Map view and a framework rewrite of the web UI | Medium to large | Route drawn on a map; component-based UI | The plain local page already exists; a map (Leaflet) and a React and Tailwind rewrite are optional; keep the API and the core unchanged |
| FE-11 | Learned scores from reviews or ratings | Large | Less hand-set data | Needs a data source; no pre-trained model by default |
| FE-12 | Plan all days of a city together | Medium | Better total value | Days are currently optimized one at a time, so total value is a sum of daily optima; a joint search over days would remove that limit |
| FE-13 | Group related categories into broader interest bubbles | Small | Easier choices | For example one Museums bubble covering museum, science, art, and open-air museums; the dataset's 58 categories are fine-grained and matched exactly |
| FE-14 | Interest strength (low, medium, high) | Small | Finer steering | Replace the single `interest_boost` with a per-category weight |
| FE-15 | Restaurants and food venues in the dataset | Medium | A real food interest | The dataset has food markets and food streets but no restaurants; needs new data |

## 2. Rules for adding any of these later

1. Write it into `PRD.md` and `Design_Doc.md` first.
2. Add Roadmap tasks and a decision on the board.
3. Keep interfaces stable: `plan_day` and `plan_trip` signatures should not change unless the Design Doc does.
