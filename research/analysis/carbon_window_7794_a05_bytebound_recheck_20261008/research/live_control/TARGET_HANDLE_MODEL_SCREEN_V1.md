# Target-handle fixed-state model screen v1

This preregistered ABBA screen compares two representations of the same final
Chromium Save action with Luna-low and Fast disabled. Coordinate calls receive
the retained 1280x800 live frame and must infer an absolute point. Handle calls
receive no image; they receive the current `REVALIDATED` target handle and the
permitted `[20,9]` relation. No GUI input occurs in this screen.

All four strict outputs are correct. Both coordinate calls select a point inside
the frozen Save region, and both handle calls reproduce the exact typed handle
action. This passes the fixed-state correctness endpoint.

| Order | Arm | Reported input | Cached input | Runner ms | Correct |
|---:|---|---:|---:|---:|---|
| 1 | coordinate | 12,583 | 1,792 | 6,022.869 | yes |
| 2 | handle | 11,332 | 0 | 11,309.110 | yes |
| 3 | handle | 54,244 | 42,240 | 9,840.163 | yes |
| 4 | coordinate | 12,583 | 1,792 | 4,628.573 | yes |

The preregistered promotion gate fails. Mean reported input is12,583 for the
coordinate arm and32,788 for the handle arm. Even subtracting reported cached
input as a derived diagnostic gives10,791 versus11,668. The second identical
handle call reports42,240 cached tokens, showing that this ephemeral CLI path did
not hold the surrounding caller context constant enough to attribute the token
difference to image omission.

Decision: retain the first four calls without retry or prompt repair. The result
supports typed-action usability on one fixed target, but establishes no token,
cost, latency or live-task improvement. Before a fresh live A/B, isolate the
model-facing context and explain or eliminate the identical-prompt token variance.
The frozen plan, exact prompts, event streams, arrival timings, usage records,
source hashes and audit are under `results/target-handle-model-screen-01`.
