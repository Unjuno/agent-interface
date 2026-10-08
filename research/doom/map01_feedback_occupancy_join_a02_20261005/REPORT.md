# Exact event identity for retained MAP01 feedback and held observations — A02

Status: `PASS_EXACT_IN_HOLD_FEEDBACK_EVENT_IDENTITY_SCOPED`.

## H/T/D/C/U

- **H:** The first independently reconstructed health/ammo feedback frame for each of the three admitted v39 primary plans is the exact timestamped observation event recorded inside that plan's hold step and no later than the v7 confirmed-any-key-held endpoint.
- **T:** Decode the hash-pinned #503 full-action artifact; bind its v39 report/events identities to the v7 occupancy result and the separately retained current-main telemetry-gap raw event stream; match plan ID, step, sequence, monotonic `capture_ns`, and RGB-frame digest across `typed_observation` and `observation`; compare the event with its hold interval.
- **D:** PASS requires one exact typed/visual pair for each of the three admitted plans, identical frame hashes, the observation in the associated hold step, capture time between first key acknowledgement and confirmed-any-key endpoint, and an independent raw-event audit with zero errors.
- **C:** Temporal overlap may reflect environmental changes or harmful effects. Plans contain multiple simultaneous or sequential keys. The records cannot identify a causal key or prove action-to-feedback causality.
- **U:** One retained stochastic v39 episode; software-side any-key evidence, not per-key physical release timing; health/ammo only; no new live game/model/GUI/input allocation, matched benefit, safety rate, or MAP01-clear claim.

## Result

| Plan | Sequence | Reconstructed change | Exact observation identity | Relation to held interval |
|---|---:|---|---|---|
| `plan-0-primary-0-1` | 30 | ammo 48→47 | typed + visual event and frame hash match | inside interval, before its final confirming sample |
| `plan-3-primary-0-1` | 115 | health 68→65; ammo 44→43 | typed + visual event and frame hash match | exactly the final confirming sample |
| `plan-4-primary-0-1` | 161 | ammo 41→40 | typed + visual event and frame hash match | exactly the final confirming sample |

The final confirming sample is the last in-hold observation used by v7's conservative any-key lower bound. Two feedback observations and held-boundary samples are literally the same sequence, clock, and frame digest. This narrows the earlier interval-join result: the ties are shared source events, not just rounded-duration coincidences.

## Provenance and execution

The source hashes and exact commands are recorded in `SOURCE_SHA256SUMS.txt` and `COMMANDS.txt`. The source, thresholds, and decision rule were frozen in `FREEZE.json` before the single candidate computation. The independent raw-event auditor passes 3 feedback rows, 3 exact observation pairs, 2 endpoint ties, zero errors. The existing v7 test passes and the telemetry-gap evidence package's six-file manifest verifies. No source artifacts or retained results were edited.

This resolves a measurement-lineage ambiguity only. There are no per-key release events in the retained stream; the v39 telemetry audit explicitly finds that all 218 observations label semantic completion `unknown`. Live useful task effects, recovery, and real-time threat control remain open.
