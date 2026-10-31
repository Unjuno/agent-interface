# WSLc spatial XDamage latch probe

This controlled Xvfb follow-up to `wslc_xdamage_change_latch_probe_20261031` asks whether a root-window damage rectangle intersecting the guarded 8x8 patch can avoid the previous whole-drawable rule's refusal for a distant change. All four cases use the same research runner and a stable textured synthetic target. The event reader collects raw-rectangle DAMAGE notifications from root and target; only root rectangles intersecting the source patch latch. The sampled-pixel latch remains active. If both permit, the existing guarded X11 keyboard path sends a scripted 100 ms F hold; the target event queue records press and release. No model or game is used.

| Run | Between-sample change | All recorded damage events | Intersecting root events | Actual input |
|---|---|---:|---:|---|
| r01 | none | 0 | 0 | completed; press/release received |
| r02 | target draw at patch | 6 | 3 | withheld |
| r03 | overlay at patch | 7 | 4 | withheld |
| r04 | target draw far outside patch | 4 | 0 | completed; press/release received |

A separate direct X11 witness captured the colored change in r02–r04; later sampled center patches were identical to the source in every run. The distant case restores only the changed distant 8x8 region, rather than repainting the full target as in the prior whole-drawable probe. Thus this is a new four-arm controlled comparison, not a paired replay of p04. It demonstrates that this spatial rule can avoid that synthetic over-refusal while catching the two selected transient changes in this environment. Damage rectangles are server-reported redraw regions, not semantic labels; an outside change can matter to an action, and an intersecting redraw can be irrelevant. No general statement about correctness or task effect follows.

All four cases were frozen together, run once in fixed order, and retained. These few cases do not establish reliability, cost, speedup, MAP01 behavior, or model operation. The event stream is drained before the decision, not fenced through key emission; events arriving later, loss/backlog, resize/move, coordinate transformations, compositor behavior, other rendering paths and failure recovery remain untested. The source and target must remain bound; the sampled test does not make screenshot and input atomic. Narrowing the rectangle can miss relevant changes elsewhere.

Each network-none WSLc container used private Xvfb, one CPU and 1 GiB, image `sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25`, and the read-only Python runtime subset checked in the earlier MAP01 fixed-patch probe; intervening main changes were research only. The four named containers exited and were removed. Both dispatched actions recorded verified neutral releases and corresponding target press/release; all four F keymap readbacks were up. The witness, event reader and target event queue are different X11 observations within the same process/server, not external sensors.

The ZIPs retain runner, fixed conditions, images, observation and input receipts, event records and logs. `python audit.py` (Pillow, normal Python mode) independently recomputes screenshot hashes, pixel differences, root-rectangle intersection, decisions, target events and release. The most useful next boundary is a controlled change after the final event drain and before input, including whether an enforceable action-boundary fence is possible; the present result must not be integrated as a general guard.
