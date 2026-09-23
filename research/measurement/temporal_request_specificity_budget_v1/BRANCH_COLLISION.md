# #1648 branch-collision retention note

The original reservation branch `research/temporal-request-specificity-budget-1648` is intentionally **not** the merge candidate.

After the verified formal had already run locally and its exact source bundle was retained, three unexpected commits appeared on that branch:

- `bc7e6934` — `Freeze #1648 PLAN.md`
- `7d3011bf` — `Freeze #1648 prove.py`
- `a8233bee` — `Freeze #1648 audit.py`

Their Git blob IDs do not match the exact source used for the retained formal. The original branch is therefore preserved as collision provenance and is not rewritten or merged.

This r2 branch starts from a later current main and carries only:
- the human-readable retained report;
- exact hash-bound formal source bundle;
- exact evidence bundle;
- bundle hash manifest;
- reconstruction script.

No formal rerun, replacement, or tuning occurred.
