# Premeasurement freeze

Task RECEIVER-CONCURRENT-CONFLICT-20260916-001, Issue #359. Immutable base `0a6012d189d2b4228d6f01462efc257e8d5e29dd`. No formal case has run at publication.

The merged #337 receiver bytes are unchanged (Git blob `e4f0ef388b2a36dd74f6035ab68517be8a371b66`). Worker barrier mechanics are unchanged from #345. This rung changes one semantic factor only: the two simultaneous requests have the same scope/command/context/generation but distinct deltas 3 and 4, therefore distinct fingerprints.

Construction: four excluded joint-cell cases; independent audit PASS 4/4; seven guaranteed non-no-op corruptions rejected. Construction ledger SHA-256 `2300397fabf82dc9d3365b30fd6cdf0771bc14741c9883e42473216144a502f2`.

Formal: 32 fresh f001..f032 cases; 8 per launch-order × a_delta joint cell, fixed shuffle seed 35920260916. Four sequential 8-case outer chunks are supervision only. Exact source/schedule/chunk hashes are in prereg.json. First outcomes only; no retry/replacement/extension/tuning.

PASS requires one APPLIED/new-effect winner and one CONFLICT loser in every case, a single durable effect/decision bound to winner fingerprint/delta, overlapping calls before first commit, deterministic winner/loser replay semantics, DB/process/source/audit integrity.
