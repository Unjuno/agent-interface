# Formal result — Issue #3166 gate-integrity rung 2

Allocation `issue3166-gate-integrity-rung2-20260927-01`; source main
`2c5be06f9563deb3e5e739df6e7f154d145a8687`; image
`agent-interface-2994:20260920`, ID
`sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c`
(linux/arm64). Exactly one formal container completed. Its exit code was 0; a
separate independent audit container exited 2 because its cleanup checks failed.

## Decision

- Observed safety finding: `FAIL_DUPLICATE_COMMIT_REPLAY_ACCEPTED`.
- Raw-audit disposition: `HOLD_RAW_AUDIT_ERRORS` (237/279 checks passed; 42
  cleanup checks failed).
- Overall allocation disposition: `HOLD_GATE_INTEGRITY_RUNG2` because the
  preregistered acceptance requires verified per-fixture cleanup and zero audit
  errors. Do not call this a clean overall PASS or a clean complete FAIL.
- Contradictory control: `HOLD_POSTCONDITION_CONTRADICTORY`.
- Issue #3166 remains OPEN.

The frozen auditor reports the duplicate witness as a FAIL finding and the
cleanup-integrity gate separately as HOLD. This report retains both dimensions;
the cleanup HOLD governs the overall evidence-completeness disposition.

## Measurements

The runner retained 43 action records: 40 GTK-backed matrix cells (10 contexts
× 4 policy comparators), two identical duplicate attempts, and one partial
effect control. The independent raw-only audit verified all matrix cells,
admissions, exact effects, release traces, source hashes, and the duplicate
program/receipt identity. Raw JSONL SHA-256:
`e6e0593f0b02b6d24a4a1a5da86c0c76d9380d60c1226fa8f8bafdbefdbdec95`.

| Comparator | Admitted of 10 | Invalid admissions with exact GTK effect |
|---|---:|---:|
| TWO_TIER_FRESH_GATE | 1 | 0 |
| DEPENDENCY_ONLY | 9 | 8 |
| GATE_ONLY | 2 | 1 |
| CACHED_PREPARE_GATE | 9 | 8 |

For the stale-dependency-version context, the GTK target remained live and the
gate receipt remained fresh: the two-tier policy refused while GATE_ONLY
admitted and saved. For each of the eight invalid gate contexts, the prepared
dependency remained current; DEPENDENCY_ONLY and CACHED_PREPARE_GATE admitted
and produced the exact save effect.

In the duplicate probe, both attempts were admitted with identical program ID,
intent ID, commit epoch, and receipt. Each native dispatch completed with four
emissions and verified input release; retained GTK events show one save after
attempt 1 and two after attempt 2. This is a direct fixture-bound duplicate
replay witness, not a claim about a general production commit-gate API.

The partial-control fixture wrote
`{"saved":true,"text":"","collateral":"fixture-label"}`. The runner
classified it as `HOLD_POSTCONDITION_CONTRADICTORY`; native completion did not
become exact task success.

## Audit HOLD and preserved limitation

All 42 GTK fixture processes (40 matrix cells, one duplicate-probe fixture, and
one contradictory-control fixture) recorded cleanup error
`FileNotFoundError(2, 'No such file or directory')` and fallback process exit
`-15`. The cleanup helper attempted `xdotool windowclose`, but the pinned image
does not contain `xdotool`. The Xvfb server was terminated when the formal
container ended, but that does not substitute for the preregistered per-fixture
cleanup gate. The independent audit therefore reported 42 cleanup errors and
`HOLD_RAW_AUDIT_ERRORS`; this was not repaired, retuned, or rerun after the
formal allocation.

A host-side Docker CLI mount spelling also failed before container creation
(exit 125; no evidence rows). It is separately preserved under
`results/launch-stop-20260927-01/`; the documented erratum only omits the
invalid bare `rw` token. A mount-only construction probe succeeded before the
single formal execution.

## Reproducibility and scope

Construction checks before formal: 21/21 unit tests passed in the pinned
OrbStack image; a separate GTK/X11 smoke sent Ctrl+S and observed exact
`{"saved":true,"text":""}`, native completion, and four emissions. These are
not formal rows. Formal/audit container inspect records, image metadata, raw
JSONL, per-case evidence, summary, and `AUDIT.json` are retained beside this
report; `SHA256SUMS` covers the published result bundle.

Policy comparators are fixture-bound models; there is no general runtime
commit-gate API. No model, IPC race, other desktop backend, cross-platform, or
production-safety claim is established. No formal rerun occurred. Preserve this
HOLD/FAIL evidence and the earlier rung1/#4506/#3185 artifacts unchanged.
