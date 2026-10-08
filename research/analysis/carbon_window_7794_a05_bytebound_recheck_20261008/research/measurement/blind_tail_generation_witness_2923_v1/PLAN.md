# #2923 blind-tail generation witness — H/T/D/C/U

## H

Under the retained #1354 two-displacement representation, phase>0 blind-tail reversals are safely unidentifiable. Holding the nominal 7.3 px motion, ±0.75 px full-motion compatibility bound, one-reversal family and fail-closed rule fixed, one fresh caller-visible X11 property-generation witness after the newest sampled displacement can identify that the sole reversal occurred after the sample. Missing, stale, cross-window, duplicate or out-of-order evidence must remain UNKNOWN.

## T

Private Xvfb/Tk/Xlib fixture; no model/provider, external network experiment, task input, user desktop or shared runtime.

CONTROL: `TWO_DISPLACEMENT`, matching #1354's blind-tail representation semantics.
CANDIDATE: `TWO_DISPLACEMENT_PLUS_GENERATION`; the only added factor is `_AI_MOTION_GENERATION` plus raw `PropertyNotify` chronology bound to the current target window.

Formal, one top-level invocation, 40 fresh Xvfb/application lifetimes:
- 24 exact phase>0 blind-tail rows: age100 phases94..99 × directions±1, age200 phases1..6 × directions±1;
- 2 age200 phase0 timing-identifiable controls;
- 4 stable/no-reversal controls;
- 10 bad-witness controls: stale, wrong-window, missing, duplicate and out-of-order × directions±1.

Three XGetImage scanlines are retained only to reproduce the predecessor two-displacement state. There is **no third/newer image sample after the blind-tail reversal**. The reversal witness is event-generation evidence, not an extra visual sample.

Candidate may resolve a blind-tail row only when exactly one target-window `PropertyNotify` for the frozen atom is received after the newest capture and the property value advances exactly 1→2. It then infers the opposite current direction under the frozen at-most-one-reversal model. Otherwise it returns UNKNOWN. Authority is always false.

Excluded construction uses ages/phases outside the formal boundary set. Formal reruns/replacements/tuning0.

## D

`PASS_BLIND_TAIL_GENERATION_WITNESS_SCOPED` iff:
- 40/40 rows complete with exact source/process evidence;
- all 24 blind-tail CONTROL decisions remain UNKNOWN;
- all 24 valid-witness CANDIDATE decisions equal independent oracle current direction;
- wrong-direction count = 0;
- all 10 stale/wrong-window/missing/duplicate/out-of-order controls remain UNKNOWN;
- all 6 stable/phase0 controls preserve the expected predecessor behavior;
- every observed full-motion displacement remains within 7.3±0.75 px;
- fresh witness resolves 12/12 phase>0 blind rows at age100 and 12/12 at age200, lifting the retained safe ceilings from 188/200=.94 to 200/200=1.00 when combined with #1354's already-safe rows;
- independent raw audit errors=[];
- 8/8 copied-evidence semantic/provenance corruptions reject;
- formal1/reruns0/replacements0/tuning0.

`HOLD_NO_ADDITIONAL_DISCRIMINATOR` if valid current generation evidence does not break the ambiguity. Any wrong direction or stale/cross-window/duplicate/out-of-order witness accepted is FAIL. Missing source/process/raw evidence is STOP/HOLD.

## C

The fixture cooperatively publishes a reversal generation. This is not a universal X11 motion signal and does not show that arbitrary applications expose the same event. The at-most-one-reversal model is inherited; multiple reversals would invalidate the inference. The 1.00 reconstructed ceiling combines fresh witness resolution with retained #1354 safe rows; it is not a new 200-row live denominator.

## U

No wall-clock 10 Hz transfer, semantic object identity, model benefit, GUI task success, task effect, human-tempo or production-runtime claim. A PASS establishes only that a current independent event-generation witness can break this known representation alias in the cooperative transfer fixture.

## Variable table

| symbol/field | meaning | SI unit | definition | domain/assumption | type |
|---|---|---|---|---|---|
| d1,d2 | newest two observed displacements | m unavailable; stored px | centroid differences between three XGetImage scanlines | |d|-7.3 <=0.75 px | scalar real (pixel coordinate difference) |
| g | motion generation | 1 | X11 CARDINAL property `_AI_MOTION_GENERATION` | positive integer, same window/session | scalar integer |
| t_c | capture receive timestamp | s (stored ns) | `time.monotonic_ns()` immediately before XGetImage | same process clock only | scalar integer |
| t_e | PropertyNotify receive timestamp | s (stored ns) | `time.monotonic_ns()` on event receipt | same process clock only | scalar integer |
| q | current direction | 1 | {-1,+1}, or UNKNOWN candidate state | at most one reversal | categorical scalar |
| N | formal rows | 1 | 24 blind +2 phase0 +4 stable +10 bad witness | N=40 | scalar integer |

Dimensional check: the only ordering test compares `t_e > t_c` on the same monotonic clock, so both sides have seconds (stored as ns). Pixel displacement compatibility compares pixel units only. Generation and decision metrics are dimensionless.
