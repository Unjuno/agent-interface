# H/T/D/C/U — auxiliary Codex event accounting

Date: 2026-09-21. GitHub issue: [#2849](https://github.com/Unjuno/agent-interface/issues/2849), preregistration comment 5751235773.

## H — Hypothesis

A host Codex JSONL stream may contain a completed, known skills-context-budget warning item in addition to one completed assistant message and one usage-bearing completed turn. Counting all completed items as assistant messages incorrectly rejects a valid schema preflight. A successor runner can classify and retain this known warning while counting only assistant messages, with fail-closed behavior for unknown events.

## T — Target

First exercise the archived PR #3685 failure stream and positive/negative mutations in OrbStack. If every control passes, perform exactly one fresh plain/no-image preflight through the explicitly selected Docker backend. No compiled schema, image, GUI, six-task allocation, or retry.

## D — Design

- Additive candidate at `research/live_control/issue_2849_runner_aux_event_v2_v1/event_accounting.py`; do not modify shared v1 runner.
- Count only `item.completed` rows whose item type is `agent_message`; permit only the exact previously observed warning text as a classified auxiliary error, retaining its type and SHA-256.
- Require one assistant message, one `turn.completed` with nonempty nonnegative integer usage, valid JSON object output; reject unknown event shapes and failures.
- Controls: archived real warning+message stream; unknown auxiliary error; duplicate assistant message; missing turn; missing usage; turn failure; malformed JSONL; warning text mismatch.
- Fresh call uses source backend/broker and schema/instructions from PR #3647 head `6a942ea04bfea1d196d19719ec59a9bdad720826`; candidate runner, OrbStack Linux/arm64, image `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, network disabled, read-only root, no image and no task authority.
- Independent schema audit runs offline in the pinned OrbStack audit image. Preserve request, raw stream, broker, process and classification receipts.

## C — Constraints

One fresh model call total, no retries. Candidate test and preflight do not establish GUI/task effects, six-task allocation, or semantic correctness. Historical PASS/FAIL artifacts remain immutable. Containers use `--tmpfs /tmp` when the root filesystem is read-only; an initial test invocation lacking that mount failed environmentally before tests could run and was not model work.

## U — Update / stop policy

Any failed control stops before model invocation. Any malformed/missing/ambiguous receipt or failed independent schema check is FAIL/STOP and remains recorded without retry. PASS is limited to this plain schema compatibility preflight.

## Baseline and duplicate check

The observed main base is `b04e93dd2e1fb610ed8761a9a91590fe69a7683b`. Existing issues #2817 and #2849 contain the matching schema-preflight/IPC scope; no new issue was opened. Open PRs #3647 and #3679 were inspected; neither owns this additive path or the auxiliary completed-item count. Candidate path is distinct from both.
