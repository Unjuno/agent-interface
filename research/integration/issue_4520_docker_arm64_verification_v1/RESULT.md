# Issue #4520 — exact-head Docker contract verification

## H / T / D / C / U

**H.** The proposed one-shot broker change preserves a child exit code of zero while retaining nonzero behavior for failures, without regressing adjacent bridge/schema contracts.

**T.** Read-only verification of PR #4524 head `71adf863725b1ad4d8a33e0298b07bb85e2a10f4`. The exact PR runtime tree was mounted read-only in cached local containers. No branch source was edited, no dependency was installed, and no live model, provider, GUI, or task input was invoked.

**D.** `runtime.test_host_model_ipc_broker_v1`: **8/8 PASS**. Combined `runtime.test_docker_host_model_bridge_v1`, `runtime.test_host_model_ipc_broker_v1`, and `runtime.test_docker_schema_preflight_v1`: **28/28 PASS** (2 + 8 + 18). This supports `PASS_DOCKER_ARM64_SCOPED`; it does not establish the Linux/amd64 gate.

**C.**

- Docker image: `agent-interface-3311-host-ipc-v2-tests:20260920`, image ID `sha256:f0190b1db8563e63136a31bd90f065ba7139ef3fb1fc269ec57487c4a115e8c0`.
- Runtime: linux/arm64, CPython 3.11.16, jsonschema 4.23.0.
- Container options: `--pull=never --network none --read-only`; 32 MiB `/tmp` tmpfs; PR runtime source and schema fixtures mounted read-only.
- Test command: `python -m unittest -v runtime.test_docker_host_model_bridge_v1 runtime.test_host_model_ipc_broker_v1 runtime.test_docker_schema_preflight_v1`.
- The two schema fixtures were fetched read-only from GitHub at the exact PR head and canonical-JSON-compared with the mounted fixture copies before the final run.
- Tested source SHA-256: broker `332d57ffa87ec12da12c0e89e26434a9e049bba23691527fbcee64ae46f5d1ce`; broker test `47f385b395a2da590938e36cad579b8854e672d2ddf20f4c966910bbe0361767`.

Two setup attempts are retained as execution context, not code failures: the pinned MAP01 image lacked `jsonschema` (the focused 8 broker cases still passed there); a first broader run in the selected contract image lacked the two read-only schema fixture mounts and therefore had 26 passes / 2 fixture failures. After selecting an already-cached image with the dependency and adding the exact-head schema fixtures, the entire 28-test suite passed. No network access or package installation was used.

## Integration status and limits

At verification time PR #4524 remained open and Draft. Its GitHub `contract` and `evidence-audit-windows` checks were failing on retained historical objects absent from the workflow checkout; `replay-gate` and `audit` were successful. This Docker run validates the exact broker/contract tests but does not repair or waive those CI failures.

No cached Linux/amd64 image for this suite was present locally; no image was pulled. The result is arm64-only. It does not establish Docker Desktop amd64 equivalence, a live host model endpoint, or production integration. The matching test details were also posted to [Issue #4520](https://github.com/Unjuno/agent-interface/issues/4520) and [PR #4524](https://github.com/Unjuno/agent-interface/pull/4524); this file is the main-branch evidence handoff for integration review.
