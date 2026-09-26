# Issue #4520 — one-shot host broker exit propagation

## H — Hypothesis
The one-shot broker records the child process return code, but `return broker.get("returncode") or 1` maps a successful child exit (0) to failure (1). Preserve zero exactly while keeping missing status nonzero.

## T — Test
Change only the one-shot return mapping. Add deterministic subprocess-mock coverage for child exit 0, child exit 23, timeout, and unavailable executable. No live model invocation.

## D — Data / implementation
Base: main commit c9bfb14c41b9ce72782a03ed4bfa0d814baf6a8f. Branch: `fix/issue-4520-broker-exit-propagation`. Changed broker and its focused contract test; this evidence file is additive.

## C — Checks
Local host Python 3.12.10, jsonschema 4.25.1:
`python -m unittest -v runtime.test_docker_host_model_bridge_v1 runtime.test_host_model_ipc_broker_v1 runtime.test_docker_schema_preflight_v1`
Result: 28/28 passed (bridge 2, broker 8, schema 18; 0.982s). The local scratch test used the intended single-backslash newline fixture; branch readback was corrected and verified to match that source spelling. The corrected remote file was not rerun locally after upload, so CI remains necessary.
Docker Desktop: UI reported Engine running, but bounded Docker Engine API/CLI probes timed out, and other unrelated Docker CLI processes were active. No Docker test is claimed. No model/API call, authority grant, GUI action, or live container experiment was performed for this issue.

## U — Uncertainty / next gate
Draft PR and CI are pending. Run the focused contract suite on the exact branch head, then the relevant Docker Desktop gate once the engine transport is responsive; review before merge. Historical #3924/#4485/#3926 evidence is unchanged. #3926's separately allocated Engine 29.8 branch was not touched.
