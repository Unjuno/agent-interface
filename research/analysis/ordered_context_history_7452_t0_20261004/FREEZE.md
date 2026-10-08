# PRELAUNCH_FREEZE — Issue #7452 T0

- Allocation: `ORDERED-CONTEXT-HISTORY-7452-T0-20261004-01`
- Frozen main: `0db425b379f9438bf6b13c95dce1b763750b06d5`
- Branch: `research/ordered-context-history-7452-t0-20261004`
- Candidate invocation: 0; independent auditor invocation: 0; formal retries: 0.
- Runtime plan: native Ubuntu WSL2, standard-library Python, no container/image/network/model/GUI/GPU/input. WSLc is present (`wslc 3.0.1.0`) but its already-started `container list --all` call remained live without output after two 30-second waits; do not restart/terminate it. `wsl.exe --list --quiet` returned Ubuntu promptly. This one-shot fixture does not exercise or claim container behavior.
- Construction tests: repaired source `python -m unittest -v test_method.py`, 5/5 PASS; `py_compile` PASS. The earlier 4/5 duplicate-row construction failure is preserved in `CONSTRUCTION_HISTORY.md`.
- SHA-256 (frozen source/docs):
  - `model.py`: `02f04e3a9060b37e64658220e0922e1847ec0df22c44b80a343e60e8f670a3e7`
  - `candidate.py`: `6e66485c0e894be02aae31f1b426e6bf6e979eb85250dfed8cb7f97920e858f7`
  - `auditor.py`: `f627e7ccdae9944335c3807fed8c0c0b67baa0366dc15d5aeb2a543976dabfa1`
  - `test_method.py`: `186a18adbcab586a055b9d6723d365189178122e86f537c2072a017e747b9589`
  - `README.md`: `224190f101da626e4e76fd3af1dab18c7f7d59f3d6c40b70a7bda6a7573fea63`
  - `CONSTRUCTION_HISTORY.md`: `aad1f3ac0e23c72c889959c5ccfaacda878277926ec25d843a5ecdc466bf3bec`

Only the commands explicitly named as the single formal candidate and single formal auditor below may produce formal outputs. No retry is allowed after either invocation. A changed frozen-source digest, mismatched main gate, missing/contaminated output, or failed candidate exits the allocation before the auditor.

1. Candidate once: `python3 candidate.py results/candidate`
2. Auditor once and only if candidate exits 0 and produces its raw file: `python3 auditor.py results/candidate/candidate.json results/audit.json`

The raw candidate and audit files are immutable after their first outcome. Tests are construction checks, not a replacement for this pair.
