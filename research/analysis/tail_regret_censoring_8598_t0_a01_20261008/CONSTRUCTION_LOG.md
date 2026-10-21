# Construction log — Issue #8598 T0 A01

All entries precede formal candidate/auditor execution unless explicitly stated.

1. Main and the Issue lineage were checked on 2026-10-08. Research branch is isolated from the WSLc shared lane. Issue #8598 explicitly authorizes only deterministic offline CPU method work and prohibits Docker/WSLc/live allocation.
2. Candidate, auditor and deterministic fixture builder were developed with tests-first construction. Earlier expected RED states (missing candidate, absent SHA binding, missing independent audit reconstruction, mutation acceptance) were retained in turn logs; they are not formal-study outcomes.
3. The preregistered recorded-covariate ranking gate was evaluated against the fixed deterministic cohort generator as a feasibility/construction check before any candidate CLI run. Strict correct tail ranking was 10/128 for IPCW and 20/128 for resolved-only. An initial ≥80% plus ≥10 percentage-point gate was amended pre-formal to retain ≥80% and require strict paired improvement. The amended rule also fails feasibility; it is not loosened further. This motivates an expected formal `FAIL_METHOD`.
4. The first and only successful fixture-generation command wrote both exact JSON inputs (public 5,257,788 bytes; truth 5,607,676 bytes; 768 cohorts, 24,576 opportunities). A deliberate second attempt to regenerate the same immutable paths returned `FileExistsError` before overwrite, confirming exclusive-create custody. This expected no-clobber event is recorded; no input bytes changed and no candidate/auditor ran.
5. Construction suite: 18 tests pass under CPython 3.12.10, both normal and `-O`. It includes independent expected-shortfall reconstruction, denominator/prefix checks, output/hash mutations, required categorical-control rejection, fixture determinism/separation, positivity behavior, and the full-fixture feasibility counts.
6. Formal execution order after the freeze commit is one candidate CLI invocation with only `inputs/public_input.json`, then one auditor CLI invocation with public, hidden truth and candidate output. Outputs are exclusive-create and must not preexist. No retry or post-freeze source/fixture edit is allowed.

The feasibility exploration did not execute the frozen candidate CLI or formal auditor CLI and therefore is not counted as either allocation.
