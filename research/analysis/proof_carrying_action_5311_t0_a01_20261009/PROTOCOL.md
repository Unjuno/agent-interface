# Issue #5311 T0 A01 protocol

Allocation: `5311-T0-A01-20261009`. Current-main anchor: `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.

## H/T/D/C/U

**H.** On this finite corpus, a producer-supplied certificate checked by a small admission routine can lower deterministic checker operations relative to reconstructing the same five policy predicates from the full plan, while producing the same admission decisions and effect labels.

**T.** The corpus contains 8 valid two-step plans and 7 directed negative plans: missing required predicate, wrong target, stale epoch, widened footprint, expired lease, unsupported predicate, and plan/certificate mismatch. Run the same corpus through `FULL_RECONSTRUCTION`, `CERTIFICATE_CHECK`, and `NO_CERTIFICATE_FAIL_CLOSED`. A separate raw-only auditor recomputes decisions and effect labels from the JSON input and candidate output. Cost is the number of explicit primitive policy-field inspections in the checker; it excludes serialization, hashing, proof production, and downstream effect verification. The protocol makes no elapsed-time claim.

**D.** PASS_METHOD_SCOPED requires all 8 valid plans accepted by both gates, all 7 invalid certificates rejected by certificate admission, zero unsafe admissions, identical effect labels on the 8 valid plans, and strictly fewer counted checker inspections in certificate mode. Certificate-only mutations may be accepted by full reconstruction because that arm reconstructs the plan and does not rely on the malformed certificate; those decisions are reported separately. Any unsafe certificate acceptance or changed valid-plan effect is FAIL_METHOD. A cost tie/regression or incomplete corpus result is UNCERTAIN.

**C.** A certificate may add work elsewhere; full reconstruction may already be cheap; the finite policy language may not capture real plans.

**U.** This does not establish proof soundness generally, cryptographic binding, atomic check-to-dispatch, live evidence freshness, GUI effects, release, safety, latency, or product value.

## Corpus and interpretation

Each plan has two actions sharing an explicit target and epoch, bounded footprint, unexpired lease, release obligation, and an independently specified post-action effect label. The certificate supplies those policy facts and binds them to the canonical plan digest. Certificate admission checks the digest and the compact claims; full reconstruction inspects every action against each required predicate. This deliberately narrow comparison tests only whether common repeated predicates can be checked once when the cert claims a shared invariant. It does not model a real proof calculus. If the two-step corpus cannot justify that optimization without trusting assertions beyond the canonical binding, the auditor should reject it and the result is not a pass.

## Execution contract

Construction tests may run before freeze. The formal candidate and independent auditor may each run once after the freeze commit, on host CPython 3.14.5 arm64 macOS; no container isolation is claimed. Preserve stdout, stderr, exit codes, and raw outputs. No retries, edits, or successor execution under this allocation. The local Docker content store returned `operation not supported`; container execution is therefore unavailable. This Issue requests only standard-library offline work and does not itself require a container.
