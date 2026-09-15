# Adaptive acquisition caller v3: local-first semantic repair

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

The attempt ledger records provider usage, visible images submitted and
model wait for completed and failed attempts when available. Coverage is
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
