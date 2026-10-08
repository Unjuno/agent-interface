# Task-conditioned GUI memory retrieval T0 — host A05

A05 is a fresh allocation after A04's immutable pre-candidate stale-main STOP.
A03's formal FAIL_METHOD and A04's STOP are both preserved unchanged. This
allocation tests the same 72-case contract as A04 with an effective-mutation
auditor that proves each corruption changes raw rows before testing rejection.

Candidate reads only `fixture.json`; `oracle.json` is scorer-only. PASS is
limited to the authored method fixture and six mutation controls. No model,
GUI, natural retrieval, cost, task effect, latency, runtime or product result is
claimed. Host-only; the OrbStack content-store failure on #7383 is not retried.
