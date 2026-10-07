# Expected-key inventory provenance construction A01

## Result

`PASS_INVENTORY_PROVENANCE_COUNTEREXAMPLE`. On the exact completeness wrapper frozen from PR #7695, deleting the `SPACE` interval and passing the underdeclared inventory `("W",)` returns `BOUNDED` with `W=70..90 ns`. The same omission with the correct frozen inventory `("SPACE", "W")` returns `UNKNOWN`; the complete fixture with that correct inventory remains `BOUNDED`. A separate raw-only auditor confirmed the original fixture has both key rows and the mutated set has only `W`.

This demonstrates that the A01 expected-key check is only as complete as its caller-supplied inventory. It does not prove that live telemetry will be omitted or that this synthetic interval bound reflects physical key-up. The pinned fixture contains no independent admission record from which the expected key set can be authenticated. Any successor that claims complete per-key coverage must bind the inventory to action-admission evidence.

## Provenance and verification

- Candidate and fixture are exact copies from PR #7695 head `7ed0dd27c3ebde976744cc7cae0062d8b449eb14`; source hashes and current main at selection are in `FREEZE.json`.
- One deterministic candidate run wrote `experiment-output.json`.
- The raw-only auditor in `audit.py` imports neither `candidate.py` nor `ledger.py` and wrote `audit-output.json` with all checks passing.
- `python -m py_compile candidate.py ledger.py run_experiment.py audit.py` passed; `git diff --check` passed.
- `SHA256SUMS.txt` covers the frozen inputs, protocol, scripts, outputs, and this report.

Scope is a standard-library host construction replay. No game, X server, GUI, model, input, GPU, or container was used. It does not establish live occupancy, useful feedback, recovery, task effect, survival, MAP01 progress, safety, latency, or human tempo. The separate #59 live allocation remains required.
