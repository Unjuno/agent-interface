# Formal allocation STOP — seed 284937

**Disposition:** `STOP_INFRA_BROKER_ZERO_EXIT_MISREPORTED`. This is not a task-level failure and cannot support the replication hypothesis either way.

The pinned OrbStack 29.4.0 environment, source/evidence lock, host Codex identity, and import-closure gate passed. The first fresh schema-only preflight made one host Codex call. Its raw response contains one `thread.started`, one assistant message, and one `turn.completed`; usage was 31,838 input tokens (15,104 cached), 258 output tokens, and 80 reasoning tokens. The response passed the frozen JSON Schema validator. No task arm had begun.

The host Codex broker receipt records CLI return code `0`. The broker Python process returned `1` because `runtime/host_model_ipc_broker_v1.py` returns `broker.get("returncode") or 1`; Python treats `0` as false and substitutes `1`. The launcher correctly treated the broker process failure as infrastructure STOP and terminated without retry. A second schema-preflight request had been staged by the inner driver, but it has no response or broker receipt. Counts are therefore: 2 IPC requests, 1 host response, 1 broker receipt, 1 actual model call, 0 task calls, 0 retries.

The raw stderr also includes Codex MCP `AuthRequired` shutdown warnings, while the same receipt reports CLI exit 0 and the complete turn. They are retained as context; the deterministic zero-to-one exit-code conversion is sufficient to explain the launcher STOP. No claim is made that the MCP warnings are harmless in other runs.

`independent-stop-audit.json` independently verifies the request/response/receipt cardinality, host turn, schema validation, no-task state, and source-level exit-code expression. `STOP.json` records primary hashes. The frozen seed 284937 allocation is consumed and will not be retried or replaced. Any broker correction and subsequent replication require a separate additive successor issue, branch/path, and fresh allocation seed.
