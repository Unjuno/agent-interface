# W2 lease-close ordering probe

Successor issue: [#5127](https://github.com/Unjuno/agent-interface/issues/5127), following preregistration in [#5116](https://github.com/Unjuno/agent-interface/issues/5116#issuecomment-5861352348).

This additive package retains a host-CPU paired diagnostic against the exact frozen W2 verifier, auditor, schema, and fixture. It does not copy or modify those frozen sources. `FREEZE.json` pins their upstream Git blob IDs and the local SHA-256 values. `REPORT.md` defines H/T/D/C/U and interprets the scoped checker disagreement. `PUBLIC_RESULT.json` is the path-sanitized run record; it records SHA-256s for both trace inputs, both verifier outputs, and the control audit output. The treatment auditor's exit-1 stderr is retained in the result; it failed before writing an audit JSON.

The reusable runner is `run_probe.py`; the result sanitizer is `sanitize_result.py`. On Windows/Python 3.12.10, invoke the runner with a directory containing the four exact pinned sources and a new output directory:

```powershell
python run_probe.py --source-dir <frozen-source-directory> --output-dir <new-output-directory>
python sanitize_result.py --run-dir <new-output-directory>
```

The retained outcome is `FAIL_W2_CLOSE_ORDER_CHECKER_DISAGREEMENT`, not a product/runtime failure claim and not Docker/formal evidence. Preserve it unchanged; any repair or container run belongs in an append-only successor result after explicit resource ownership and a fresh source freeze.
