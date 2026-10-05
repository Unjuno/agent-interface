# Retained-result audit v2

The original `audit.py` and `RESULT.json` are historical evidence and remain unchanged. A separate mutation check showed that the original audit returned `AUDIT_PASS` after changes to the cover terminal status, acceptance timestamp, aggregate death count, and physical-occupancy limitation. Those fields therefore were not fully protected by the original audit.

`audit_v2.py` validates the source commit, blob IDs, SHA-256 hashes, and byte counts from `FREEZE.json`, then independently rebuilds the complete saved result projection from the pinned report and event stream. It checks exact JSON types as well as values, preventing booleans from passing as integer timestamps. It does not rerun `analyze.py`, the game, a model, or input.

The test suite runs the v2 auditor on the unchanged result and on temporary mutated copies. It confirms rejection of incorrect terminal state, admission timestamp, model wait, aggregate deaths, physical-occupancy scope, and a boolean timestamp alias. The original audit remains available as an immutable historical check; use v2 when claiming complete validation of `RESULT.json`.

Reproduce from the repository root:

```text
python3 -B research/doom/v39_retained_diagnosis_59_a01_20261005/audit.py
python3 -B research/doom/v39_retained_diagnosis_59_a01_20261005/audit_v2.py
python3 -B -m unittest research.doom.v39_retained_diagnosis_59_a01_20261005.test_audit_v2 -v
```

This repairs result-field verification only. The diagnosis remains descriptive: threat descriptions are model-authored, score and visible-change receipts are not independently attributed to individual actions, and no live threat response, useful feedback, survival benefit, or MAP01 exit is established.
