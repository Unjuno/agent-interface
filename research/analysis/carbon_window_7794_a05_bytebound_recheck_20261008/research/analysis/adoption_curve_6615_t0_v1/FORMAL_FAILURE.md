# Formal failure — Issue #6615 T0

Allocation: `ADOPTION-INCLUSIVE-CURVE-6615-T0-20261002-01`  
Frozen base: `afea9a530cafd7af529df4c9e59f36b816bca24f`  
Environment: host-local CPython 3.14.5 on macOS (WSLc unavailable; OrbStack daemon read probe unresponsive).

## Observed execution

- Frozen candidate invoked once; exit 0; emitted 58 event rows.
- Frozen independent auditor invoked once; exit 0; reconstructed 58/58 rows and returned `errors: []`.
- The audit reported `unsupported_host` as comparable at prefix 0 and assigned `first_comparable_wall_break_even_prefix: 0`.
- At prefix 0 neither route has delivered any verified task; the unsupported host is explicitly outside the supportable domain. Treating this vacuous empty prefix as a break-even violates the preregistered rule that unsupported routes are never eligible for a quality-preserving comparison.

## Decision

`FAIL_METHOD_GATE` despite process exit 0 and structural reconstruction success. The frozen auditor's comparison eligibility predicate omitted the host-support gate. This is a semantic audit defect, not evidence for or against actual adoption economics. Preserve all source, freeze, stdout/stderr, raw data, and audit output unchanged. Corrected logic must use a new successor allocation/path and independently rerun the complete frozen protocol; do not overwrite this record.

## Narrow supported synthetic observations (not a pass)

- On the stipulated learning fixture, guarded setup + tasks cost 95 wall seconds versus 100 direct by prefix 5, with identical five verified task IDs; at prefix 4 guarded costs 95 versus 80.
- Setup-dominates fixture has no wall break-even through K=5 (guarded 170 versus direct 100 at K=5).
- The structurally reconstructed ledger contains one supported-route setup failure, one wrong/unverified task attempt, one route-ineligible task and zero unsupported-host successes.

These are deterministic fixture values only. They establish no operator effort, real setup burden, adoption, efficacy, or product claim.

## Artifacts

- Candidate stdout: `candidate.stdout`; stderr: `candidate.stderr`; exit 0.
- Raw event ledger: `raw.json`.
- Auditor stdout and preserved copy: `auditor.stdout`, `audit.json`; stderr: `auditor.stderr`; exit 0.
- Frozen hashes: `FREEZE.json`.
