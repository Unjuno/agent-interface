# Development record

1. The merged capability model still marks direct keys as coarse `ASCII` support. The prior XKB transfer result showed German/French Group1-level0/1 gaps, motivating payload-aware eligibility.
2. A first development matrix duplicated all 95 printable ASCII characters × two budgets. US completed PASS; the run hit the outer 120 s limit during German because each clipboard fallback spawned two Tk owner processes. This was fixture overhead, not a scientific failure; no formal ID was consumed.
3. The matrix was reduced to the complete union of retained German/French gap characters plus `office` and `βeta` (13 payloads). This preserves every selector disagreement while avoiding duplication of PR #328's exhaustive direct-key matrix.
4. A second development run completed US and German PASS but again hit outer timeout during French because fallback still spawned processes per trial.
5. Fixture-only optimization: one prior clipboard owner and one mutable clipboard service per arm. Each trial audits clipboard mutation version, owner identity, direct emissions, keymap fingerprint and physical release. Scientific routing conditions are unchanged.
6. Final development matrix: 104/104 gates PASS; route counts direct 56 / clipboard 24 / none 24; coarse-selector mismatch 40. Stop tuning and freeze.
