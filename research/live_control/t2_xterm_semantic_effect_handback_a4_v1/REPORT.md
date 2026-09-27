# XTerm semantic-effect handback A4

Issue #1553. Fresh instrumentation-only successor to #1548.

## Construction

`PASS_CONSTRUCTION_ELIGIBLE`: four excluded rows passed exact PTY input, top-level focus, helper/XTerm exit0, terminal QueryKeymap x-UP4/4, positive receipt3/3, NO_EFFECT timeout, and admission press before declared frontier4/4.

## Formal execution

Immutable batches0–2 completed once with all rows terminal x-UP, exact input/focus/exit0, and admission-before-frontier.

Batch3 (offset39 ms) completed once, but one baseline delay10 row had actual XTEST press at **40.211092 ms** from t0, after the declared frontier return at40 ms. The other seven batch3 rows pressed before frontier.

Per stop rule, batch4 NO_EFFECT was not executed. No aggregate scientific result is formed and no A4 row is pooled.

Disposition: `STOPPED_BATCH_TIMING_VIOLATION`; scientific disposition `NONE`; batch reruns0.

The terminal-key evidence repair itself worked: every executed formal row ended QueryKeymap x-UP. A successor may change only the pre-frontier scheduling mechanism so actual press time, not requested wake target, satisfies the frozen offsets. Semantic delays/deadlines/corpus/gates must remain unchanged.
