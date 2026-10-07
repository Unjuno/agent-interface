# Issue #59 — retained v39 fire-cover ammo timeline (posthoc)

**Disposition: `NO_ZERO_EXPOSURE`; independent reconstruction `PASS` (5/5).**

This is a read-only posthoc reconstruction from the exact retained report and event-log Git blobs pinned in `FREEZE.json`. It is exploratory, not preregistered, and adds no live allocation. The analysis found three model-wait intervals whose active cover included `retreat_fire`:

| Decision | Typed observations | Ammo first → last (minimum) | Decreases | Health first → last | Policy invalidation |
|---:|---:|---:|---:|---:|---|
| 1 | 32 | 46 → 44 (44) | 2 | 91 → 85 | none |
| 4 | 41 | 43 → 41 (41) | 2 | 65 → 61 | none |
| 5 | 49 | 40 → 37 (37) | 3 | 55 → 48 | health |

Across the trace there are 218 typed observations and 634 event rows. None of the three windows observed ammo zero. The trace has one aggregate `post_control_score` row and no time-local per-action effect events; the aggregate kill count must not be attributed to any window. See `RESULT.json`, `AUDIT.json`, and the exact input/script digests in `FREEZE.json`.

**Interpretation boundary.** The telemetry demonstrates observed ammo decreases while a prior cover policy contained a fire action. It does not establish that a physical fire key was continuously held, that firing caused the decreases, or that any interval produced a useful effect. It does not test zero-ammo guard behavior, causal benefit/harm, survival, or MAP01 completion. No game, controller, model, GUI, or input was rerun.

## Reproduction

From the repository root, with the pinned base commit available locally:

```sh
python3 -B research/doom/v39_fire_cover_ammo_timeline_59_p01_20261005/analyze.py
python3 -B research/doom/v39_fire_cover_ammo_timeline_59_p01_20261005/audit.py
```

Both scripts refuse to infer or mutate the source trace. The candidate refuses to overwrite an existing result. The audit independently reconstructs the window rows from the pinned Git blobs.
