# Direct retained-input identity audit at current PR head

**Disposition: `PASS_TOKEN_KEY_IDENTITY_FAIL_CLOSED_CONSTRUCTION`.**

This package pins PR #7356 after merge commit `0b953488b3d09c0bc1ce08d56fbcaf635218d8d8`, which includes current main `f11ee9d051239094cf3679e19c80bd7deaed0564`. Its copied analyzer and focused tests match the integrated tree by SHA-256.

The frozen 22-case matrix has one positive nonempty string token/key pair and 21 negative cases covering absent, null, empty, integer, Boolean, list, and dict token/key identities; missing release token; mismatched token; and malformed admissions appended after a valid pair. The raw-only auditor independently recomputes readiness, interval bounds, result counters, and complete case ordering. It reports 1 ready / 21 fail-closed with zero errors in `audit-current-main.json`. The mutation control alters the positive readiness result and is rejected specifically as `candidate_result_mismatch`.

The integrated focused suite passes 12/12; Python byte-compilation and `git diff --check` pass. This is construction evidence only. No live input, X11, GUI, game, application effect, recovery, formal allocation, or efficiency run occurred.

From repository root, use a clean checkout or fresh output paths:

```powershell
python -m unittest -v research.doom.test_analyze_map01_direct_retained_input_v1
python -m py_compile research.doom/analyze_map01_direct_retained_input_v1.py research.doom/test_analyze_map01_direct_retained_input_v1.py
python research.doom/results/direct-retained-identity-current-head-v1/candidate.py
python research.doom/results/direct-retained-identity-current-head-v1/audit.py
python research.doom/results/direct-retained-identity-current-head-v1/audit-mutation-test.py
```

The candidate and auditor refuse to overwrite outputs. `FREEZE.json` and `SHA256SUMS.txt` bind the saved source, cases, scripts, and reports.
