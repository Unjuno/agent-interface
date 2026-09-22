# Issue #2542 — five-sample X11 reversal history-depth successor

Allocation: `x11-history-depth-2542-20260922-01`.
Owned additive path: `research/measurement/x11_reversal_history_depth_2542_v1/`.
Owned branch: `research/x11-history-depth-2542-20260922-v1`.

## H
Hold #1335's saturated-red X11 centroid path, logical 100 ms geometry, 7.3 px full step, ±1.0 px point envelope, ±2.0 px displacement compatibility, one-reversal family, ages {25,50,75,100,150,200}, directions ±1 and phases0..99 fixed. Change only retained history from H3 to H5. H5 should reduce UNKNOWN without wrong directions. H3 must reproduce #1335.

## T
Provided Linux x86_64 execution container, CPython3.13.5, Tcl/Tk8.6, Python-Xlib0.15; private Xvfb 320x200x24, TCP disabled, ephemeral Xauthority. No model/provider, host desktop, task input, user data or experiment network.

Formal: 1200 matched trajectories; each renders five logical samples at -phase,-100-phase,...,-400-phase ms, oldest→newest. The same five real XGetImage scanlines feed H3 (newest3) and H5 (all5). Four private sessions own phase blocks0-24/25-49/50-74/75-99. Total6000 scanlines, losslessly retained.

Decision rule: classify each 100 ms interval as full +, full -, or mixed using the frozen ±2 px compatibility around ±7.3 px. Enumerate feasible at-most-one-reversal worlds: intervals before the reversal must match -s, after it s, with only the containing interval unconstrained; reversal before oldest and after newest are explicit. Return direction only if exactly one current direction is feasible; else UNKNOWN. H3 must equal the frozen #1311/#1335 three-sample rule on every row.

Excluded construction: ages40/110/175 and phases0.5/33.5/66.5/99.5 only. Formal invocation1; reruns/replacements/tuning0.

## D
PASS only with1200 trajectories/6000 frames, four clean sessions, H3 exact reproduction of #1335 accuracies {25:.15,50:.40,75:.65,100:.90,150:1.00,200:.89}, H3 legacy disagreement0, H3/H5 wrong0, H5 accuracy>=.95 at100/150/200, every H5 proposal uniquely feasible, all point errors<=1 px, malformed/stale/order/cadence controls fail closed, independent raw audit and >=10 corruption controls pass.

Safe recovery miss => HOLD_HISTORY_DEPTH_INSUFFICIENT. Any wrong direction => FAIL_HISTORY_DEPTH_SAFETY. Provenance/denominator/audit contradiction => STOP/FAIL_INTEGRITY.

## C/U
This is geometry-equivalent known-speed/at-most-one-reversal research only. More history cannot repair motion-class violation, stale lineage or a wrong point bound. No wall-clock10Hz, semantic target, model/task, input authority, token/latency, human-tempo or production claim.