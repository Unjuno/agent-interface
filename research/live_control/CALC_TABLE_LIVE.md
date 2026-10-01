# Calc live transport and modal recovery

A new explicit socket entry, cause_servo_socket_v2, routes Calc or Inkscape to cause_servo_interactive_v2 with executor v6. Existing defaults and frozen entries remain unchanged. The new manual stage client returns the full v4 receipt plus lossless input state table.

## Actual self-use, seed 225

One familiar blank Calc sheet required A1=816, A2=345, saved as Excel format. The assistant used the private socket, read the stage receipts/state companions and viewed images. Initial numeric entry was chosen from the ready task and submitted in the same tool call that returned the initial image; subsequent save, inspection and confirmation decisions followed viewed screenshots. This is not a blind task.

- Enter: five steps completed; screenshot shows the two correct values.
- Save: Control+s opens the format dialog. Natural focus change causes needs_decision/focus_changed, zero completed steps, verified release, no settle tail. The returned image is partially painted.
- Inspect: a new observe program completes without stale cause and shows the full dialog with Excel format selected.
- Confirm: Return closes the dialog. Natural focus change again causes needs_decision/focus_changed, zero completed steps and verified release. The image still contains old dialog pixels.
- Verify: a fresh observe completes without stale cause. Screenshot shows the values, no dialog, and cleared modified indicator. GUI-only success prediction was hashed into a clock command before independent evaluation.
- Finish: saved workbook independently contains [816,345], success true. Bridge process exited 0.

Separate audit verifies all 72 raw events across 13 socket exchanges, source hashes, regenerated receipts, exact state-table round trips, both distinct interruption tokens and their owner records, pre-score GUI commitment, 14 PNG/AIT frames and saved workbook. Results are in results/calc-table-live-01; audit source is audit_calc_table_live_v1.py.

Initial capture to GUI decision: 115.537222521 s; to final evaluation: 115.861728346 s. These include tool orchestration, reading and manual decisions, with no matched baseline or verified model configuration. They do not establish human-like speed. Actual model tokens/cost remain unmeasured.

## What this changes next

The common interface exposed two normal modal boundaries correctly, and the full receipt retained negative evidence while the companion made state changes readable. However, program interruption did not mean the application action failed: save opened its dialog and confirmation closed it. Repeating those inputs would be the wrong recovery. Two additional observation programs (four clock/submit socket exchanges) were used because immediate screenshots were partially painted.

The next candidate should make useful post-transition observation available without granting further input or silently treating arbitrary focus changes as safe. Test a bounded observation-only continuation following terminal release, including unrelated focus loss, against this normal modal flow. Keep the decision and new input lease separate. This targets recovery/wait cost rather than hiding needs_decision.

State companion size is not uniformly smaller: entry's nine selected observations are 8025 canonical bytes versus 3447 companion bytes; each one-observation stage grows (888 to 1188, or 881 to 1087). Preserve that overhead result; bytes are not tokens. Avoid a format-only optimization before measuring recovery improvement.

This is one non-Inkscape live case with natural modal transitions, not a controlled injected fault or A/B speed result. No automatic runtime promotion, general fault coverage, or independent per-child cleanup inventory is claimed.
