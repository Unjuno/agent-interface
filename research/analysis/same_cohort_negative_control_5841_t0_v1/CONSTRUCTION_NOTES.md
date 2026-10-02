# Construction chronology — Issue #5841 T0

These are test-development outcomes, not scored candidate/auditor invocations.

1. Test-first RED before `candidate.py` existed: `python -m pytest -q test_method.py` stopped collection with `ModuleNotFoundError: No module named 'candidate'` (the intended missing API).
2. First post-implementation run: 7 tests passed; 2 auditor-mutation tests errored because the test call omitted the independent expected-table argument. This was a test-harness signature error, not a candidate result. The tests were corrected to pass the frozen literal oracle.
3. After adding paired missingness cases, a targeted RED run produced 2 expected failures: the candidate compared only per-route missing counts and lacked an any-missing gate. Tests were retained and the implementation was corrected to detect episode-level asymmetry and hold every cohort with an unavailable primary outcome.
4. Final pre-freeze construction command `python -m pytest -q test_method.py`: **11 passed**. JSON decoding validation: `json-ok`. No candidate CLI or independent raw-audit CLI ran before source freeze.

No construction error was hidden, relabeled as a scientific failure, or used to tune the six frozen case outcomes.
