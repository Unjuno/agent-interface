# Issue #4520 — one-shot host broker exit propagation

## H — Hypothesis
The one-shot broker records the child process return code, but `return broker.get("returncode") or 1` maps a successful child exit (0) to failure (1). Preserve zero exactly while keeping missing status nonzero.

## T — Test
Change only the one-shot return mapping. Add deterministic subprocess-mock coverage for child exit 0, exit 23, timeout, and unavailable executable. Assert the broker process return code matches the receipt for child completions, while preserving the response bytes. No live model invocation.

## D — Data / implementation
Intake base: main commit c9bfb14c41b9ce72782a03ed4bfa0d814baf6a8f; broker blob f307daafdfd36d1ab4faf39bb36c36350e6e67e4; test blob e645ae575cd6fdae02556df9facc9919739584f3. Branch: `fix/issue-4520-broker-exit-propagation`. The PR diff now changes only the one-shot mapping and focused tests (plus this additive evidence path); original CRLF line endings are preserved in the runtime source.

## C — Checks
Local host Python 3.12.10, jsonschema 4.25.1, scratch mirror of the frozen source plus current focused change:
`python -m unittest -v runtime.test_docker_host_model_bridge_v1 runtime.test_host_model_ipc_broker_v1 runtime.test_docker_schema_preflight_v1`
Result: 28/28 passed (bridge 2, broker 8, schema 18; 0.400s). Broker cases cover child exit 0, child exit 23, timeout, and unavailable executable. The exact remote branch-head suite and GitHub CI have not run/reported; see U.

Docker Desktop: Engine API pipe exists and the Desktop/backend processes are present, but four other Docker CLI requests remained live, and no Docker test was started to avoid adding contention or disturbing their jobs. Earlier bounded CLI/API probes timed out while the UI had reported Engine running. No Docker result is claimed. No model/API call, authority grant, GUI/task action, or live container experiment was performed for this issue.

## U — Uncertainty / next gate
Draft PR #4524 remains pending. Run the focused tests and applicable CI against the exact branch head, then the relevant Docker Desktop linux/amd64 gate when Engine API contention clears; obtain review before merge. Historical #3924/#4485/#3926 evidence is unchanged. #3926's separately allocated Engine 29.8 branch was not touched.
