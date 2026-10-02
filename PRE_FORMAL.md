# A03 pre-formal construction record

Allocation: `EXOGENOUS-OPPORTUNITY-BOUNDARY-5694-A03-20261002-01`.

The first construction invocation used:

```text
python -B -m unittest discover -s . -p 'test_*.py' -v
```

It passed 7/8 tests and failed only `test_candidate_and_independent_replay_match_on_frozen_rows`: candidate and raw-only auditor used different descriptive strings for the same observed receipt. No candidate CLI, formal output, auditor CLI, model, GUI, container, or WSLc process was invoked. The labels were normalized before the source freeze.

Before freezing, a separate semantic inspection found a censoring error: an opportunity whose capture and delivery were observed but whose expiry remained in the future could not yet be classified as a missed decision. The fixture now includes this case and both independently written classifiers retain it as `UNKNOWN/right_censored`, unless a terminal safe-stop or independently verified effect is already present.

The corrected construction command above ran at approximately 2026-10-02 19:28 UTC: **8/8 passed**. `python -B -m py_compile candidate.py auditor.py test_protocol.py` also exited 0. These are construction checks only; formal candidate/auditor counts remain 0/0 before the one-shot window.
