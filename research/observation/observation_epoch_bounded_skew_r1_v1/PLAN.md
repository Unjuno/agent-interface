# Observation Epoch bounded-skew R1

Parent #42; predecessor #1218 strict-join PASS.

## Analytical result

A small timestamp gap is not sufficient to compose consequential evidence. A critical field can be sampled immediately before a state mutation while a newer noncritical field is sampled immediately after it. The timestamps can remain within the skew budget although the critical fact is no longer valid.

The candidate therefore anchors composition at the newest sample completion. All fields must share session, surface and currentness generation. Critical fields must remain explicitly valid through the anchor. Noncritical fields may be older than the anchor only within the frozen skew budget. Missing, malformed or future evidence fails closed.

This rule is narrower than semantic readiness: temporally joinable evidence can still be semantically wrong.

## H/T/D/C/U

H: anchor-validity composition admits useful staggered noncritical evidence that strict exact-anchor joining rejects while preventing stale critical joins admitted by a naive timestamp-skew rule.

T: four-field stdlib model: critical focus/target binding, noncritical image/UI context, skew budget 2 abstract ticks. Candidate vs independent oracle; naive-skew negative discriminator; strict comparator. Construction then one 300,000-row frozen formal corpus.

D: candidate/oracle mismatch0; stale-critical/cross-identity/malformed joins0; strict-rejected valid candidate joins >=50,000; naive stale-critical joins >0; source/audit integrity PASS; formal1/reruns0.

C: critical classification and the two-tick budget are scoped assumptions. Production may use validity intervals or revalidation receipts. Real capture intervals and clock uncertainty remain transfer questions.

U: semantics only. No GUI/model/token/latency/task-success/human-tempo claim.
