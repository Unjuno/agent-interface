# WSLc XDamage change latch on a stable X11 target

This exploratory follow-up to `wslc_stable_latch_gap_control_20261031` tests whether X11 DAMAGE notifications can supplement sampled screenshots. A separate X connection subscribes to raw-rectangle damage on both the root and a stable, textured target window. The test drains notifications after a transient change and restoration, then latches any notification; it also checks the original center patch at sampled times. If both checks pass, the existing guarded keyboard path sends a scripted 100 ms F hold to the synthetic target. There are no model calls, real game or network.

| Allocation | Change between screenshot samples | Change-stage notifications (root / target) | Action |
|---|---|---|---|
| p01 | none | 0 / 0 | completed; target saw F press and release |
| p02 | draw on target at guarded patch, then restore | 1 / 1 | withheld |
| p03 | map overlay over guarded patch, then remove | 1 / 0 | withheld |
| p04 | draw far outside guarded patch, then restore | 1 / 1 | withheld |

In p02/p03 an independent direct X11 witness captured the magenta transient, and later sampled patch images matched the source. The retained notification records show that the event latch blocked both cases despite the sampled-image gap. In p04 the changed 8x8 area was outside the checked patch; a whole-drawable event rule still withheld the action. The target is a synthetic fixture and the test cannot prove that an outside change is semantically irrelevant in general. p01–p03 were frozen together, in fixed order. p04 was separately frozen after the first outcomes to probe over-refusal; it is not an independent randomized control.

This is evidence that DAMAGE is a promising additional signal in these specific Xvfb cases, not a complete change detector, an atomic fencing mechanism, or a production safety guarantee. The test drains events before deciding; it does not fence a change between the last drain and key emission. Event delivery loss, server failure, other drawable types, compositors, occlusion, high-rate noise, backlog, resource costs and coordinates under resizing remain untested. Notification rectangles describe damage, not semantic changes or target identity. A rule that latches every event can unnecessarily stop useful work, as p04 illustrates. No MAP01 success, inference speedup or task-level benefit is established.

All four isolated network-none WSLc runs used the pinned image `sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25`, one CPU and 1 GiB, private Xvfb, and the same read-only Python runtime subset checked in the earlier fixed-patch probe; intervening main changes were research only. The named containers were confirmed exited and removed. The clean action receipt and final owner close recorded neutral release, and all F keymap readbacks were up; other arms sent no action. The direct witness, event reader and target event queue are separate X11 observations in the same test process/server, not independent physical sensors.

`python audit.py` (Pillow, normal Python mode) checks frozen runner hashes, witness pixels, saved screenshot hashes and patch differences, retained damage-event records and rectangle relation, decision, target key events, and release receipts. The ZIPs retain conditions, runner, event records, images and output. The next integration question is whether a narrowly scoped event stream can be bound to the guarded target and drained/fenced at the action boundary without dropping events or treating unrelated redraws as semantic failures.
