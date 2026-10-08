# #1204 fresh-X11 reversal invalidation latency

Scientific contract is frozen in Issue #1204.

H: once a future reversal becomes visible in fresh pixels, a deterministic adjacent-centroid direction guard can invalidate a stale velocity-based speculative continuation earlier than the same 200 ms TTL, without false invalidation on continuation controls.

T: private Xvfb/Tk 320x240, 20 Hz full-frame captures. Reversal cases: initial direction +/-1 x offsets {5,15,25,35,45} ms x2 repetitions =20. Continuation controls=10. Guard uses only capture_finished_ns + red_centroid_x; fixture reversal timestamp is scorer-only. Formal one invocation, reruns/replacements/tuning0.

D: 20/20 reversals detected before TTL; continuation false invalidation0/10; capture exceptions0; reversal->YIELD p95<=110 ms and max<=140 ms; paired median stale-exposure reduction vs TTL_ONLY>=75 ms; authority/input0; integrity pass.

C: 20 Hz information arrival can dominate and scheduler jitter can widen tails.

U: private-X11 moving rectangle only; no task/model/MAP01/production claim.

Construction-only correction: initial implementation computed score_start before Tk startup, allowing score_start/reversal target to pass before fixture readiness. Repaired by ready-first control-file handoff; scientific timing/gates unchanged. Corrected excluded construction: one reversal detected at 83.728218 ms with 89.590637 ms stale-exposure reduction; one continuation control false invalidation0.
