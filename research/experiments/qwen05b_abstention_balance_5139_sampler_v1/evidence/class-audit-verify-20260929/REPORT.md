# Synthetic class-attribution auditor defect and repair

Date: 2026-09-29 (Asia/Tokyo)

## H/T/D/C/U

- **H — Hypothesis:** the raw-result auditor independently verifies that each row's evaluation class follows from its ground-truth intent, so a consistent class relabeling cannot preserve `integrity_pass` or per-class metrics.
- **T — Test:** synthetic sentinels formal seed `830513911` and support seed `830513912`; swap `yield:forbidden` and `yield:ambiguous` in stored support/heldout labels, regenerate selected support and heldout rows from those labels, and build internally consistent raw outputs. No model weights, GPU, CUDA, or Docker were used.
- **D — Data:** the pre-fix independent audit accepted the altered dataset (`integrity_pass=true`, `errors=[]`) and reported 64/64 exact in every arm and 8/8 in every class, despite **24** labels disagreeing with an independently derived class from intent. Reproduction output is in `result.json`; deterministic altered dataset SHA-256 is recorded there.
- **C — Conclusion:** hypothesis was false for the prior auditor. It verified selection mechanics and consistency with stored class labels, but did not independently bind the labels to intent. `audit_results.py` now derives labels from allowed intent schemas and checks every support/heldout pool row. A regression test exercises the consistent relabel-and-reselect attack. The defect concerns synthetic audit integrity, not model behavior or a Qwen result.
- **U — Uncertainty / next steps:** full local suite passes after the repair (28 tests). This is not a formal experiment result, GPU run, or evidence that a model improves. PR remains Draft; formal seeds, exact run protocol, assigned execution slot and independent review are still required before any model/CUDA/Docker run or merge.

## Reproduction and verification

Pre-fix reproducer: `python evidence/class-audit-verify-20260929/reproduce.py`.

Post-fix regression and complete package suite: `python -m unittest discover -s research/experiments/qwen05b_abstention_balance_5139_sampler_v1 -p 'test_*.py' -q` — 28 tests passed.

The independent class derivation in the auditor validates the operation shape and allowed reason vocabulary rather than importing the candidate dataset's class-label helper. Errors identify mismatching support or heldout case IDs. Historical evidence was not modified.
