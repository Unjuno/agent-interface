# Issue #5895 T4 — frozen synthetic completion-semantics experiment

## Allocation / scope

Allocation: `AUDIT-COMPLETION-5895-T4-ORBSTACK-20261001-01-8d0c7f53`. Exclusive owner is Codex thread `01a0b98b-8d0c-7f53-92bc-4c6a28d73c73`, this local macOS ARM64 OrbStack host, 2026-10-01 10:30–10:50 UTC. This T4 is distinct from terminal T3 and all earlier attempts. Do not execute candidate outside the exact slot or after any start-gate mismatch.

## H — hypothesis

In the exact synthetic CLI auditor frozen at PR #5630 head `288d0498d11cf16657e523a04616bf4f49cd94f4`, selecting `runner_complete` rows using `exit_code == 0` before cardinality validation accepts Boolean `false`, float `0.0`, and one success accompanied by a failing completion row. Null, string `"0"`, missing exit code, and duplicate success are rejected.

## T — test/treatment

Refresh Issue #5085 queue, exact task/host owner, current main, PR #5630 head and all three frozen source identities; inspect OrbStack nonterminal/running inventory; verify exact pinned local image/platform; verify the candidate `/out` directory is absent/empty. Candidate is one invocation in a bounded `--network=none`, read-only-source, 1 CPU/512 MiB/64 PID, no-capability Linux/arm64 container. Run the eight isolated raw JSONL cases in order: pristine integer-zero; Boolean false; float zero; null; string zero; missing exit code; duplicate success; success plus failure. Expected exits: `[0,0,0,1,1,1,1,0]`. Preserve stdout/stderr and container IDs outside `/out`.

Only if the single candidate container exits 0, invoke a separate bounded network-disabled container exactly once for the independent raw-only auditor against the candidate manifest and `/out`. Never retry. Any STOP, candidate nonzero, or artifact mismatch ends the allocation with no auditor invocation. Preserve source/image identity, exact command, container inspect, raw JSONL, every audit/stdout/stderr/exit, hashes, and deviations.

## D — decision

Scoped PASS only if all eight exits match, the independent auditor validates source/fixture identity, exact mutation rows, unchanged non-completion evidence, complete output inventory and hashes, and the declared target status/predicate. Otherwise retain `FAIL_CONSTRUCTION` if execution is valid but a case or audit is wrong. Missing grant, owner, host/context, source, image, empty-output, or container-inventory evidence is `STOP` / `NOT_EVALUATED`, not a scientific FAIL. Candidate nonzero means no auditor and no retry.

## C — controls and limits

One synthetic JSONL CLI, one Linux/arm64 pinned Python image, no network. The success-plus-failure row is an independent control for completeness, in addition to the malformed typed-zero cases. The container is not an X server, GUI, input, model/provider, game, GPU or live task. The audit independently reads raw artifacts and does not call the candidate target.

## U — uncertainty

This tests only one synthetic completion-record boundary. It does not validate PR #5630's formal X11 provenance boundary, physical key-up timing, keymap state, MAP01 occupancy, safety, efficacy, latency, or Issue #59 completion. Preserve T3's pre-populated-output STOP unchanged. If the 10:30 start gate detects any unowned active container or other discrepancy, do not proceed.

## Frozen identities at preparation

- Current main at initial T4 worktree creation: `c7346fe1ad0c0d40254c6aa7898a8ed6de76c0dc` (refresh at slot start).
- PR #5630 head: `288d0498d11cf16657e523a04616bf4f49cd94f4` (refresh at slot start).
- Read-only source checkout ref: `origin/research/5895-auditor-completion-gate-prep-20261001`, commit `7a969fb26e36879ca467e8d17db4b60fa2338bb0`.
- `target/audit_formal_x11.py`: Git blob `da805fb83f70a57ad68a0768186e214524689d40`, SHA-256 `f74da3f66fa979db99c17213df31d295056b99ae04c8d8b59bd6d5b5d71a93e0`.
- `target/EXPECTED.json`: Git blob `3d33bda096c4c8789e183e3f864ee7626e643a7e`, SHA-256 `7bf403b88773ecdfd04243f023c17e26e859c3286b71ccf5eb2db3101e0ef076`.
- `target/test_audit_formal_x11.py`: Git blob `d1eb9a854cc810fa77ca173d7e2de287ee1bd64a`, SHA-256 `1fbb4b86fec10ad8ed578efa476df1857d38e82617d802ff8e0252ff848163f5`.
- Candidate implementation freeze: `matrix.py` SHA-256 `ffc2ce99a2605b08a6de5f989e8fda3a42af4e8db1915be4e547e7f23fce5162`; `run_candidate.py` SHA-256 `59981d7bd7574389e20755d1e131e379b5b64ce929da66f6e971484255a56738`; `independent_audit.py` SHA-256 `1c7e07b92b3d76e0ded94a186bd43324e401d537a17232fd6a7aae91d6c88fd8`.
- Frozen target mount: `/private/tmp/agent-interface-5895-pr5630-source/research/live_control/auditor_completion_gate_5630_t0_5895_v1/target` from the read-only source worktree commit above.
- Required image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, linux/arm64; read-only preflight found exact local image. Recheck at start.

Preparation is not candidate execution. T3's STOP and source mismatch in its allocation are not reinterpreted or reused.
