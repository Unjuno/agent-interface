# Conditional V39 health-guard crossing on retained MAP01 replay

## H / T / D / C / U

**H.** The existing V39 authored health-floor contract, applied conditionally to the retained decision-4 HUD readouts, distinguishes guard configurations that would invalidate during the recorded cover wait from those that would not. It cannot react to a threat while all guarded values remain unchanged.

**T.** Enumerate every accepted `critical_health_minimum` (1..min(source health, 200)) and `maximum_health_loss` (0..20) for source health 100. For each pair compute `floor=max(critical, 100-loss)` and locate the first retained waiting sample with `health < floor`. Compare the result to an independent threshold-frequency partition. Input is the retained manual HUD readout; this is a new conditional contract analysis, not a rerun of the old game allocation.

**D.** PASS_CONDITIONAL_FINITE_ENUMERATION only when all 2,100 valid parameter pairs are represented, the frozen source SHA matches, both implementations agree, and counts partition exactly. Any disagreement fails. No live or causal claim follows from this result.

**C.** Alternative interpretations include stale/unbound historical values, guard polling cadence missing a change, and gameplay damage or ammo use occurring between sparse manual readouts. The previous video replay samples pixels every 0.2 game-seconds, but these manual HUD values are only available at selected frames.

**U.** The replay did not run V39, preserve the V39 signal receipts, or establish what V39 would have observed or done. It does not establish threat detection, cancellation latency, physical key release, useful feedback, recovery, or task success.

## Result

Source SHA256: `610b77f02302150f26c7de81e46bcba5e8a4fc646d6195442c86db93c6305724`.

| Symbol | Meaning | Unit | Domain / assumption | Type |
|---|---|---|---|---|
| `H` | health at guard creation | health points (HUD percentage points) | `1..200`; observed source is 100 | integer |
| `C` | authored critical health minimum | health points | `1..min(H, 200)` | integer |
| `L` | authored maximum allowed health loss | health points | `0..20` | integer |
| `F` | fixed hard health floor, `max(C, H-L)` | health points | `C..H` | integer |
| `h(t)` | sampled current health at game time `t` | health points | retained manual HUD samples | integer |
| `t` | game time of the HUD sample | seconds | selected frames from one 2x video replay | real-valued timestamp |

Invalidation condition: `h(t) < F`. This is a discrete state threshold; the timestamps inherit the retained source cadence and transcription limits.

All 2,100 accepted pairs partition into 468 with floor ≥97 (first invalidating sample 47.0 s, health 96), 222 with floor 95 or 96 (first invalidating sample 54.8 s, health 94), and 1,410 with floor <95 (no invalidation in the sampled waiting interval through 56.2 s, health 94). Sampled ammo remains at least 37, so the paired ammo floor of 1 does not invalidate in these readouts. The 56.4 s sample (health 87) is after the recorded model-return boundary and is excluded from waiting-only classification.

The counts are an exhaustive partition of allowed parameter values, not recommended settings and not runtime probabilities. In this discrete set, the guard is a health-loss threshold; it has no full-scene threat input. Any enemy appearance that does not change health, ammo, validity, binding, or freshness cannot trigger this guard. The current goal therefore still requires fresh live threat exposure to test monitor cadence, cancellation/release, feedback/recovery, and task effect together.

## Reproduce

From repository root, run `python research/doom/v39_guard_crossing_replay_a01_20261008/analyze.py`. It writes only `RESULT.json` beside itself. It refuses any `VISUAL_READOUT.json` whose SHA-256 differs from the frozen value above, then compares the enumerator's first-invalidation distribution against a separate floor-frequency/running-minimum calculation. Run `python -m unittest research/doom/v39_guard_crossing_replay_a01_20261008/test_analyze.py` for the frozen-source reproduction and mutation checks. The source artifact is read-only.
