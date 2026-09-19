# Issue #3300 — live scorer coherence

Additive successor to the ideal-phase scorer evidence. This path does not
rewrite or promote the retained results under #944/#1461.

`RAW.jsonl` must retain one row per scheduled scorer period. Every accepted
row binds the source observation sequence, capture and typed-ready timestamps,
frame digest, epoch, scheduled/start/finish timestamps, and missed-period
accounting. A delayed or stale row is rejected before any input authority.

Formal execution requires Docker `--network none`, a pinned image/source
manifest, raw stdout/stderr, and an independent audit that recomputes schedule
advancement. A PASS is limited to the fixture and allocation; it is not a
MAP01 efficacy, human-tempo, or production claim.
