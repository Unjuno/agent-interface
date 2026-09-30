# Cleanup-receipt follow-up to #4534

Issue: #4926
Allocation: `temporal-resume-control-map-cleanup-20260928-01`

## Question and preservation

This is a new copied-evidence verifier allocation, not a temporal-scientific rerun. Preserve #4447, #4511, and #4534 source, raw output, hashes, and HOLD decisions unchanged. The prior #4534 run rejected all eleven mutated copies and accepted the unchanged copy, but sampled `positive_control.copy_removed` while its `TemporaryDirectory` still existed.

## H/T/D/C/U

**H — hypothesis.** Recording temporary-copy existence immediately before and after leaving its context will yield a truthful cleanup receipt (`true` then `false`) for each of eleven mutated evidence copies and the unchanged positive control, without changing the frozen #4511 verifier's decisions.

**T — treatment.** Use the exact #4534 runner only as a frozen mutation helper and the exact #4511 `verify_receipts.py` as the verifier. Run baseline once; then ten original #4447 corruptions, the added comparator return-code corruption, and one unchanged acceptance control, each on a fresh disposable copy. Observe copy existence inside and after `TemporaryDirectory`. Use the exact cached Python image recorded by #4534, local OrbStack, `--pull=never`, `--platform linux/amd64`, `--network none`, read-only root/source/evidence mounts, bounded writable output and `/tmp`. A separately invoked raw-only auditor recomputes decisions, counts, case-48 identity, source/evidence tree hashes, and cleanup receipts.

**D — decision.** PASS only if the baseline reports 54 rows, 48 candidate matches, 40 comparator disagreements, six corruption refusals and no errors; all eleven mutated copies are byte-changing and rejected; case 48 is correctly targeted; the unchanged positive control is accepted and unchanged; each disposable tree exists before scope exit and is absent afterward; original source/evidence hashes match before and after; and the independent audit has no errors and rejects all frozen corruption probes. Otherwise retain typed HOLD/FAIL/STOP. No retry or tuning.

**C — controls.** Deterministic same-author offline copied-evidence audit. No temporal case is executed. Mutations are targeted verifier robustness probes, not independent review or prevalence estimates.

**U — limits.** Cannot upgrade prior HOLDs, establish predecessor fixture identity or Docker kernel equivalence, or claim runtime, production, durability, or performance behavior.

## Exact inputs

- Current main at intake: `519f2c1bdb219697c2f5e92ae6c27714265d60e0`.
- #4447 immutable evidence manifest: `1584edb3a45202b3e816d2a9735708265dae279fd4e18d8680fded7756cc3855`.
- #4447 BATCH5: `14e38390c6c18547d6d5e6fcc62e1dc0827a57ca9d196a88f9d6fa32817e699e`.
- #4511 verifier SHA-256: `a5fa59f118c46d2c01b555b32dbc3af57d80b2e0df1eea55961ef5ad994faac2`.
- #4534 frozen mutation-helper SHA-256: `080233cbaa90156de1da948591e2c2b57b6b8ee9444eddab3229773d4fb15c46`.
- Container image ID: `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419` (linux/amd64 as recorded by #4534; exact image selected by ID, no pull).

## Execution order

Freeze source and gates, publish and verify their exact GitHub blobs, and record preflight. Run synthetic-only contract tests in the pinned container. Then invoke the copied-evidence runner once in a fresh output directory, followed by exactly one independent raw-only audit invocation over retained output. Retain full stdout/stderr/exit receipts and hashes. Any failure is a STOP/HOLD; no same-allocation retry.
