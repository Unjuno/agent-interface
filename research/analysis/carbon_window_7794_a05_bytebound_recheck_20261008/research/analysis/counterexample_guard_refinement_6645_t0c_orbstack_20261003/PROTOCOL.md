# Issue #6645 T0-C preregistration

Allocation `CGREF-6645-T0C-ORB-20261003-03` is a fresh formal allocation. A01
stopped in construction; A02 passed construction but its typed `docker create`
command failed before container creation. Neither predecessor invoked a formal
candidate or auditor. This allocation uses their frozen A02 candidate, fixture,
and independent auditor byte-for-byte, through allocation-binding wrappers
frozen here; no scientific gate, case, outcome, or source algorithm changes.

## H / T / D / C / U

**H.** On the ten-state authored fixture, only a replay-authenticated real guard
miss yields a refinement. Preserving all equally minimal refinements should
refuse the three held-out harmful families, retain the ordinary valid control,
invalidate both siblings depending on the changed predicate set, and fail closed
on unmodeled, ambiguous, corrupt, and no-fallback cases.

**T.** Run the 13-case construction suite result already obtained against the
exact SHA-bound A02 source as the construction gate (13/13, Python 3.12.14).
Preflight the exact image reference by `docker image inspect` and verify it
matches the frozen digest before creating either formal container. Run one
candidate and one independent raw-only auditor in separate network-disabled
containers. Candidate/auditor files are read-only; only their unique output
mounts are writable. Preserve all ten rows, audit, container inspection,
stdout/stderr, statuses, and hashes. No rerun, tuning, or overwrite.

**D.** `PASS_METHOD_SCOPED` only if independent audit returns PASS with zero
errors, zero candidate false admissions, all three held-out harms refused,
`valid_common` admitted, `valid_rare_alias` and its observationally identical
harmful counterpart both UNKNOWN, out-of-envelope/no-fallback cases STOP,
siblings A/B invalidated while C remains valid, and no task input replay or new
authority. Any audit mismatch or false admission is FAIL; inability to verify
frozen inputs/image is STOP before candidate execution.

**C.** Conservative invalidation may be simpler; a finite authored vocabulary
can overfit; ambiguous valid/harmful states necessarily lose availability.
**U.** Synthetic method result only: no real skill/cache, GUI, model, user data,
live input, external effects, latency benefit, production safety, or
generalization beyond this finite coverage envelope.
