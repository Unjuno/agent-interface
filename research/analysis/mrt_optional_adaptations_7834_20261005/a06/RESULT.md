# A06 — PASS_METHOD_SCOPED_A06

Allocation MRT-7834-A06-20261005; prospective freeze #5986671820; previous A05 FAIL_METHOD is preserved at #5986643544 and A06 is a fresh allocation, not a retry.

Candidate and independent auditor each executed exactly once in separate WSLc 3.0.1.0 containers from pinned Node v22.23.3 image node@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402. Both exited 0, with pull never, network none, CPU 1, source/input read-only, separate output mounts, zero retries. No container remained running afterward.

The candidate emitted exactly four assignment-support rows. The independent auditor reconstructed them from the frozen fixture and direct potential-outcome differences: M0=+2, M1=-1, equal-stratum pooled effect=+0.5, heterogeneity M0−M1=+3. All three frozen support/timing controls returned NONIDENTIFIABLE, and all 7/7 raw-row mutations were rejected, including an unexpected extra property. D gate passed within 1e-12.

This is finite synthetic method evidence only. The fixture has two fixed moderator strata, known assignment probabilities and complete deterministic outcomes. It does not establish moderator discovery, finite-sample accuracy, a real-user or application effect, treatment recommendation, or product benefit. GPU use is irrelevant to this four-row enumeration and was not attempted.
