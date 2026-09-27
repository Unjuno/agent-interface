# Excluded construction — Issue #4150

No full 64-row formal corpus was generated during construction.

Checks before freeze:
- `python -B test_contract.py`: 6/6 PASS.
- `python -m py_compile experiment.py audit.py controls.py test_contract.py`: PASS.

Directed construction checks only the closed margin boundary, narrow-margin PROBE/NEEDS_DECISION split, tie ambiguity, invalid provenance refusal, below-min/empty refusal, and the deliberately incomplete top1 negative control.

Formal invocations: 0. Reruns/replacements/tuning: 0.
