# Excluded construction — Issue #4155

No formal row was generated during construction.

Checks before freeze:
- `python -B test_contract.py`: 4/4 PASS.
- `python -m py_compile experiment.py audit.py controls.py test_contract.py`: PASS.

Directed construction covers only four uniquely identifiable positive signatures, three UNKNOWN/contradictory/all-normal YIELD examples, variation invariance, and no-authority row shape. It does not enumerate the full 324-row formal corpus.

Formal invocations: 0. Reruns/replacements/tuning: 0.
