# Adaptive acquisition caller v3: local-first semantic repair

Current-source navigation (2026-10-16): the [caller convergence crosswalk](../integration/caller_current_main_convergence_20261016/README.md)
records the already-composed #7289/#7310 repair family, later effect receipts,
76 selected normal/-O local methods and the remaining live provider/task-effect
gates. The original evidence count below is historical, not the current total.

The [persistent grounding failure-accounting repair](../integration/grounding_failure_accounting_20261016/README.md)
also tests the actual model/planner/caller boundary with an inert RPC client:
known failed-call accounting survives before the caller skips input/effect stages.
This does not qualify live provider usage or independent application effects.

The added [JSONL transport composition regression](test_grounding_appserver_usage_transport.py)
uses the real `CodexAppServerClient` against a deterministic local protocol peer.
It verifies that a failed completed turn's thread ID, turn/call ID and token usage
survive into the adaptive caller's all-attempt ledger and match the retained
protocol journal. The peer is synthetic: this checks transport-to-ledger
plumbing, not provider billing, provider-log reconciliation, or task effects.

The [explicit compiled v3 connection](COMPILED_CALLER_V3.md) builds from the final
selected target and retains a returned core receipt across auxiliary sink
failure. Trusted execute adapters can use `ExecutionReceiptError` with a
validated detached decision; ordinary error attributes do not grant progress
evidence. The caller records known delivery without promoting task success.

## Problem

The retained matched v3 comparison established one narrow case in which a
cached target handle could repair a semantic region after a Chromium width
change. The shared v2 caller could account for model repair, but it moved from a
failed warm revalidation directly to model reacquisition. It could not express
the measured local route, require a later observation after repair inference,
or aggregate model-visible images and model wait separately.

## Contract

`adaptive_acquisition_caller_v3.py` versions that boundary. A reuse request
declares separate `local_repair_on` and `repair_on` reason sets. The caller tries
at most one local repair for an eligible invalidation. A successful repair must
return an exact no-authority result and report zero model calls. A configured
`missing`, `ambiguous`, or `association_changed` result may fall back to one
accounted model reacquisition. Unconfigured outcomes stop without input.

After repair inference, the caller obtains one passive exact observation. Its
post-model receipt must bind the completed call ID and a strictly later source
and current sequence, current capture clock, and current pointer binding. A
changed or malformed receipt stops before ordinary final revalidation and
execution. Neither local repair nor this receipt grants semantic or input
authority.

An optional target returned by successful final revalidation is promoted as the
selected target and cache update before execution. This removes the prior need
for live adapters to smuggle newly minted handles through an external variable.
Stop results cannot expose a target, and a null revalidated target fails closed.
The result retains the ordered statuses from reuse, local repair, model
reacquisition and post-model revalidation so a later success cannot erase why
the fallback was entered.

The attempt ledger records provider thread and turn/call identity, provider
usage, visible images submitted and model wait for completed and failed attempts
when available. Older adapters may omit thread identity. Coverage is
reported independently; missing values remain unavailable rather than becoming
zero. A typed upstream capacity refusal becomes `TASK_DEFERRED` rather than a
generic caller failure, while failed upstream and malformed output remain
`CALLER_FAILED`. V2's typed partial execution, comparison classes, duplicate call IDs and
input-consumption semantics remain.

## Offline evidence

Twelve direct tests and a separately audited retained report cover cold accounting,
unchanged reuse, zero-call local repair, `missing`/`ambiguous`/changed-evidence model
fallback, unconfigured refusal, changed post-model evidence, same-frame receipt
rejection, authority escalation, failed-call accounting and typed partial
execution. Windows and WSL execute the same checks. This block makes zero fresh
model and GUI calls.

## Limits and next test

This is branch and accounting integration. The matched Chromium v3 run motivates
the local route but does not make these test doubles new efficacy evidence. The
next finite live use should pass through this exact caller, exercise a natural
local repair and a changed-evidence fallback, retain all attempts, and score task
effects independently. A failed idea remains eligible for a new test only when
the changed condition and failure discriminator are declared before execution.
