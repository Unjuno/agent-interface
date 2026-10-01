# A8 result — real X11 temporal-ring Rung1 integration

Decision: **PASS_X11_TEMPORAL_RING_RUNG1_INTEGRATION_SCOPED**

The source-frozen A7 160×120 ROI / 20 Hz / 500 ms ring was composed with the synthetic Rung1 historical-request mechanism. Six fresh counterbalanced matched pairs completed in one detached formal supervisor invocation; reruns/replacements/tuning were zero.

## Primary result
- ring: 24/24 historical requests, extra acquisition boundaries 0
- ring request→evidence p95: 17.76245 µs
- JIT live-only: 24/24 requests required one acquisition boundary
- JIT request→future-equivalent evidence median: 100.437535 ms
- paired median JIT-minus-ring: 100.43612225 ms
- future-equivalent evidence promoted as historical: 0
- authority grants: 0

## Capture integrity
Exact ROI [80,60,160,120], 76,800-byte normalized frames, zero capture exceptions. Ring capture p95 ranged 0.387–1.045 ms; JIT capture p95 ranged 0.333–0.555 ms. The 500 ms ring reached at most 11 frames. Maximum historical target error was 0.738 ms, below the frozen 35 ms bound.

## Scope
This demonstrates a real-X11 acquisition-boundary advantage for already-retained history on this declared live-only source. It does **not** show that a model needs temporal history, that the frames improve a decision, or that the result transfers to replay-capable backends or production compositors.

The exact first raw JSON is retained losslessly as FORMAL_RESULT.json.gz. Its uncompressed SHA-256 is e6a7536458c3cb6a665521775d45c994fc5b53b6b7a4f8d41e9e75ef4121e948.
