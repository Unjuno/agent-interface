# Issue #8502 T0 A02 — independent audit of retained A01 bytes

A02 is a distinct successor audit-only allocation over saved A01 bytes. A01 remains unchanged and remains recorded as `FAIL_METHOD`: its auditor compared each group's largest cumulative proportion instead of computing the largest between-group cumulative difference, so it incorrectly rejected F02. A02 does not rerun or patch A01's candidate, auditor, fixture, truth, or result; its actual disposition is the `decision` field in this package's `AUDIT.json`.

## H / T / D / C / U

- **H:** A fresh raw-only auditor can identify A01's specific estimator defect, independently reconstruct the five frozen candidate labels/localizations from immutable bytes, and reject semantic tampering without rerunning either A01 program.
- **T:** Read A01 `FREEZE.json`, `fixtures.json`, `truth.json`, `candidate.json`, and failed `AUDIT.json`; verify the frozen source/input digests and exact A01 failure signature. A02 independently recomputes cumulative-category differences from category-count tables and ordinal-score associations from raw integer moments, then compares all five decisions/localizations against a truth map embedded in the new auditor. Run five in-memory mutations (wrong class, dropped result, wrong threshold item, wrong sparse decision, and malformed association edge) plus a changed-input-byte integrity control.
- **D:** `PASS_AUDIT_ONLY_SCOPED` only when all A01 identities/failure evidence match, all five baseline results reconstruct, each semantic mutation is rejected, and changed input bytes fail identity validation. Otherwise `FAIL_AUDIT_ONLY`.
- **C:** The A02 truth map remains hand-authored for a narrow synthetic fixture family; candidate and auditor share the declared practical margins, though not implementation code. This verifies one finite screening instrument and the A01 audit defect, not a general psychometric estimator.
- **U:** No human data, latent-mean comparison, ordinal CFA/IRT, workload construct validation, participant/accessibility inference, or production decision. `COMPATIBLE_SCREEN` is not scalar invariance evidence.

## Reproduction

From the repository root, run once:

```powershell
python research/analysis/measurement_invariance_8502_t0_a02_20261008/auditor.py --a01-dir research/analysis/measurement_invariance_8502_t0_a01_20261008
```

The command is read-only with respect to A01 and creates only this directory's `AUDIT.json` using exclusive creation. No candidate, model, container, GUI, or participant-data invocation occurs in A02.
