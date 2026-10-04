# Issue #7712 T0: exact discrete PID qualification

**Disposition: `PASS_METHOD_SCOPED`.** The frozen bivariate Williams–Beer `I_min` implementation recovered the expected redundancy, unique-information, and synergy atoms on six exact integer-count distributions. The separately written raw-data auditor independently reconstructed all rows; three frozen mutation controls rejected source relabeling, deleted probability mass, and a changed joint distribution.

| Fixture | Redundancy (bits) | Unique X1 (bits) | Unique X2 (bits) | Synergy (bits) | Joint MI (bits) |
|---|---:|---:|---:|---:|---:|
| Duplicate source | 1 | 0 | 0 | 0 | 1 |
| X1 only | 0 | 1 | 0 | 0 | 1 |
| X2 only | 0 | 0 | 1 | 0 | 1 |
| XOR | 0 | 0 | 0 | 1 | 1 |
| Independent null | 0 | 0 | 0 | 0 | 0 |
| Imbalanced target, X1 only | 0 | 0.811278124459 | 0 | 0 | 0.811278124459 |

## Reproduction

From this directory, using CPython 3.12.10:

```powershell
python candidate.py
python audit.py
python -B -m unittest -v test_audit
```

The frozen inputs and code hashes are in `SHA256SUMS.txt`; the first run, independent result, and mutation-test outputs are in `RUN.txt`, `raw.json`, and `audit.json`. Their post-run hashes are in `RESULT_SHA256SUMS.txt`.

## Limits and next gate

This only qualifies the selected `I_min` arithmetic on six tiny deterministic distributions. It is not a comparison among PID definitions, a finite-sample estimator, or evidence about any GUI modality, model decision, acquisition cost, task accuracy, or safety. A separate read-only T1 feasibility audit is retained in `t1_readonly_audit/`: it found coherent screenshot/accessibility data and independent authored state labels in the #6678 static fixture, but no per-capture safe-action/effect labels. The proposed GUI decision target therefore remains on HOLD until a suitable independent action/effect oracle is available.
