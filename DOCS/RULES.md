# RULES.md: Rules for agents working on the Japan Travel Planner

Read this first, then `AGENT_BOARD.md`, then `PROJECT_MEMORY.md`. Do not scan the repository to learn project state.

---

## 1. Read order and authority

1. `DOCS/RULES.md` (this file), `DOCS/AGENT_BOARD.md`, `DOCS/PROJECT_MEMORY.md`.
2. For a planned module: its section in `DOCS/Design_Doc.md`, its source file, and its test file. Nothing else.
3. For a bug: its test and implementation first; open a direct dependency only if the failure requires it.

Authority when documents disagree: owner instruction, then `Design_Doc.md`, then `PRD.md`, then `Roadmap.md`, then `PROJECT_MEMORY.md`. If memory disagrees with code plus a passing test, fix the memory file and log it on the board.

## 2. Scope guard

- Build only what `PRD.md` and `Design_Doc.md` describe. Nothing in `Future_Enhancements.md` is in scope.
- Do not add features, options, modules, files, or dependencies on your own. If something seems missing, write it as an open issue on the board and ask the owner.
- Build in Roadmap order. Do not start a phase before the previous one passes its tests.
- This project is the Japan Travel Planner only. Do not touch files outside this repo.

## 3. Code rules

- Python 3.10+. Standard library only for the package (see `Tech_Stack_DOC.md`). Matplotlib only in `experiments.py`.
- Follow `Design_Doc.md` Section 3 conventions exactly: minutes since midnight, `(lat, lon)`, haversine in km, travel factor applies to travel only, value computed once by the expert system.
- Keep every tunable in `Config`. No magic numbers elsewhere.
- No global random state. Core code uses no randomness. Experiments take a seeded `random.Random`.
- Small functions, type hints on public functions, plain names. Prefer clear code over clever code.
- Do not use network calls, and do not write files outside `results/` and the user's explicit output paths.
- Heap entries always include an integer tie-breaker. A* must keep the goal re-queue at f = g (`Design_Doc.md` Section 8.3).
- Apply the `senior-developer-skill` guidance to all code work (clean code, careful debugging, small reviewable steps). The `autonomous-ui-architect` skill applies only if the owner approves a UI; the CLI build does not need it.

## 4. Testing rules

- Write the test first for search and rules. A module is not done until its tests pass.
- Run `.venv/bin/pytest -q` before ending any session and record the pass count on the board.
- The brute-force oracle lives in `tests/` only; never import it from the package.
- Tests are deterministic: fixed seeds, no network, no dependence on the current date or clock.
- Never weaken or delete a test to make it pass. If a test is wrong, say why on the board and fix it deliberately.
- Every full plan in tests must satisfy the invariants in `Design_Doc.md` Section 11.

## 5. Data honesty

- Place data is hand-written. Never present guessed coordinates, scores, durations, or opening hours as verified facts.
- Keep `"verified": false` in a data file until the owner confirms it against official sources.
- Do not invent places or facts to fill a file. Ask the owner or leave the entry out.
- Report only numbers you actually measured. Do not quote the prototype reference numbers in `Design_Doc.md` Section 13 as results of this project.

## 6. Honesty and reporting

- If something fails, is incomplete, or you skipped a step, say so plainly on the board. Do not claim "done" without a passing test.
- If you disagree with a document, do not silently deviate. Write a decision or an open issue and follow the authority order.
- Do not read PDFs, notebooks, or `results/` contents unless a task requires it.

## 7. Git and files

- Do not commit, push, or rewrite history unless the owner asks.
- Preserve unrelated existing changes in the working tree.
- Do not rename or delete files outside your task. Keep the repo map on the board correct.
- Deliver files as plain files in the repo. Do not publish documents or code as hosted pages unless the owner asks.

## 8. Agent board protocol

`AGENT_BOARD.md` is the shared whiteboard. It saves every later agent from re-reading the repository.

**Before you start:** read the Quick Start, the Status table, Open issues, Decisions, and Gotchas. Mark your module IN PROGRESS with your name.

**Before you stop (always, even if you only got part way):**

1. Add an Activity Log entry at the top (newest first) using this format:

```
### YYYY-MM-DD | <agent name> | <short title>
- Did: <what changed, one or two lines>
- Files: <paths created or edited>
- Verified: <exact commands and results, for example `.venv/bin/pytest -q` -> 12 passed>
- Notes: <surprises, decisions, risks>
- Next: <the single next task>
```

2. Update the Status table (status, tests, last touched, notes) and the Repo map (drop "(planned)" when a file exists; add, rename, or delete lines as needed).
3. Add to Decisions (`D-NNN`), Open issues, or Gotchas if you made or found any.
4. Update `PROJECT_MEMORY.md` only for project-wide facts (phase status, public interfaces, verified test count, next task, contracts, cross-cutting gotchas).
5. Tick the Roadmap checkboxes for the tasks you completed.

Keep entries short. When the log passes about 15 entries, compact the oldest into the Archive section as a few summary lines.

## 9. Definition of done for a task

1. Code matches `Design_Doc.md` for that module.
2. Its tests exist and pass, and the full suite passes.
3. Board, memory (if needed), and Roadmap updated.
4. No out-of-scope additions.
