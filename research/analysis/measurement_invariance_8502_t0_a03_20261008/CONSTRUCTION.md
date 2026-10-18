# Construction history (before formal freeze)

- First, `test_candidate.py` was written before `candidate.py`. The initial test invocation failed at import with `ModuleNotFoundError: candidate`; no candidate code existed yet. This was a test-first construction stop, not a method result.
- After the candidate existed, the targeted cutpoint test demonstrated the corrected same-cutpoint statistic: the hand-calculated expected maximum is 0.40, while the retired difference-of-maxima formula would be 0.04.
- Fresh-seed fixture construction and independent contingency-table checks were exercised only as construction tests. No `candidate.json`, `AUDIT.json`, or `FREEZE.json` existed during these checks.
- Before freeze, the construction suite ran five times as source/tests evolved; the latest suite passed 7/7 in normal Python. The full synthetic fixture-family candidate helper was exercised nine times in those construction checks, and the independent-auditor test suite four times. These are explicitly non-formal calls.
- Python 3.12.10; standard library only. No container, model, GUI, network, GPU or participant data. No A01/A02 file or program was changed or executed.

The formal allocation begins only after `FREEZE.json` exists and records one candidate plus one independent-auditor invocation, zero retries.
