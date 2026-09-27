# Successor to #3924 — OrbStack host-broker exit and receipt contract

## H — hypothesis

On current main, a deterministic fake child returning 0 is written to the
broker receipt as returncode 0, but the one-shot broker process returns 1 due
to `broker.get("returncode") or 1`. Nonzero child codes should propagate
exactly; timeout/unavailable cases should be typed and fail closed. `--once`
should process at most one sorted eligible request.

The predecessor #3924 allocation did not invoke the fake child: the formal
container mounted the checkout at `/repo` but omitted the frozen `/study`
mount. Preserve that STOP and its raw files unchanged. This successor adds a
mount-presence/hash/executable preflight before any formal case.

## T — frozen one-shot treatment

- Issue intake main: `a718da028d33c9608433789676ddd7204d8c5d14`; refreshed
  immediately before formal freeze to `67f1aedace0039d2ab8e4550becfaea78c50653c`.
  The branch is based on that refreshed main, and both frozen source/test Git
  blobs are unchanged.
- Broker: `runtime/host_model_ipc_broker_v1.py`, Git blob
  `f307daafdfd36d1ab4faf39bb36c36350e6e67e4`, SHA-256
  `034b2e72a28fc3defb1b48195a2a8d3450e850895a4b3b7b7919dca44e198775`.
- Existing contract test: `runtime/test_host_model_ipc_broker_v1.py`, Git blob
  `e645ae575cd6fdae02556df9facc9919739584f3`, SHA-256
  `a28b59232e55956a11bd87a35812b7d77df16febe5510c68fb80eda03a3ede1c`.
- Engine: OrbStack 29.4.0, Linux arm64; image `python:3.12-slim`, pinned
  local ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
- Fresh network-none container; root read-only; full source checkout mounted
  read-only at `/repo`; this study directory separately mounted read-only at
  `/study`; only a unique allocation output directory mounted writable at
  `/evidence`. CPU 1, memory and swap 256 MiB, PID limit 32, all capabilities
  dropped, no-new-privileges, bounded noexec/nosuid tmpfs. Do not forward host
  environment, credentials, model/provider endpoints, GUI, or input authority.
- Before formal start, in the actual formal image and exact mounts, assert
  `/study/fake_codex.py` exists, is executable, and matches its frozen SHA;
  assert the current broker and test source hashes match FREEZE. Failure is a
  pre-case STOP with case count 0.
- Exactly one formal container invocation with seven rows: exit0, exit23,
  timeout, unavailable, malformed request, `--once` with no request under an
  external 300 ms bound, and two queued requests. Retain raw requests,
  responses, receipts, fake argv/stdin/stdout/stderr, process statuses, image
  identity, and SHA-256 manifest.
- Run the independent raw-only auditor once in a second fresh container with
  same isolation and pinned image. No formal retries or post-result tuning.

## D — decision

- `FAIL_ZERO_EXIT_PROPAGATION` if the fake exit0 receipt records 0 while the
  broker process exits nonzero.
- Other required behavior: exit23 propagates exactly; timeout and unavailable
  are typed and non-successful; malformed request fails closed; no-request
  `--once` is externally bounded with no receipt; two queued requests yield
  exactly one response/receipt/fake invocation for the lexicographically first
  ID; request, response and receipt IDs reconcile; independent audit errors=0.
- `PASS_BROKER_EXIT_CONTRACT` only if every required behavior holds and all
  source, process, container and audit provenance is complete.
- Any source/image/mount/runtime/provenance/audit failure is a typed STOP, not
  a scientific result. Preserve the failed output; do not rerun this allocation.

## C — constraints

Fake child only. No real Codex/model/provider calls, secrets, GUI, task input,
seed or shared source edits. Additive branch/path only. The #3924 predecessor
STOP/PR/main record remains immutable.

## U — limits

This allocation only tests deterministic host broker process/receipt behavior
on one OrbStack Linux/arm64 configuration. It does not validate model utility,
GUI/task success, efficiency, Docker Desktop equivalence, or product claims.
