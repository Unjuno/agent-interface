# Construction diagnostic run record

- Issue: #8630; prior one-shot T0 A01 remains unchanged at branch head `3e4a66b7a047fdd08a3c0dfe8a33838bad468929` and remains `FAIL_METHOD`.
- Diagnostic source main: `ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385`.
- Classification: exact-arithmetic construction diagnostic; not a formal or live allocation.
- Model freeze: `MODEL.json`, authored before the calculator/oracle run. Its package SHA-256 is recorded in `SHA256SUMS.txt`.
- First output attempt: shell could not open the redirection target because `run-01/` did not exist; calculator process was not started. No candidate or scientific calculation ran in that attempt.
- Calculator: `python3 -B diagnostic.py > run-01/candidate.json 2> run-01/candidate.stderr`; invoked once after creating `run-01/`, exit 0.
- Independent path enumerator: `python3 -B enumerate_oracle.py < run-01/candidate.json > run-01/oracle.json 2> run-01/oracle.stderr`; invoked once, exit 0.
- Construction tests: 4/4 normal and 4/4 optimized. These tests validate the diagnostic model and do not invoke any prior A01 or formal candidate/auditor.
- Reconciliation: both regimes contain 8 feasible policies; the independent enumerator reports `PASS_DIAGNOSTIC`, zero errors, observe for informative and skip for weak signal.
- Result: informative 19/20 vs never-observe 71/80; weak signal 7/8 vs always-observe 151/200. All scored schedules retain mandatory verification and at least one recovery attempt.
- Scope: the authored probabilities and independence assumption are illustrative only. No GUI, runtime, model, latency, token, safety-rate or product evidence.
