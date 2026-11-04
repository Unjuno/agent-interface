# Retired-owner terminal generation handoff — A01

## Claim

On current main `122309750ab28b510a3505dd1540f75e7da041bf`, the process-identity backend's normal terminal emitter did not attach the current input-owner generation and owner ID, although the controller's retired-owner rotation path requires both fields to authenticate a cancellation terminal. A canceled stale cover could therefore reach the owner-rotation helper without the metadata that its generation checks require.

## Evidence and source boundary

The retained `map01-v39-current-main-threat-live-20261024-r02` trace contains an earlier `cover-1` terminal with `status=cancelled`, verified empty X-server keymap, `target_focus_query_failed=true`, and a retired/dead process-identity reader. The next `plan-1-primary-0-0` terminal is `needs_decision`, zero steps, verified empty X-server keymap, the same failed focus query and retired reader, with `interruption=null` and `decision_reason=null`.

The preregistered repository commit is `26c383a983782be25d6a1ae33814f7c551d88d63`; the retained runtime-source manifest expects controller SHA-256 `e4c74a587cd5db3577d402162a9a3943f6b7bb2a04e3207abe9da82d2ee1d81e`. That is not the current-main controller source. The raw `controller-failure.json` records only `RuntimeError` at `active_action_execution`, so the exact historic exception cause remains unknown. This result does not attribute the old run's failure to the metadata omission.

Current-main source review showed:

- `doom_process_identity_backend_v1.Backend._emit_identity` attached `input_owner_generation` only to observation events, not terminal events.
- `executor_v13` emits terminal events without owner generation or owner ID.
- `map01_overlap_controller_v39.rotate_retired_owner_after_cancel` rejects terminals without those two fields, and the current controller calls it after a canceled invalidated action when the target identity reader has retired.
- Existing rotation tests manually supplied both terminal fields, leaving backend-to-controller propagation uncovered.

The retained traces establish X-server release only; they do not establish physical Windows input release or game consumption.

## Change and minimum test

For the internal process-identity owner path, terminal emission now binds the event to the backend's current generation and owner ID. The new regression starts with a terminal containing a deliberately stale generation, passes it through the backend emitter, then passes the emitted event to the actual controller rotation helper. The helper rotates once and accepts only a fresh higher-sequence process-bound observation plus a matching no-authority source-refresh receipt.

## Result

- Focused regression: 1/1 passed under Python 3.11.9 normally and under `-O`.
- Full `research/doom/test_map01_overlap_controller_v39.py`: 25/25 passed normally and 25/25 under `-O`.
- `git diff --check`: passed.

## Decision and limits

Construction PASS for current-main backend terminal metadata flowing into the existing bounded owner-rotation and fresh-source-refresh contract. This closes a source/test seam; it is not a live X11, Docker, WSLc, provider, physical-input, MAP01 task-effect, threat-policy, or MAP01-clear result. The old r02 failure remains failed/unfinished evidence. A newly preregistered eligible runtime allocation is still needed to determine whether this repair produces finite recovery under the live target conditions.
