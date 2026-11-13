# Future_Enhancements.md: Japan Travel Planner

**Everything in this file is out of scope for the course build.** Agents must not implement any of it without an explicit owner instruction. It exists so good ideas are kept without growing the project.

---

## 1. Ideas by effort

| ID | Enhancement | Effort | Benefit | Notes |
|---|---|---|---|---|
| FE-01 | Kyoto and Osaka data files | Small | More cities in the demo | Data only; also listed as optional Phase 6 |
| FE-02 | Route plot of each day | Small | Visual demo | Matplotlib scatter with day colors and arrows |
| FE-03 | Return-to-hotel constraint | Small | More realistic days | Add the return leg to the feasibility check and to `h`; config flag |
| FE-04 | Verified opening days (weekday closures) | Small to medium | Fewer impossible plans | Add a `closed_days` field and a start weekday input |
| FE-05 | Preference layer (food, nightlife, nature) | Medium | Personalized values | Becomes a second expert-system stage that adjusts `value` |
| FE-06 | Budget limit | Medium | Cost-aware plans | Second constraint in search; the bound needs a cost term |
| FE-07 | Hill Climbing or GA for large cities | Medium | Scales past 20 candidates | Start from the Greedy plan and improve; compare with A* on small cases |
| FE-08 | Real travel times from a transit or maps source | Medium | More accurate schedules | Replace `travel_min`; keep the interface |
| FE-09 | Multi-city trips | Large | Realistic trips | Add a city-level stage; trains between cities |
| FE-10 | Web or map UI | Large | Better demo | If done, apply the UI workflow skill; keep the core unchanged |
| FE-11 | Learned scores from reviews or ratings | Large | Less hand-set data | Needs a data source; no pre-trained model by default |

## 2. Rules for adding any of these later

1. Write it into `PRD.md` and `Design_Doc.md` first.
2. Add Roadmap tasks and a decision on the board.
3. Keep interfaces stable: `plan_day` and `plan_trip` signatures should not change unless the Design Doc does.
