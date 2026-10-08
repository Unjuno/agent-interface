# Issue #5269 — mandatory verification-plan coverage boundary

## Intake and collision check

- Repository: `Unjuno/agent-interface`; branch `research/verification-coverage-5269-v1-20260930`.
- Frozen base/current `main`: `972fd822dd75dba7def4d0601d6b96830903d184`.
- #5269 is open; no #5269 branch was returned by GitHub branch search. No matching open PR was found in intake (PR #5290 is a merged parent-IR delivery, not a #5269 PR).
- Parent #5268's IR/oracle experiment is already merged and is consumed as immutable input; it is not rerun or relabeled.
- Open parallel #5266 owns risk-tier escalation and #5273 owns verifier capability/latency/cost registry. This study does not implement either child.
- Root ROADMAP still names 2026-09-19 desktop integration as priority while canonical `docs/CURRENT_GOAL.md` r133 directs posthoc MAP01 reconstruction; the mismatch remains unmodified. The repository-wide roadmap remains open.

## H / T / D / C / U

**H.** Given the frozen deterministic mandatory IR for each action, a small authority-neutral coverage gate can preserve every non-OPTIONAL check, reject any omission/downgrade/contract change, permit optional residual checks, and reject a selected verifier whose supplied finite latency bound exceeds a non-null check deadline.

**T.** One finite no-model/no-task/no-GUI construction allocation over all 10 parent #5268 Agent Action cases. First compare generated policy rows to the parent's separately authored literal oracle. Then execute all complete plans, omit each non-OPTIONAL row individually, and run named corruptions: downgrade, wrong subject, wrong evidence role, wrong intent generation, deadline-infeasible optional verifier, semantic duplicate, unknown primitive, and removal of both external-side-effect safeguards. Check optional omission/addition. Keep the parent inputs byte-identical. A separate auditor imports neither the candidate policy nor the new coverage validator.

**D.** All complete/valid proposals must be accepted; every generated omission and corruption above must be rejected; each policy's check tuples must match the parent oracle; accepted results may only state plan coverage and may not claim authority/currentness/effect truth. The new validator must be deterministic and the audit must recompute all decisions. Report the finite counts and exact scope. **Overall #5269 PASS is additionally gated on high-risk mandatory escalation being representable/testable.** If frozen v0.1 lacks that concept, preserve the measured finite boundary as `HOLD_UNREPRESENTED_RISK_ESCALATION`; do not invent a primitive or close #5269.

**C.** The 10 hand-built cases/oracle may share favorable omissions; check-row consistency is not real task correctness. A supplied verifier bound may be an inaccurate estimate. The external-side-effect case is only a high-consequence proxy, not an independently labeled #5266 risk tier; no escalation primitive is in the frozen IR.

**U.** Synthetic finite contract behavior only. No live task, learned router, model call, GUI/input, verifier execution, authenticated registry/SLA, measured latency, action authority/currentness/effect truth, or cross-domain evidence. The supplied `upper_bound_ms` is a test fixture—not an observed or registered latency envelope. The experiment cannot establish full #5269 H/D while high-risk escalation remains unrepresented.

## Frozen execution

- Allocation: `verification-coverage-5269-v01-20260930-01`.
- Parent allocation: `verification-ir-5268-v01-20260930-01`; input SHA-256 values are in `FREEZE.json` and raw output.
- Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (Linux/arm64, CPython 3.12.14).
- Container: no network, 1 CPU, 512 MiB, 128 PID limit, read-only root, 32 MiB no-exec `/tmp`; only the allocation output mount is writable.
- Formal and audit invocations are each one-shot. Launcher refuses if an output already exists; no retries, model, GUI, external services, or task input.
- Exact argv, timestamps, streams, exit codes, source hashes, raw hashes and audit hashes are retained in `results/formal-01/`.
