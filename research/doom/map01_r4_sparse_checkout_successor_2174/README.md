# MAP01 r4 sparse-checkout successor

Successor Issue: #2174. This branch preserves r4 STOPs and changes only the
checkout strategy: shallow, blobless, sparse paths, bounded job duration.

The gate is source-only and has no construction/formal/GUI/input/model claim.
A workflow PASS means only that the gate was reached and emitted a result.
