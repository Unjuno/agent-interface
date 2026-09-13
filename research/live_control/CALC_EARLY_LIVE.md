# Actual Calc self-use with early interruption replies

New explicit entries cause_servo_socket_v4/cause_servo_interactive_v4 connect the stopped socket to executor v8. early_exchange_v1 keeps the prior clock, image-sequence and own-command/admission checks, but waits for own input_stopped or terminal and returns PendingAction state. early_resume_v1 reconstructs that state from the recorded submit/replies and makes exactly one read-only poll. It neither sends input nor refreshes the lease; only images in the received followup are resolved. A poll timeout may remain pending. There is no automatic loop.

## Actual episode

results/calc-early-live-01 records Calc seed 225 with the same initial PNG and numeric entry/save/confirmation input steps as prior familiar runs. The assistant viewed the initial and entered worksheet, early save image, early confirmation image and final confirmation image. The save followup image had the same hash as the already-viewed early save image. Full lifecycle, receipt attention and state companions were inspected.

Entry completed. Save and confirmation each returned input_stopped_capture_pending with focus_changed and no terminal, then a separate read returned terminal_received with the same cause and zero completed input-program steps. No extra observe input program or input retry was used. The first save image already showed the complete format dialog; its two later passive captures were identical to that early image. The early confirmation image still showed old dialog pixels; the final image showed a clean worksheet and cleared modified indicator. GUI-only prediction was hashed into a clock command before finish. The saved workbook independently contains [816,345], success true. Bridge/runtime exited 0.

## Timing and cost

| Metric | Save | Confirm |
|---|---:|---:|
| Submit exchange start to early reply, ms | 225.546 | 215.707 |
| Early reply precedes runtime terminal, ms | 280.524 | 339.082 |
| Runtime terminal to followup reply, ms | 10728.913 | 10314.356 |

The roughly ten-second gaps include tool orchestration, image review and assistant decisions; they are not capture latency or pure model-inference timing. Early notification arrived sooner but did not by itself reduce the manual turn cycle.

Total: 59 events, 13 captures and 11 socket exchanges, versus 59/13/9 for the prior terminal-wait passive run. Initial capture to GUI prediction was 97.064s here versus 78.780s previously. These ordered familiar trials have different runtime/client candidates, setup timing, unverified model configuration and decision overhead; no causal speed comparison is claimed. Both final values are correct. Actual model token/cost instrumentation remains absent.

## Compatibility finding and audit

Receipt v4 recognizes the older terminal state name, so new terminal_received/lifecycle fields leave program_binding null even after actual completion. These warnings were not hidden or relabeled. Lifecycle also repeats some observation fields already present in the state companion, increasing review payload. This prototype is not ready to replace the existing report format.

The separate audit checks source pins, all raw socket reply slices, exact command echoes, clock/source-sequence/deadline consistency, regenerated lifecycle and receipt/table values, read-only followups with unchanged prefixes, owner causes/releases, no input in followup replies, pre-score GUI commitment, thirteen exact PNG/AIT frames and workbook values. Its passed result is separate from the older receipt's unsupported binding status.

## Decision

Keep early delivery optional. Always exposing an additional model turn for a normal approximately 300ms post-release capture is not justified by this evidence. Next compare a bounded client wait that includes promptly arriving terminal/images in the same outer response, while returning explicit capture-pending state when that wait expires. The read must not replay input or silently extend authority. Retain early stop timestamps for first-notification metrics, independently of when the outer response is delivered. Preserve blocked-capture tests to ensure the wait is bounded. Resolve new-state receipt compatibility without suppressing real uncertainty before promotion.
