# Issue #4682 — runtime-bound result-ledger audit

Successor to #4665 / PR #4675. Preserve predecessor allocations, sources, and results unchanged. This allocation tests audit runtime provenance and construction reproducibility only.

## H — hypothesis

The local auditor must reject any Docker Engine, daemon platform, image ID, image platform, or CPython version that differs from the frozen environment before invoking semantic audit. The construction suite must use this package's immutable `inputs/` and pass on this exact main snapshot.

## T — frozen local allocation

- Intake main: `fb7bb7c82baf2be614e6e1d14fd0245c48c81b87`; allocation `issue4665-runtime-provenance-fixture-v2-20260927-01`.
- Additive branch `research/issue4665-runtime-provenance-fixture-v2-20260927`; path `research/audits/issue_4665_runtime_provenance_fixture_v2/`.
- Ten immutable predecessor input roles and `MANIFEST.json` are copied byte-for-byte from the exact intake main snapshot; role file hashes are frozen in `FREEZE.json`.
- Construction suite: predecessor's four tests plus three runtime-guard tests; no formal Docker audit in this phase.
- One formal local Docker invocation, using cached image ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; `--pull=never --network none --read-only`, source/input read-only, fresh output writable, 1 CPU, 512 MiB, 32 PIDs. Host receipt is generated from local `docker version`, `docker info`, and `docker image inspect`; container reports `sys.version_info`.
- Expected runtime: Docker Engine 29.8.0, daemon `linux/x86_64`, exact cached image ID above, image `linux/amd64`, Python 3.12.14. No other workspace containers are inspected or touched.
- Five predeclared one-field receipt/runtime mismatch controls (engine, daemon platform, image ID, image platform, Python) call the same pure validator before semantic audit. Then one baseline and three existing ledger mutation cases exercise the auditor.
- A second isolated local Docker invocation runs a raw-only independent verifier over `FREEZE.json`, `AUDIT.json`, the receipt, and immutable files. No GitHub Actions/workflow is run; no model/provider/GUI/input, no predecessor runner/auditor/formal replay, no retries or tuning.

## D — decision

- `PASS_RUNTIME_BOUND_AUDIT_SCOPED`: all frozen identity hashes reconcile; host runtime and in-container Python exactly match; construction tests pass; exact ledger envelope passes; dropped-role, altered-digest and wrong-path controls reject; every one-field runtime mismatch stops before semantic audit; independent raw audit reports zero errors.
- `FAIL_RUNTIME_MISMATCH_ACCEPTED`: any mismatch control permits semantic audit or scoped PASS.
- `FAIL_CONSTRUCTION_FIXTURE`: the package-local tests fail to load or reconcile the immutable inputs.
- `FAIL_RESULT_LEDGER_BINDING`: a complete baseline or any ledger mutation behaves contrary to the frozen gate.
- Typed `STOP_PROVENANCE_OR_ENVIRONMENT` for missing/malformed host receipt, any source/input/image/runtime mismatch, or unavailable local engine/image. Preserve first outcome; no retries.

## C / U

Only this additive audit package. Network-disabled local Docker Desktop, no credentials, no writes to predecessor paths. Synthetic result-ledger and runtime-provenance checks only; does not recover #4649's unpublished formal ZIP, prove arbitrary auditor completeness, validate other engines/platforms, or establish any runtime/product claim.
