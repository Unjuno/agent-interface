# Issue #5327 T0 — allocation 03 result

Disposition: **`PASS_FEEDBACK_CONSTRAINT_SCOPED`** and independent **`PASS_AUDIT`**. The Docker runner exited 0 for all 20 policy×scenario traces. The independent raw-only auditor exited 0 with `errors=[]` and rebuilt every event-derived fact and decision.

| Policy | Current PASS acknowledged | PASS delivery lost | Stale prior PASS | Current REJECT | Unmapped action |
|---|---|---|---|---|---|
| `LOCAL_GATES_ONLY` | Admit | Unsafe admit | Unsafe admit | Reject | Unsafe admit |
| `STPA_MODEL_ONLY` | Admit | Unsafe admit | Unsafe admit | Reject | Unsafe admit |
| `STPA_PLUS_FEEDBACK_MONITORS` | Admit | Reject | Reject | Reject | Admit* |
| `FAIL_CLOSED_UNMAPPED` | Admit | Unsafe admit | Unsafe admit | Reject | Reject |

The bounded decision criterion passed: the local-only baseline has two missing/stale-feedback hazards; the explicit feedback monitor blocks both while preserving the current acknowledged PASS; the verifier REJECT remains blocked; and the distinct unmapped-specific policy refuses an unmapped action. `STPA_MODEL_ONLY` matches local-gate behavior, illustrating that traceability documentation alone did not enforce the added constraint.

`*` The feedback-monitor-only policy does not claim to enforce the unmapped-action constraint; that is tested separately in `FAIL_CLOSED_UNMAPPED`. Combining both obligations in one production policy is outside this fixture.

## Provenance and retained failures

Allocation 01 remains `STOP_DOCKER_BIND_SOURCE_MISSING`: Docker rejected an absent host output path before container/runner start. Allocation 02's runner passed but its independent audit returned `STOP_AUDIT_MISMATCH` because it conflated sequence equality with delivered acknowledgment. Neither STOP has been overwritten or retried. Allocation 03 is a new freeze/output path, changing only the independent oracle semantics plus a construction regression test.

Docker image `python:3.12-slim`, digest `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64, Python 3.12.14, network disabled, read-only root, capabilities dropped, no-new-privileges; source mount read-only. Raw bytes 15,657; SHA-256 `39acb53e6817cf35c78e9040e7c6b574c0d2465c89d4af5abff2d0b4f3a4acb0`. Artifacts are at [`formal-03/raw.json`](formal-03/raw.json) and [`formal-03/summary.json`](formal-03/summary.json), reflecting the frozen `/out/formal-03` argument under host mount `results/formal-03/`. `AUDIT_SUMMARY.json` retains the independent reconstruction.

## Scope limits

All states, feedback loss, sequence staleness, and mappings are synthetic stipulated inputs. This does not analyze actual Agent Interface controllers, establish STPA completeness, estimate a hazard rate, validate real delivery/sequence contracts, demonstrate a production guard, or prove safety. T1/live application fault injection remains unauthorized by this T0.
