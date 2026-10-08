# Run log — Issue #5440 T2

All timestamps below are from the 2026-10-01 local task session. The exact frozen main SHA is in `FREEZE.json`.

1. **Candidate construction checks (pre-freeze):** Docker Desktop, pinned Python 3.12 slim image, network none, read-only source. `python -B -m unittest -v test_construction.py` → 4/4 PASS. No raw candidate allocation consumed.
2. **Freeze:** candidate, auditor-v1, input, test source and base main hashes recorded. Main rechecked immediately before candidate invocation and matched `a2469a821f4d27d2ec9a1d5d63ed8b81e57f81c3`.
3. **Candidate:** one Docker Desktop invocation; exit 0; 20 rows: 8 `ROBUST`, 12 `UNIDENTIFIED`, 0 `SENSITIVE`. Raw retained, SHA-256 `048e47d158dc9bacf26877a783864120398e46d8c638d416bff3760de1f3a09f`.
4. **Auditor-v1:** one separate Docker Desktop invocation; exit 1; `FAIL`, errors `base_main_sha` and `candidate_row_18`. Raw was not changed. Output SHA-256 `b3d6c55d9585db6f22905db2b2efa3661a5a544a5de65026c16861512a4889a1`.
5. **Auditor-v2:** one separate Docker Desktop invocation; stopped with `KeyError: 'mode'` before writing an audit result. Recorded as `STOP_AUDITOR_EXCEPTION_BEFORE_RESULT`; no candidate rerun.
6. **Auditor-v3 construction checks:** a new source passed 2/2 tests in a separate network-disabled Docker Desktop container; tests only derived expected rows from frozen input and did not read raw.
7. **Auditor-v3:** one separate raw-only Docker Desktop invocation against the original raw; exit 0; `PASS_T2_SYNTHETIC_SCOPE_GATING`, exact rows, 8 hidden-world reversals, 8 fail-closed `UNIDENTIFIED` decisions, 4/4 controls rejected, zero errors.

No network access, model/provider, GPU, GUI, X11, game, physical input, or user data was used. No candidate retry or rerun occurred.
