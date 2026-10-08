# Issue #5895 — strict runner-completion semantics T6 (Linux/amd64)

Allocation: `AUDIT-COMPLETION-5895-T6-AMD64-20261001-01-8d0c7f53`
Owner: Codex thread `01a0b98b-8d0c-7f53-92bc-4c6a28d73c73`, local macOS ARM64 OrbStack context `orbstack` only; guest container platform **linux/amd64**.
Reservation: #5085 comment 5931167730; Issue registration: #5895 comment 5931175249.
Preparation main: `722c42bf0d6d808cf80575ecb6353401de934b26` (fast-forwarded at 2026-10-01 12:36 UTC before candidate).
Target: open PR #5630 head `288d0498d11cf16657e523a04616bf4f49cd94f4`, exact blobs/bytes in `FREEZE.json`.

## H / T / D / C / U

**H.** The frozen synthetic CLI auditor (PR #5630 `target/audit_formal_x11.py`, lines 234–235) filters `runner_complete` rows with Python `exit_code == 0` before cardinality validation. It therefore accepts Boolean `false`, float `0.0`, and a success accompanied by a failing completion row. Null, string `"0"`, missing exit code, and duplicate success are rejected.

**T.** In the reserved bounded OrbStack allocation on a pinned **Linux/amd64** Python image, run one candidate emitting eight fixed cases: integer-zero control, Boolean false, float zero, null, string zero, missing code, duplicate success, and success-plus-failure. Only if candidate exits 0, run one separate raw-only independent auditor in a second network-disabled container. The candidate output mount is the initially-empty `results/formal-t6-01/output/`; all CID/stdout/stderr/inspect receipts stay outside it in `results/formal-t6-01-host/`. Check exact digest and the AMD64 platform-specific image ID before launch; no substitution or retry.

**D.** Expected target exits: `[0,0,0,1,1,1,1,0]`. `METHOD_REPRODUCED_SCOPED` requires that exact vector; exact target Git blobs/SHA-256 and allocation/source/image identity; all mutation and unchanged baseline rows; complete artifact hashes; and independent audit `PASS_INDEPENDENT_RAW_AUDIT` with errors empty. Candidate mismatch is retained without tuning. Any failed pre-candidate gate is `STOP_NOT_EVALUATED`, not scientific FAIL.

**C.** Exactly the Issue's synthetic CLI boundary: one deterministic JSONL auditor boundary in one pinned **Linux/amd64** Python container. No model/provider, X11, GUI/input, game, GPU, network, runtime authority, or task effect. Candidate and auditor are separate one-shot containers, each one CPU, 512 MiB RAM, 64 PIDs, network none, source read-only.

**U.** No formal X11 provenance, physical key-up timing, keymap state, MAP01 occupancy, safety, efficacy, latency, or Issue #59 completion claim.

## Allocation and predecessor

Window: 2026-10-01 12:35–12:55 UTC. Candidate 1, auditor 1 conditional on candidate exit 0, retry 0. T3/T4 STOPs remain unchanged. T5 is a terminal pre-candidate scope STOP because its ARM64 preregistration contradicted Issue #5895's Linux/amd64 C-boundary; its exact record is copied unchanged to `predecessors/T5-STOP.md`. At 12:35, re-read #5085, #5895, PR #5630, latest main, exact owner, OrbStack context/container inventory, pinned digest plus AMD64 image ID, target hashes, receipts path, and unique empty output. If image/platform, queue, owner, or any resource gate fails, STOP before candidate.
