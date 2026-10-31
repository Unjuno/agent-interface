# Calc fresh-grounding comparison: release receipt contract correction

The archived `wslc_calc_persistent_grounding_comparison_20261031` runner requires a nonempty verified neutral release after the first click, and its compiled composition similarly rejects an empty release list. In contrast, the fresh route's entry and save checks used `all(...)` over `releases` without requiring a member. Python considers `all([])` true; the checks also treated a missing key/button field like an empty list. Thus a `completed` result with absent release evidence could continue to another consequential action or report completion. This is a defect in that **research comparison runner**, not proof of a production backend fault or an observed missing release during the historical four runs.

`runner-successor.py` is the archived runner with only those two conditions changed: a nonempty release list is required, and every receipt must have `verified is True`, `keys_down == []` and `buttons_down == []`. Historical raw archives remain untouched. `verify_history.py` checks the archived runner SHA across all four runs, verifies actual entry/save release receipts in the two fresh runs and the compiled transition release flags, and checks that only those two runner lines differ. It uses assertions and must run without Python optimization.

`test_release_contract.py` extracts and evaluates the actual two branch predicates from the successor source. Before the correction, six subcases failed: missing, empty and missing-key-state receipts were not rejected for entry and save. After the correction, missing/empty/unknown/held input and failed-status cases are rejected, while an explicit verified neutral release is accepted. Tests pass under normal Python and `python -O`. This is local predicate fault injection: it does not exercise GUI, provider behavior, cancellation, an end-to-end composed fault path, or delayed task effects.

Run from any working directory in a checkout containing the existing comparison archives:

```
python research/integration/calc_fresh_release_contract_20261031/verify_history.py
python research/integration/calc_fresh_release_contract_20261031/test_release_contract.py
python -O research/integration/calc_fresh_release_contract_20261031/test_release_contract.py
```

This successor is a research harness starting point; it has not been run as a new live comparison. Existing timing/token figures remain descriptive for their actual positive runs and do not establish comparable fault handling. A future matched comparison must exercise absent, unknown and delayed-release outcomes through both complete paths with independent effect checks and no blind replay.
