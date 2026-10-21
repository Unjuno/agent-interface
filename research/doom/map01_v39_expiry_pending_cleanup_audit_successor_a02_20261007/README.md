# A02 expiry-receipt auditor correction

## H / T / D / C / U

**H.** The merged A01 raw auditor validates nested physical-up evidence but can accept contradictory top-level receipt metadata. Three independently reported mutations set the emitted receipt's authority flag to true, add a conflicting `edge=down`, or change its reason from `expired` to `cancelled`. A strict, versioned correction should reject these while preserving acceptance of the exact retained raw and all previously declared controls.

**T.** Reuse the immutable fake-display A02 raw JSON from A01. Run the same eleven-case gate against the merged A01 auditor and this versioned auditor under normal and optimized Python: unchanged raw plus ten negative mutations (the original six, three isolated metadata mutations, and one coordinated mutation of both receipt copies). Run the corrected auditor directly on the retained raw. Do not execute the candidate or any runtime, GUI, model, input, container, or game path.

**D.** PASS_AUDIT_CORRECTION_SCOPED requires the baseline to reproduce the three isolated false accepts in both interpreter modes; the corrected auditor must accept the unchanged raw and reject all ten mutations in both modes; and the raw file's SHA-256 must match A01. Any accepted negative control or rejected unchanged raw is FAIL for this correction.

**C.** Existing nested-evidence equality and identity checks are useful, but do not constrain contradictory or unrecognized top-level fields. Exact emitted-to-owner receipt equality closes disagreement between the copies; explicit authority/reason/edge checks and exact receipt-key validation also reject coherent corruption of both copies.

**U.** This is a correction to one offline auditor over one immutable synthetic fake-display record. It does not change the A01 candidate or its scientific disposition, validate production input or physical release, or close Issue #59's live threat-control gate.

## Result

The merged A01 auditor reproduced the three reported false accepts. The A02 correction accepts the retained raw and rejects all ten negative controls in normal and optimized Python (11 tests, 22 isolated auditor subprocesses). A direct raw-only CLI audit also passes. No candidate execution, formal/live allocation, container, model call, GUI, OS input, or game run occurred.

The correction requires the owner cleanup receipt and emitted receipt to have the canonical field set and exact matching content. It also checks that neither receipt grants input authority, that each reason matches the owner's `expired` cleanup, and that the nested physical edge is `up`.

## Reproduction

From the repository root:

```powershell
python research\doom\map01_v39_expiry_pending_cleanup_audit_successor_a02_20261007\test_mutation_gate_v2.py research\doom\map01_v39_expiry_pending_cleanup_audit_successor_a01_20261005\audit_successor.py
python research\doom\map01_v39_expiry_pending_cleanup_audit_successor_a02_20261007\test_mutation_gate_v2.py research\doom\map01_v39_expiry_pending_cleanup_audit_successor_a02_20261007\audit_successor_v2.py
python research\doom\map01_v39_expiry_pending_cleanup_audit_successor_a02_20261007\audit_successor_v2.py --candidate research\doom\map01_v39_expiry_pending_cleanup_audit_successor_a01_20261005\results\formal_02\candidate.json
```

The first command is expected to exit 1 with three failing mutations; its output is retained. The next two commands exit 0. The audit script prints its result and does not write into A01 or modify the retained input.

## Provenance

- Intake/source base after current-main refresh: `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`.
- Immutable A01 input: `research/doom/map01_v39_expiry_pending_cleanup_audit_successor_a01_20261005/results/formal_02/candidate.json`, SHA-256 `961b867713d9fbbef923b61b6271b6f4f8a94a488b4833f344e3583411b433cf` (also verified against A01's `SHA256SUMS.txt`).
- A01 auditor, its original report, and its source manifest are unchanged.
- `SOURCE_LOCK.json`, `RESULT.json`, saved command outputs, and `SHA256SUMS.txt` bind this correction and its limits.
