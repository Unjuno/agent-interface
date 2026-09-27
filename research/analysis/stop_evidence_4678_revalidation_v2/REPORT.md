# Successor #4678 STOP evidence source/hash revalidation — #4795

Disposition: **PASS_SOURCE_BOUND_CHECKSUM_DISCREPANCY_REPRODUCED** (public snapshot only).

## H / T / D / C / U

**H.** The #4791 snapshot source contents match their recorded GitHub blob IDs; the seven SHA256SUMS mismatches reproduce; no raw checkpoint-cache inventory was retained.

**T.** One formal local Docker invocation ran the corrected stdlib-only auditor against the exact #4791 frozen bundle. Image `python:3.12-slim-bookworm`, ID `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, linux/amd64; network none, read-only root, 1 CPU, 512 MiB, 64 PIDs, all capabilities dropped, no-new-privileges. No GPU/model, install, provider, network or host-cache access. Formal invocations=1; no reruns/replacements/tuning.

**D.** All 8/8 frozen Git blob identities matched; all 7 published SHA256SUMS entries mismatched when recomputed from the corresponding frozen content; checkpoint absence had no retained raw inventory; the old #4678 auditor's assertion-only absence predicate returned true; mutation controls rejected 5/5. Container exit=0. Exact machine-readable output is `AUDIT_RESULT.json`.

This confirms a checksum-manifest discrepancy in the public evidence snapshot. It does **not** prove that checkpoint absence was false: the required raw host-cache inventory was never retained. It also does not establish tampering or misconduct. The previous #4791 formal HOLD and its defective verifier remain unmodified.

**C — controls.** Correct Git object hashing used `SHA-1("blob " + byte_length + NUL + bytes)`; source-integrity errors are evaluated before scientific decisions. Input is the #4791 bundle only. No private host paths are read.

**U — limits.** No claim about actual checkpoint presence/absence on the original PC, model quality, or guard effectiveness. Repairing the historical claim requires new contemporaneous raw inventory under a separately preregistered successor; this allocation is consumed.

## Provenance

Base main at intake: `5df0b2742c6d232529a50f5ca1a04724e1c32086`. The exact #4791 input bundle Git blob is `4e64d884466c28fc982b10256f6fa2bdb086498c`; the frozen corrected auditor is pinned in `FREEZE.json`. The source/bundle/output and this report are additive; #4678, #4791, PR #4781, and PR #4794 remain unchanged.
