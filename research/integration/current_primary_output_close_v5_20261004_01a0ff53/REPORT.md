# Primary stdio output-close V5 addendum

This candidate is based on current `main` commit `9c3a6b8a761e460baa6a3c8c801c93a34f3b7252` (observed 2026-10-04 00:03:06 UTC). The selected base versions of `primary_stdio.mjs`, the existing stdio tests, and `native-mcp-v1.yml` match the immediately prior reviewed base `61e704d63cb917ba5f03e2533c6e110e9daddb2f`; current-main was rechecked before composition. No main write occurred.

The source repair observes a silent output `close` during each write, throughout the line-transport lifetime, and from the outer primary owner while startup/cleanup is active. The new startup regression holds filesystem-capacity inspection, closes stdout, then releases startup; the host fixture is started and retired, but no ready line or exchange directory is produced. This proves that dispatch initialization is stopped; it does not claim the already-started fixture was avoided. It refuses commands after a close observed while idle, settles already destroyed output before exchange execution, preserves first failure, waits for already accepted work, and does not replay it. A preclosed stream with `destroyed`/`closed` flags now refuses before host startup; the intended source-owner policy is zero task executions in that case. This does not prove an OS receiver is dead while all Node stream flags remain open.

Local verification on macOS with Node 26.7.0 and inert fixtures:

- The current-main 17-module workflow Node command ran with the new evidence-root environment and all listed source dependencies present: **211 tests passed, 0 failed**, PID 53876, exit 0. Raw output and receipt are in this directory.
- The workflow's separate strict UTF-8 module passed **15/15**, PID 54265, exit 0; raw output and receipt are included.
- `git diff --check`, `node --check runtime/host_v1/primary_stdio.mjs`, and YAML parsing passed.
- Hosted Ubuntu Node 22 and the Python/native integration step were not run here. No GUI, physical input, model/provider, formal allocation, or task-effect/release experiment was run. Full computer-control correctness, finite recovery, latency, and total-resource claims remain unproven.

Two exploratory invocations were incomplete because the sparse local checkout omitted test dependencies; a subsequent invocation initially passed 187 tests while silently omitting two unavailable files. These are retained as incomplete local diagnostics, not validation. The definitive 210-test run above was made after checking out all five missing tracked dependencies from this exact base. A separate invocation-construction attempt also mistakenly passed a `.py` dependency to Node; it was retained locally and is not a product failure.

The five code/workflow changes are limited to the product module, workflow, and two output-close regression modules (the existing failure-order module already exists on main). Product SHA-256: `96dbb1cca146210c51b1c7a24c23666ba7d37634fc4b549085b6c4fcb57dca21`. Workflow SHA-256: `6234226e80e553ec5733c9ffb11996c9fee8b28f608fd36c64cf74fb6a52040d`.

Per the previous V5 evidence, PR #7248 remains an historical, open draft based on older main20db889; its reviews, approvals, and artifact digest do not transfer. This addendum must be a fresh current-main proposal. The canceled V4 send path remains canceled. Main sends: 0; unknown sends: 0.

The dedicated startup-close regression passed 4/4 in its focused run (including its three prior whole-owner cases). Its witness, host receipts, and exact inert fixture text are retained under `startup-close/`. This fixture is intentionally allowed to start during an in-flight asynchronous capacity check; the tested guarantee is no exchange/ready/task dispatch and orderly close.
