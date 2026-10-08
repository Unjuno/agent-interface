# #1074 Rung1 retained-data readiness audit

Decision: **`BLOCKED_DATA_TEMPORAL_SPECULATION_RUNG1`**.

This result does not weaken #1095's real-X11 temporal-ring latency PASS or #1074 Rung0's synthetic speculation PASS. It asks only whether already-retained #1095 evidence can score the next speculation question without replay/regeneration.

Pinned #1095 evidence identities: fixture `0843f29618b0aa9010b22789f56d248bbeb8f7a4`, runner `c495fad798cc325bd2321a097bd6a3acff081c15`, result summary `314e85e29c01d49b322a4a8f467dcd9b11602cab`, audit `7300abd31cff9061c61183830f8fc6159e5756db`, formal gzip `c36a8c46dfad5e8c1ed01ffd1a0d2864b6ab8bfc`.

The retained schema contains request/capture timestamps, selected capture timestamps, target error, distinct-frame flags, capture counts/latencies/payload types, ROI, geometry and frame byte **size**. The live capture object transiently held raw `data`, and the fixture internally tracked rectangle `x/dx`, but those are not persisted in the result schema.

Therefore the retained evidence does not directly preserve: frame content; frame digest; reproducible current-state identity; rectangle x/direction; content identity for historical frames; future state/frame label; reversal/invalidation label; or an independently scored future outcome. Treating the deterministic fixture source as a per-row label would regenerate/infer evidence that was not retained.

Under the frozen readiness gate, constructible same-current alias pairs from retained evidence = **0** and constructible opposite-history/future-disagreement pairs = **0**. Required gates are >=32 and >=16 respectively, with explicit fresh-current identity and an independently retained future label for every scored pair.

Minimum successor collection fields:
1. content-derived current frame digest/state projection;
2. content IDs/digests for retained history frames;
3. observable direction/temporal feature derived from retained frames;
4. future frame digest/state projection at a frozen horizon;
5. explicit reversal/invalidation marker or an independently derivable retained future transition;
6. per-row source/session/sequence timestamps binding history-current-future.

Independent audit passes with errors `[]`; six copied-result mutations that invent the missing evidence are rejected. No live/formal/X11/model/task-input action was allocated and no #1095 run was repeated.
