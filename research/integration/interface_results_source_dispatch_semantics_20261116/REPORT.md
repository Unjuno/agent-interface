# Exact-result source dispatch projection

## Finding

A supervised Win32 `interface_results` response marks the lookup itself as not dispatching input. The retained source action is nested separately and can record `action.input_dispatched=true`. Consumers that read only the response-level field can confuse a read-only lookup with the source action's delivery history. The R193 retained response exhibited this shape; its source outcome remains UNKNOWN, and this projection does not promote task success.

## Change

The exact-result response keeps the existing `input_dispatched=false` compatibility field and adds two explicit fields:

- `query_input_dispatched=false` describes the read-only lookup.
- `source_action_input_dispatched` copies a known Boolean from the retained action and is null when that action has no Boolean receipt.

The source action remains available unchanged under `action`. Task success and replay gates are unchanged.

## Verification

Final-source focused public-caller tests cover both a source action that dispatched input and an expired start gate that dispatched none. They passed 2/2 under CPython 3.11.9 in normal and optimized modes. Exact stdout/stderr transcripts, source hashes, and conditions are in this directory.

During exploratory broader module runs, the existing mid-program expiry stdio case varied with scheduling: the dispatch envelope could be captured as `unknown` or after the same bounded recovery had already completed as `recovered`. Both paths retained `task_success=null` and `replay_allowed=false`; the final reported test set therefore sticks to deterministic projection and zero-dispatch checks and does not claim a clean full-module pass.

## Limits

This clarifies result interpretation and preserves the source delivery fact. It does not establish native GUI task success, MAP01 effect, reliability, or the #57 matched-efficiency comparison.
