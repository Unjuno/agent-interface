# Issue #5205 — audit-only supplemental verification

Audit allocation: 'typed-mode-4844-calibration-v5-posthoc-audit-20260928-01'.
Branch: 'research/typed-mode-calibration-v5-posthoc-audit-20260928'.
Additive path: 'research/experiments/typed_mode_generalization_4844_calibration_v5_audit_v1/'.

## Scope and H

The original #5198 allocation-01 runner was executed once; its frozen auditor then failed because parsed JSON arrays were compared against reconstructed Python tuples. This separate post-hoc audit asks whether a newly authored, raw-only reconstruction that JSON-normalizes the independent reference confirms the immutable raw exactly and can apply #5198's preregistered decision criteria as a supplemental audit finding.

This is not a new data allocation, not a retry of the old auditor, and not permission to invoke the frozen formal runner. #5198 remains STOP_AUDITOR_IMPLEMENTATION_DEFECT regardless of this audit's outcome.

## T — bounded audit protocol

- Sole input: the exact 2,794,446-byte result.json from #5198; expected SHA-256 b55b8d9e58497c47ef5a2152d1236d27fdb6918a018cbeebf2a75f0b5f709470. At launch, copy/read the raw from PR #5198's published path if merged, otherwise the original retained local file. Verify byte count and SHA before any reconstruction, then mount the file read-only.
- Bind reference lineage to #5198 source commit 668b888a47ddfbb1a50e1dd9ff3a386836b22484, freeze SHA-256 abfc648a7599af3e041eceb5b8817a8a088bd91368d318f9b87a40f21b2963bd, and original seeds 67010231/67010232/67010233. These identify/reconstruct the existing data only; no replacement formal output is generated.
- audit_posthoc.py is separately implemented. It regenerates train/calibration/test structures in memory, independently fits the two fixed estimators, reconstructs thresholds/rows/metrics/controls, canonical-JSON-normalizes the Python reference before comparison, validates raw canonical bytes/identity, and applies unchanged #5198 decision gates. It must not write to or alter the input raw.
- Before source freeze, run only construction tests using seeds 600501/600502/600503 and 20 rows/block. Tests explicitly exercise tuple-to-JSON-array normalization and all 16 corruption controls.
- Docker Desktop desktop-linux only; cached image config digest sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a, network none, read-only root/source/raw, 1 CPU/512 MiB/32 PIDs/no-new-privileges. One construction test invocation, then one audit-only formal container invocation maximum. No formal experiment runner, GUI, model/provider, GPU, network or retry.
- Freeze exact source/tests/protocol/commands, hashes and Git blobs before the sole audit. Preserve source-container ID/inspect/stdout, raw-input digest/size, audit output/log/exit and all hashes.

## D — supplemental dispositions

POSTHOC_AUDIT_CONFIRMS_RETAINED_RAW only if the exact input hash/size/canonical encoding match, the independent JSON-normalized object equals every raw field, all thresholds/rows/metrics/controls reconstruct, and all 16/16 mutations reject. Then report the unchanged #5198 gates as a supplemental post-hoc decision; never rewrite the original STOP as a preregistered audit pass.

HOLD_POSTHOC_AUDIT_MISMATCH for any unexplained content/reconstruction/gate mismatch. STOP_AUDIT_PROVENANCE_OR_INFRASTRUCTURE for raw/source/image/command/exit/receipt failure. No retry.

## C / U

The audit reuses one immutable finite synthetic dataset; it adds no independent sample and does not cure the frozen auditor. Even confirmation is limited to the existing five-mode/six-cue family. No GUI, runtime, authority, safety, model quality, task effect, efficiency, cross-app, human-tempo or product claim.
