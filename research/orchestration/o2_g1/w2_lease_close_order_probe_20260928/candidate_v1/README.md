# W2 lease-close candidate matrix

Successor issue: [#5127](https://github.com/Unjuno/agent-interface/issues/5127). This is a construction-only candidate/oracle extension; the frozen verifier, raw auditor, schema, original fixture, and counterexample result are unchanged.

`close_order_candidate.py` conservatively classifies an input edge against its lease open and close intervals. `close_order_oracle.py` reconstructs the same decisions from raw event rows and is not imported by the candidate. `close_order_cli.py` and `audit_close_order_cli.py` run in separate processes. `run_close_order_matrix.py` executes six candidate/auditor pairs and retains each versioned trace, candidate report, raw-audit report, and SHA-256. The tamper control changes an after-close decision to `AUTHORIZED_MATCH` and requires the independent auditor to reject it.

Reproduce the suite from this directory with Python 3.12.10 and the exact frozen fixture from `research/orchestration/o2_g1/w2_measurement_v2_20260927/trace-cases.json`:

```powershell
$env:W2_TRACE_FIXTURE = "<path-to-frozen-trace-cases.json>"
python -m unittest -v test_close_order_cli.py
python run_close_order_matrix.py --fixture $env:W2_TRACE_FIXTURE --output-dir <new-output-directory>
```

`FREEZE.json`, `REPORT.md`, and `RESULT.json` state provenance, gates, limits, outcomes, and hashes. The candidate is not a production repair, formal result, or Docker result. Missing/foreign close actuation lineage conservatively holds; that behavior does not claim the broader contract has chosen close scope.
