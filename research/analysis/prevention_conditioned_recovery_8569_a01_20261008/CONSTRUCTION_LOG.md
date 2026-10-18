# Pre-freeze construction checks

This log describes development checks only, not the formal candidate/auditor allocation.

1. Initial `python3 -B -m unittest -v test_method.py`: 5 tests ran; 2 errored because the tests attempted `float("108/125")`-style conversions. Candidate values themselves were exact rational strings. The test assertions were corrected to compare `fractions.Fraction` values.
2. Corrected pre-freeze `python3 -B -m unittest -v test_method.py` in Ubuntu WSL, Python 3.12.3: 5 tests, all passed in 0.002 s.
3. WSLc launcher smoke test using `python3 --version` did not produce a usable process result; the explicit retry returned generic `E_FAIL`, exit 1. No formal source was invoked by WSLc. Native Ubuntu WSL was selected before freeze and is the preregistered formal runtime.

The pre-freeze test suite exercises pure in-memory candidate/oracle functions and mutation rejection. It does not create, read back, or overwrite `candidate_raw.json` or `audit.json`.
