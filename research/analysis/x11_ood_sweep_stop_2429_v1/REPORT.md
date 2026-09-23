# X11 OOD threshold sweep — STOP

## H/T/D/C/U

- H: OOD threshold quantile sweep should expose a useful utility/safety tradeoff.
- T: sweep 95th, 99th, and 99.5th percentiles of non-self base nearest-reference distances over fixed base, old-shift, and fresh-family X11 sets.
- D: same source-bound manifests and Euclidean downsampled pixel distance as #2409.
- C: calibration-only result; no semantic/runtime claim.
- U: thresholds must be distinguishable before selecting a gate.

## Result

All three quantiles produced the identical threshold **0.07607439** and identical routing:

| set | accepted |
|---|---:|
| base | 160/160 |
| old shift | 143/160 |
| fresh | 0/160 |

The base reference contains many tied distances, so this sweep has no discriminative calibration value. **STOP calibration attempt; no threshold change or promotion.** Previous OOD results remain unchanged.
