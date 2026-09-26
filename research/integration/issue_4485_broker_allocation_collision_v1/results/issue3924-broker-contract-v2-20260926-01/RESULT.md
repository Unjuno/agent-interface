# Issue #4485 — formal result

Allocation: `issue3924-orbstac-broker-contract-v2-20260926-01`

Decision: **`FAIL_ZERO_EXIT_PROPAGATION`** (primary hypothesis); **timeout subgate incomplete**.

Source base: `21dd6a26dbd9f5cb4a6e11b1060902799a76a733`.

One OrbStack formal container completed the seven planned rows after an in-container source/fake-executable preflight. An independent raw-only audit ran once in a separate isolated container. Formal raw SHA-256: `d149992af141530fe97a54821e7694879d4f6745bf6e0ad982a8bca728dacad2`.

## Observed gates

| Case | Observation | Gate |
|---|---|---|
| fake exit 0 | broker receipt records child `returncode=0`; `--once` process exits `1` | **FAIL_ZERO_EXIT_PROPAGATION** |
| fake exit 23 | receipt and broker process both return `23` | pass |
| internal timeout | outer 300 ms watchdog fired at 303.3 ms; no broker receipt; fake was invoked | **incomplete**, not evidence that the broker typed the timeout |
| executable unavailable | `FileNotFoundError`, `HOST_BROKER_EXECUTABLE_UNAVAILABLE`, process exits `1` | pass |
| malformed request | process exits `1`, no receipt or fake invocation | pass |
| idle `--once` | outer 300 ms watchdog fired at 306.0 ms, no receipt | bounded nontermination observed |
| two queued IDs | only lexical-first `a-first` has response/receipt and one fake invocation | pass |

The raw-only audit reported 9/11 checks true; its two errors are zero-exit propagation and typed internal timeout. The primary failure is directly established by a valid receipt plus the broker's process status. The timeout case did not reach the preregistered internal timeout receipt, so the full seven-case acceptance matrix is not claimed. The raw allocation is consumed; no retry, tuning, or relabeling was performed.

## Provenance and scope

OrbStack 29.4.0, Linux/arm64. Image `python:3.12-slim` resolved before execution to `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9` (`python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`). The formal invocation used network-none, read-only root, 1 CPU, 512 MiB memory/swap, 64 PIDs, all capabilities dropped, no-new-privileges, bounded `/tmp`, read-only checkout/study mounts, and a dedicated evidence mount. The separate audit container used the same isolation with 1 CPU, 256 MiB memory/swap, and 32 PIDs.

The executed broker and existing test sources match the issue-frozen Git blobs and SHA-256 values recorded in `PREREG.md`; fake executable SHA-256 is `c9855dcc434b3bd52c9d1a5d35d0fadb72f338d2e7fefde11499f91ed849c64a`. No source/runtime code was changed. Local broker tests passed 4/4 before formal execution. This establishes only the bounded OrbStack broker contract; no model, provider, GUI, user input, task effect, Docker Desktop equivalence, or product claim follows.

The 300 ms outer watchdog was too close to the internal 200 ms timeout under this run's scheduling latency. This is retained as a protocol adequacy limitation, not repaired post hoc. Any follow-up requires a distinct successor allocation.
