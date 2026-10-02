# T0 result — Successor Issue #6437

## Disposition

`PASS_METHOD_SCOPED`: 32/32 unique policy-vignette rows matched the independently recomputed result. The result supports only deterministic typed response normalization over this frozen synthetic fixture. It does not compare policy utility or establish any human, product, privacy, safety, or production benefit.

## H / T / D / C / U

- **H:** Typed normalization can preserve valid generic answers as scoped append-only clauses while rejecting ineligible evidence and never granting dispatch authority.
- **T:** Eight vignettes × four policies; exact independent reconstruction, source preservation, eligibility/revision/privacy checks, and seven corruption rejections.
- **D:** All gates passed: 32/32 exact, 32 unique keys, source clauses unchanged, append-only revision/provenance, no authority, no private payload disclosure, 7/7 corruption controls rejected.
- **C:** Fixture semantics are stipulated; a source-only conservative default may make normalization unnecessary; correct normalization cannot repair biased or absent answers.
- **U:** No human or model; no evidence of recall, preference fidelity, hidden-constraint discovery, interruption cost, task benefit, consent, safety, runtime, or production suitability.

## Formal run

- Candidate invocation: once. Independent auditor invocation: once; raw fixture, oracle, and candidate output only. No formal reruns.
- Runtime: OrbStack Docker, `python:3.12-slim`, image ID `sha256:f77ac9e44ae96ef2f90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, network disabled, 1 CPU, 256 MiB, 64 PIDs, read-only root, no capabilities, no-new-privileges.
- Counts: `APPENDED_FORBID=3`, `APPENDED_ALLOW_SCOPED=3`, `CONFLICT=3`, `UNKNOWN=12`, `NOT_ASKED=11`.
- Construction gate: PASS; seven planted corruptions independently returned `FAIL_METHOD`. Construction is distinct from the formal result.
- Issue body frozen SHA-256: `af6f1caed29b8e432f16a0b80d4ac2522b3f70338a7a21e86b628fbd258d5d6d`.
- Formal outputs, timestamps, runtime identity, and checksums: `run/`.
- Predecessor #6380 remains an unmodified failed allocation; this is its separately preregistered successor.

## Reproduction

From repository root run `sh research/analysis/constraint_response_normalization_6437_t0_v1/RUN.sh`. The runner verifies the pinned local image ID and makes exactly one candidate and one auditor invocation. It writes evidence under `run/`.
