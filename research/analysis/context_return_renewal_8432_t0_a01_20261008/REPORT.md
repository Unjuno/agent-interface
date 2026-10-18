# Issue 8432 T0 A01 — first-run report

## Decision

**FAIL_METHOD_GATE.** This deterministic construction-only run makes no model-behavior claim and does not satisfy the method gate.

## Frozen execution and first outcome

- Runtime: Ubuntu on WSL, WSL package 3.0.1, Python 3.12.3. Docker was not used; this CPU-only task ran directly in WSL.
- Candidate: exactly one invocation; exit 0; wrote `RAW.json`; SHA-256 `8e448a60072da2e53822da417d32446c4910a262b3da56c92c55a2af296eaa2f`.
- Candidate stdout claimed 18 episodes, but the retained raw has 9: three each for `chronological`, `context_tagged`, and `none`. Only six episodes have matched (non-`none`) histories.
- Auditor: exactly one invocation; exit 1 with `ValueError: expected 12 matched episodes`; no `AUDIT.json` was written.
- Model, GUI, network, game, and OS-input calls: zero.
- No candidate/auditor rerun, retry, or edit to the frozen sources occurred.

## Interpretation

The raw agrees with the auditor's independent reconstruction, which itself constructs 3 treatments × 3 tracks = 9 episodes. The frozen decision text nevertheless requires 12 matched history-treatment × context-track episodes, while only two of the three treatments are matched, yielding 2 × 3 = 6. The frozen candidate's summary count of 18 also disagrees with the retained raw. These internal count inconsistencies invalidate the method gate. Since the one-shot stop rule was reached, this allocation stops here; any corrected design must be a separately frozen successor allocation/issue and must preserve these files as the failed predecessor record.

## Provenance

The exact candidate, auditor, protocol, and freeze remain unchanged from the pre-run commit `d75ab5946e4dca12b47868c39d34ea8bca450311`. Their source hashes are in `FREEZE.json`. `RUN_RECEIPT.json` records the full machine-readable outcome. `RAW.json` is the sole generated experimental artifact; the lack of `AUDIT.json` is itself recorded and must not be replaced with a fabricated audit.

