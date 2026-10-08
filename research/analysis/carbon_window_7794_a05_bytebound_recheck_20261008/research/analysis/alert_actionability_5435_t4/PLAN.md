# T4 preregistered plan — Issue #5435 alert batching under capacity

## H/T/D/C/U

- **H:** A conservative identity-bound duplicate batcher can lower non-actionable notification burden under a finite deterministic responder capacity without increasing unique actionable misses or hard-alert response latency, even when an unrelated low-severity actionable event is mis-scored under a held-out shift.
- **T:** One deterministic full-factorial run: 3 arrival patterns (same-tick burst, paired waves, spaced), 2 responder capacities (1 or 2 notifications/tick), 2 response deadlines (1 or 3 ticks), and 2 score conditions (calibration-like vs shifted) = 24 streams × 5 policies = 120 policy-stream traces. Ten fixed alert deliveries per stream include true duplicate event identities, a distinct actionable alert sharing a text signature with a benign warning, a low-severity UNKNOWN score, hard safety alerts, and one unique low-severity action whose score shifts from 0.8 to 0.05. Policies: emit-all, severity-only, probability-threshold suppression, signature-based batching, and identity-bound conservative batching. Exact deterministic FIFO-with-severity/deadline priority; no RNG, external services, model/GPU, retries, or tuning.
- **D:** The identity-bound policy passes this finite model only if (1) hard alerts are never suppressed; (2) unique actionable misses are no greater than emit-all in every stream; (3) its maximum hard-alert response latency is no greater than emit-all in every stream; and (4) it reduces published non-actionable alert deliveries by at least 10% in aggregate. Otherwise FAIL. Any PASS remains model-scoped and does not establish human/model fatigue or production safety.
- **C:** Emit-all may remain preferable when capacity is adequate; severity-only may be lower burden but miss low-severity actions; signature batching can conflate distinct causes; probability-only thresholds can suppress shifted low-severity actions. Stable event identity and raw evidence retention—not a calibrated score alone—may be the operative mechanism.
- **U:** Alerts, truth, scores, priorities, arrival patterns, deadlines, and one-responder service behavior are authored. No humans, adaptive fatigue, model-context behavior, calibrated population, adversarial alert stream, or live verifier integration are present. Score shift is a fixed counterexample, not a distribution estimate.

## Frozen policy semantics

- **EMIT_ALL:** publish every alert.
- **SEVERITY_ONLY:** publish only severity ≥ 2.
- **PROBABILITY_THRESHOLD:** suppress any low-severity alert with known actionability score ≤ 0.1; hard alerts bypass suppression.
- **SIGNATURE_BATCH:** for low-severity alerts with score ≤ 0.1, suppress if an earlier published alert has the same text signature, regardless of incident identity; hard alerts bypass suppression.
- **SAFE_IDENTITY_BATCH:** for low-severity alerts with score ≤ 0.1, suppress only if the exact incident identity was already published; preserve UNKNOWN scores, first alerts, and every hard alert. Retain the raw event regardless of publication.

One formal candidate invocation after preregistration. Construction checks use one hand-authored stream only and do not execute the 24-stream factorial. Preserve raw trace, independent replay audit, and mutation controls unchanged.
