# Rescue qualification — Issue #5352 T15 preparation (2026-10-03)

This is a custody-only transfer from Draft PR #6753, source head
`592a830f8e2f576596489859b7b9b548d15830b8`. All six original package files
across the T0 construction and T15 preregistration directories are preserved
byte-for-byte. The stale source-branch README/index snapshot is not copied; the
current-main README is retained with one additive, scope-qualified status line.

## Verification performed

- The T15 finite construction-contract suite passes locally: 5/5 under
  CPython 3.12.13. It exercises in-memory candidate/auditor functions and
  mutation controls; the candidate and auditor CLIs were not invoked.
- Re-ran the repository's current analysis-index checker unit suite: 17/17
  pass under CPython 3.12.13; the checker validates 620 retained
  result/failure directories. The source branch's historical construction
  report separately records 6/6 index tests at that older revision. These
  are construction checks, not WSLc candidate/auditor results.
- The current analysis-index test workflow receives one additive T15 test
  command; no existing current-main test step is removed.
- The T0 package has `CONSTRUCTION_REPORT.md`, not `REPORT.md`,
  `FORMAL_FAILURE.md`, or `STOP.md`; it does not qualify for the generated
  retained-result index. The manual summary line is explicitly labeled
  preformal and makes no efficacy claim.

## Execution boundary and disposition

The preregistration requires an exact current-source/image/output freeze and an
explicit non-overlapping WSLc CPU assignment plus shared-runtime owner release.
The checked PR/coordination records do not provide that #5352-specific
assignment. No WSLc/container, candidate CLI, or auditor CLI ran during
recovery. Formal counts remain candidate=0, auditor=0, containers=0, retries=0.
No scientific effect, prevalence, GUI, human, or efficacy result is claimed.

Original #5352 T0 `FAIL_SAFETY_OR_REFERENCE_GATE` and PR #5376 remain unchanged.
This T15 five-row fixture is only a method-level discriminator; it neither
reclassifies the earlier 155 traces nor establishes real task equivalence.
Issue #5352 remains open. Any future formal run must satisfy the fresh source,
input, output, image, and explicit resource-owner gates in the preregistration.
