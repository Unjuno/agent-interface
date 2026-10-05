# Astra health-guard threshold replay A01

**Result: the current V39 health guard has a concrete threshold boundary in this retained episode.** The controller computes `hard_minimum = max(critical_health_minimum, source_health - maximum_health_loss)`. Replaying the current `ObservableSignalGuard.evaluate` over PR #7909's selected manually transcribed health samples gives:

| maximum health loss | hard floor from 100 | first saved invalidating sample | observed position |
|---:|---:|---:|---|
| 3 | 97 | 47.0 s, health 96 | during pending cover |
| 4 | 96 | 54.8 s, health 94 | during pending cover |
| 5 | 95 | 54.8 s, health 94 | during pending cover |
| 6 | 94 | 56.4 s, health 87 | first local-plan sample |
| 12 (existing example) | 88 | 56.4 s, health 87 | first local-plan sample |

At a loss threshold of 3, the guard would have requested a new decision at the first changed-health sample. This is 9.2 game-seconds before the last pending-overlay sample at 56.2 s (9.4 s before the first local-plan sample at 56.4 s). Thresholds 4–5 cross at 54.8 s, 1.4 s before the last pending sample; thresholds 6 and 12 cross only at/after the first local-plan sample. These are replay-clock differences, not measured cancellation latency.

The candidate invokes the current-main production guard evaluator and AST-extracted `guard_spec`; the independent audit recomputes the thresholds and crossing times from the exact copied `VISUAL_READOUT.json`. The threshold 3 result is the loosest tested threshold that triggers at the first changed sample. It may also stop useful cover on benign damage. No threshold is recommended for general use from one trace.

Input provenance: PR #7909 head `2b7815984dccc7c9fcbf8836677e452ce3347723`; exact readout SHA-256 `610b77f02302150f26c7de81e46bcba5e8a4fc646d6195442c86db93c6305724`. Production controller and guard are pinned to main `f60752d0fb71595363a80977636ca74c1fd10b21`. Health/phase entries are selected manual transcriptions at sparse timestamps; no value is interpolated. This result does not demonstrate that the live V39 reader would emit these rows at this cadence, that the planner cancellation or empty release succeeds, or that stopping the cover improves MAP01 outcome. A prospectively frozen live exposure with useful feedback, recovery, per-key release, ammo/progress, and terminal score remains necessary.

Reproduce the one candidate and independent arithmetic audit with `python3 candidate.py` and `python3 audit.py`. No game, model, GUI, or input ran. OrbStack remained unavailable after its earlier image-inventory error; this deterministic replay ran on host Python without retrying/pulling an image.
