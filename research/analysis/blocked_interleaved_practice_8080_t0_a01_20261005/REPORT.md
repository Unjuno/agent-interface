# Issue #8080 T0 A01 report

## Result

**`METHOD_PASS_SCOPED` for the deterministic synthetic schedule and reversible
effect-oracle contract.** This is a method-readiness result only. It contains no
participant, GUI, model, delayed-retention, or transfer outcome. The Issue #8080
human-study gates remain in force.

The frozen candidate generated two 12-slot schedules over three procedures at
four attempts each. The blocked order grouped each procedure; the interleaved
order cycled through all three procedures four times. Materials and one feedback
event per attempt were identical. The independent auditor verified all 24
forward effects, all 24 inverse effects, and all 24 restorations to initial
state across the two arms. It found no held-out labels in the schedules and
classified the four scorer controls as valid exact effect, wrong target,
false-success, and unknown outside-family.

Five adversarial mutations were rejected: held-out leakage, an omitted attempt,
a duplicated variant attempt, a false forward effect, and a failed inverse.
The exact deterministic candidate output was reconstructed from the frozen
design.

## Provenance

- Allocation: `BLOCKED-INTERLEAVED-PRACTICE-8080-T0-A01-20261005-01`
- Base main: `1fa854d537bfd711b5dfd99f8c04ab6c35bad286`
- Frozen source commit: `80279fb1b157133a1824d2d0b99d3ab6570c3283`
- Run: `2026-10-05T08:11:46.751570Z`–`2026-10-05T08:11:46.941140Z`
- Host: macOS 27.0.1, arm64, Python 3.14.5
- Candidate input: `design.json` only; held-out IDs and truth are in
  auditor-only `scorer_fixture.json`
- Raw SHA-256:
  `5783e26d7bcd4472405fbdb3960c4c3e54d581719abd37f8afbec5dc82fb3fc6`
- Audit SHA-256:
  `26150a5c6c90b6b158ed3d4aa16b83679c026d1b4bd65c4d65ebaea9838eec72`

Exact commands, exit codes, durations, and all input/output hashes are in
`results/a01/run_metadata.json`. The pre-freeze construction evidence and its
earlier timestamps limitation are retained separately under
`results/construction/a01/`.

At selection, the latest direct Issue #8080 read in the preceding work segment
showed it open with no comments; the merged #8084 A02 report on current main
also says the #8080 baseline remains untouched. A final live Issue/PR status
refresh at 08:01 UTC could not complete because GitHub REST returned the
authenticated user's API rate-limit 403. No Issue comment, push, or PR write
was attempted; current owner and PR state therefore remain unverified here.

## Limits and next gate

The schedule comparison demonstrates that the two practice orders can be
constructed with equal synthetic exposure. It does not show that interleaving
improves or harms learning. Spacing and switching costs remain bundled with
order. No human study, live personal workspace, or consequential action was
used. A future T1 needs separate consent/privacy/ethics review, preregistration,
and fresh coordination with the active owners of #8080 and #8084.

This frozen method check ran directly on the host because the tested property
is a finite pure-Python contract and has no OS or GUI residual. It makes no
OrbStack/container reproducibility claim.
