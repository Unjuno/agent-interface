# Issue #7825 A01 evidence rescue on current main

## H — Hypothesis

The finite synthetic result is useful as a bounded negative comparison: in this fixture, forward key evolution showed no distinct historical-forgery advantage over independently rotated keys, while the separate latest-head checkpoint detected the tested suffix/fork/prefix rollback cases. A valid signature still did not establish a false claim's truth.

## T — Local preservation checks

- Preserved the original frozen package unchanged on current main `1eac6ea9f5b91cc10a8c3dc20374b9d79ffcf179`.
- Package manifest: 42/42 files verified; frozen-input manifest: 34/34 verified.
- Construction-only tests: `python3.12 -m unittest -v construction_tests` — 4/4 passed.
- Did not rerun the frozen formal candidate or independent formal auditor. `SOURCE_PLAN.md` prohibits retries; this PR preserves the original one-shot result and raw outputs.

## D — Data and scope

The retained one-shot WSLc result is a four-period synthetic SHA-256/Lamport fixture, not production cryptography. The environment record says swap/cgroup memory-limit enforcement was unavailable; the requested 512 MiB limit is not claimed as effective. No physical secure erasure, trusted witness honesty/time, runtime/GUI, model, input, effect, safety, or deployment result is established.

## C — Conclusion

Preserve as a method-scoped archival result: no distinct historical-forgery advantage over rotating keys on this fixture; checkpointed latest-head validation rejects only the registered rollback/fork cases. This is not a scheme-level FSS security claim. Draft pending independent review.

## U — Remaining uncertainty

The finite fixture, synthetic attack seeds, and witness assumptions do not generalize to production. Resource enforcement is unverified. No predecessor branch or cryptographic implementation is promoted by this evidence-only rescue.
