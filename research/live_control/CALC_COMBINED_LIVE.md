# Combine prompt passive results inside one caller operation

calc_combined_live_v1 wraps the existing early exchange with at most one bounded_followup_v2 call when the returned state is input_stopped_capture_pending. The exact early report remains archived before the additional read. Ordinary completed operations skip this read. Both early and followup exchanges retain their original timestamps; outer_operation brackets invocation through report preparation, excluding rendering/tool delivery/model receipt.

## Actual self-use

Calc seed 225, initial PNG identical to the prior early-return episode, same entered values and input steps, same executor v8 and stopped socket. The assistant viewed initial, entered, save and confirm screenshots and reviewed lifecycle, receipt warnings and state tables. Save and confirm each obtained the terminal and final passive image before the outer operation returned; no separate followup stage or observe input program was needed. Both retain needs_decision/focus_changed with zero completed steps. No input tail resumes.

The GUI showed A1=816/A2=345, the Excel format choice was confirmed, and the final modified indicator was cleared. A GUI-only prediction hash was echoed by a clock command before independent scoring. Saved workbook values pass; bridge/runtime exited 0. Audit verifies source pins, early-report prefix preservation, command-free bounded reads, full reply/event coverage, exact lifecycle/receipt/state-table regeneration, owner causes/releases, images and saved cells.

| Measure | Save | Confirm |
|---|---:|---:|
| Additional bounded read, ms | 253.594 | 279.139 |
| Outer operation through report preparation, ms | 627.886 | 613.356 |
| Runtime terminal to followup reply, ms | 10.638 | 12.518 |

Prior manual early-return episode had terminal-to-followup gaps of 10728.913ms and 10314.356ms. Combining the calls removes those particular manual boundaries. It does not establish equivalent reductions for arbitrary models/tasks. Early notification still existed internally, but was not presented as a separate model-visible response in this candidate.

Both episodes used 11 socket exchanges. Separate followup stage invocations fell from two to zero; network round trips did not decrease. Current episode has 60 events/14 captures versus 59/13, because entry settle sampled one more frame. Initial capture to GUI commitment was 83.588s versus 97.064s previously, with unverified model configuration, repeated familiarity, different setup timing/window IDs and deliberation. No causal speedup or human-speed claim. Initial setup capture counts were 12 versus 14; workbook byte hashes differ, scored cells agree.

## Decision and remaining work

This supports retaining bounded followup as a candidate for short passive recovery while preserving the existing pending path for slow capture (separately tested with stalled capture and silent sockets). Do not run more identical Calc episodes merely to improve a wall-time number. Before promotion, fix the new-state receipt compatibility and duplicated lifecycle/state presentation while preserving unknown/negative evidence, then verify on a different desktop transition/task. Receipt v4 still leaves program_binding null for terminal_received; this audit separately validates actual bindings and does not suppress the warning. Actual token/cost measurement and comparable model/latency instrumentation remain open.

Default runtime/client entries were not changed. Two calls' deadlines do not bound the whole outer operation: initial clock/submit and local file/encoding/rendering are outside the optional 650ms socket deadline. Independent cancellation still cannot preempt a stuck capture or output operation.
