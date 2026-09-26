# Docker Desktop host-broker exit/receipt contract — preregistration

Parent: [Issue #3924](https://github.com/Unjuno/agent-interface/issues/3924). This is a Docker Desktop Linux/amd64 cross-engine successor; it does not alter or supersede the OrbStack allocation.

## H / Hypothesis

On the exact current-main broker source, a deterministic fake child that exits 0 will produce a broker receipt with `returncode: 0` while the broker process exits 1 because the one-shot path evaluates `broker.get("returncode") or 1`. Child exit 23 should propagate as 23. Timeout and missing-executable outcomes should remain typed and non-successful, malformed requests should fail before a receipt, no-request mode should remain bounded by the harness, and one-shot mode should process only the first of two lexically ordered requests.

## T / Test

Freeze current `main`, broker/test source bytes, test/audit/fake program bytes and the cached image before formal execution. First make only one construction invocation to establish that the fake-only harness runs inside Docker Desktop without real Codex/model/provider access. Freeze the final harness after that construction and run the characterization suite exactly once in a fresh Linux/amd64 container. Capture per-case request bytes, child argv/stdin/stdout/stderr, broker receipt/response, exit status, and hashes. In a second fresh no-network container, independently re-read the raw bundle, verify its complete inventory/digests and recompute the seven case classifications without importing the test runner.

Cases are fixed and ordered: exit 0; exit 23; 100 ms broker timeout with a 1 s fake child; unavailable executable; malformed request JSON; no-request bounded idle (observe 200 ms, then terminate only this test child); two requests in `--once` mode. The bounded `/tmp` tmpfs is explicitly executable because it contains only the generated deterministic fake executable; the container root and source remain read-only. Docker limits are fixed at 1 CPU, 256 MiB memory, 64 PIDs and 32 MiB tmpfs. No retries or parameter adjustment after formal execution.

## D / Decision

- The predicted defect is `FAIL_ZERO_EXIT_PROPAGATION` if child and receipt both report 0 while the broker process returns nonzero.
- Exit 23 must be preserved exactly; timeout/unavailable must have their specified typed receipts and nonzero broker exits; malformed JSON must produce no response/receipt; the no-request child must produce no artifacts during the bounded observation; one-shot must produce exactly one response for request A and none for request B.
- Independent raw audit must verify every source/input/output hash and reproduce every case classification with zero audit errors. A behavioral mismatch outside the predicted defect is a separate FAIL; source/image mismatch is STOP before the run; infrastructure or missing evidence is HOLD/STOP.
- The experiment records the behavior only. It does not change production broker code.

## C / Constraints

Base: `a7a6cdd7a2a260f008128a8b216159244b048b5d` (fast-forwarded from the initial `a0f0ca37c88ad46f3f98485483453cedbe432723` freeze on 2026-09-26; source content remains unchanged). Authoritative Git tree blobs at this base: broker `f307daafdfd36d1ab4faf39bb36c36350e6e67e4`; existing unit-test `e645ae575cd6fdae02556df9facc9919739584f3`. Windows checkout byte SHA-256 values (the bytes bind-mounted into the container) are broker `034b2e72a28fc3defb1b48195a2a8d3450e850895a4b3b7b7919dca44e198775`; test `a28b59232e55956a11bd87a35812b7d77df16febe5510c68fb80eda03a3ede1c`. Docker Desktop Engine `28.5.1 linux/x86_64`; cached `python:3.12-slim`, `linux/amd64`, image ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`. Formal containers use `--pull=never --platform linux/amd64 --network none --read-only`, read-only source, one writable evidence mount, bounded `exec` tmpfs/CPU/memory/PIDs, all capabilities dropped, and no-new-privileges. No real Codex executable, credentials, model/provider, GUI, game, input, or production-source edit.

Additive branch: `research/issue-3924-dockerdesktop-broker-contract-v1`. Additive path: `research/integration/host_broker_exit_contract_dockerdesktop_v1/`. Formal outputs are frozen at `formal/dockerdesktop-20260926-01/`: raw case records under `raw/`, host Docker stdout/inspection at the formal directory root, and the separate independent audit under `audit/`. Invoke the formal suite once and the independent audit once using `run_experiment.ps1`; their full command arrays are retained in `formal_run.json` and `audit_run.json`. The formal result directory must be absent before invocation.

## U / Scope

This characterizes only the fake-process exit/receipt contract for this pinned source and one Docker Desktop Linux/amd64 engine configuration. It is not a real model/IPC/task-effect result, arbitrary subprocess-safety proof, or OrbStack equivalence claim.
