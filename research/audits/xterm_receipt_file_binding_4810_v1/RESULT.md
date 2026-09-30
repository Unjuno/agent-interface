# Issue #4810 — local result

## Disposition

`HOLD_PARTIAL_GAP`. The unchanged frozen auditor accepted the baseline and
accepted two missing-receipt copies, but correctly rejected the missing
EPHEMERAL effects JSONL copy. The broader hypothesis that all three missing
files evade audit is not supported. This is an audit-adequacy result only, not
an XTerm timing or product result.

| Case | Frozen auditor | Exit | Result |
|---|---|---:|---|
| Baseline | `CONSTRUCTION_AUDIT_ACCEPT` | 0 | accepted |
| Delete EPHEMERAL ready receipt | `CONSTRUCTION_AUDIT_ACCEPT` | 0 | gap reproduced |
| Delete RESIDENT done receipt | `CONSTRUCTION_AUDIT_ACCEPT` | 0 | gap reproduced |
| Delete EPHEMERAL effects JSONL | `CONSTRUCTION_AUDIT_REJECT` | 1 | correctly detected |

The exact public source commit, audit SHA-256, raw SHA-256, container image ID,
and resource limits are in `FREEZE.json`. The original 68-file input was
unchanged. Mutations were isolated disposable copies. No formal Xvfb/XTerm run,
GPU work, workflow, or external service was used.

The first post-run classifier treated a correctly rejected file deletion as an
unexpected error. The frozen probe output was not changed or rerun. A separately
named v2 classifier was applied to that same output and correctly classified
the mixed acceptance/rejection pattern as `HOLD_PARTIAL_GAP`.

## Retained outputs

- `probe-report.json` — complete stdout, exit codes, auditor outputs, and exact
  manifests for baseline and all three disposable copies.
- `postrun-classification-v2.json` — independent classification of the saved
  probe report.
- `postrun-classifier-v2.py` — stdlib-only verifier/classifier source.

SHA-256 of the full probe report:
`7f52a95b3dc3fab10061eee3d32bba6a6b2573b28518f5d299005c64aed9276e`.
