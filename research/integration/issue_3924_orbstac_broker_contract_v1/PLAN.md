# Issue #3924 OrbStack host-broker contract

## H — hypothesis

In the current-main `runtime/host_model_ipc_broker_v1.py`, a successful fake
child exit code 0 is written to the receipt and response, but `--once` returns
1 because `broker.get("returncode") or 1` coerces zero to one. Nonzero child
codes should propagate unchanged; timeout and unavailable-executable outcomes
should remain typed, nonzero, and fail closed.

## T — frozen treatment

- Repository: `Unjuno/agent-interface`, branch based on current `main` at
  `c83ddb057c680a126144d000bf7ef7ba2274652a`.
- Source under test: `runtime/host_model_ipc_broker_v1.py`, Git blob
  `f307daafdfd36d1ab4faf39bb36c36350e6e67e4`.
- Adjacent existing tests: `runtime/test_host_model_ipc_broker_v1.py`, Git blob
  `e645ae575cd6fdae02556df9facc9919739584f3`.
- Container engine: OrbStack 29.4.0, Linux aarch64.
- Container image: `python:3.12-slim`, local immutable image ID
  `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`
  (local architecture `linux/arm64`).
- The deterministic fake executable is the only child process. It creates
  response receipts recording argv/stdin/stdout/stderr and returns predefined
  statuses. No real `codex` binary, credentials, provider, GUI, or host authority.
- Formal fixed case matrix: exit 0, exit 23, bounded timeout, executable
  unavailable, malformed request, one-shot no-request bounded idle, and two
  queued requests in `--once` mode. Capture request/response bytes, receipts,
  fake invocation records, container exit status, image/source identities, and
  hashes. Source/fake mount read-only, evidence mount writable, network none,
  read-only root, bounded tmpfs/CPU/memory/PIDs, all capabilities dropped,
  no-new-privileges.
- An independent audit process/container will classify only from retained raw
  IPC, fake invocation records, process statuses, and recomputed hashes.

## D — decision

- `FAIL_ZERO_EXIT_PROPAGATION` if child and receipt record 0 but the broker
  exits nonzero.
- `PASS_BROKER_EXIT_CONTRACT` requires exact success/nonzero propagation,
  typed non-success timeout/unavailable results, exact request/response/receipt
  ID reconciliation, one-shot processing bounded to one eligible request,
  complete raw provenance, and independent audit with zero errors.
- Any source/image/runtime/network/provenance/audit infrastructure failure is a
  typed `STOP` or `HOLD`, never scientific PASS/FAIL. Preserve partial outputs;
  do not retry a formal case after a gate failure.

## C — constraints

No real model/provider call, GUI action, host input authority, credentials, or
seed allocation. No production source edits. All work is additive under this
directory. The predecessor allocation in #3898 and reservation/STOP branch for
#3924 are immutable.

## U — limits

This tests deterministic host broker process/receipt semantics only. It does
not test model utility, GUI/task correctness, #3898's efficiency hypothesis,
or equivalence with Docker Desktop.

## Freeze record

The exact file hashes, runner hash, environment, and preregistration digest are
recorded in `FREEZE.json` before formal invocation. Construction checks do not
count as formal cases.
