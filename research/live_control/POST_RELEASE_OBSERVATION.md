# Passive post-release observation candidate

Executor v7 is an explicit research fork of v6. For needs_decision focus_changed/surface_changed with verified cleanup, it emits input_stopped, takes two passive snapshots with 80ms sleeps, then emits the unchanged status/reason/interruption plus post_release_observation metadata. No program tail resumes; no lease is created or renewed. The executor remains busy until terminal publication. New input still requires a fresh submit and normal admission.

This is bounded in capture count and scheduled sleep, not a hard wall-clock deadline: synchronous capture, encoding, owner queries and emit may block. It delays terminal availability and cannot preempt a stuck capture. input_stopped is separately present in the event log, but the tested client waits for terminal, so this trial does not prove early model delivery of that event. Snapshot failure is reported separately while the original interruption remains. Equal sample pair is only exact frame/binding equality, never readiness or task completion; both actual modal pairs were unequal.

## Evidence

- results/post-release-01: six synthetic integration cases for stable/changing frames, snapshot exception, release failure, unrelated decision reason and normal execution. Only eligible interruptions invoke captures; no tail runs after them. These do not test unrelated persistent X11 focus, cancellation during capture, hard deadlines or transport stalls.
- results/calc-table-live-02: actual assistant self-use through socket v3/interactive v3 on Calc seed 225. Same initial PNG and same entry/save/confirm input steps as the historical baseline. Full receipts and state companions reviewed; initial, entry, save and confirmation screenshots viewed before subsequent decisions.
- Save/confirm both retain needs_decision/focus_changed with completed prefix zero. Two post-release captures arrive in each existing submit reply. Their input-state samples show no owned keys/buttons and no active owner lease; no subsequent input or program step occurs before terminal.
- The final save screenshot showed the complete format dialog; final confirm screenshot showed the document and cleared modified indicator. No extra observe program was requested. GUI prediction was hashed into a clock command before independent scoring. A1=816/A2=345 passed, and the bridge exited 0.
- Separate audit validates source pins, complete raw reply coverage, receipts/table round trips, distinct cause records, post-release event ordering/state, 13 exact PNG/AIT frames and saved workbook. No default entry was promoted.

## Cost and interpretation

| Measure | Historical v6 run | v7 candidate run |
|---|---:|---:|
| Correct saved values | yes | yes |
| Extra observe programs | 2 | 0 |
| Socket exchanges | 13 | 9 |
| Total captures | 14 | 13 |
| Initial capture to GUI decision, seconds | 115.537 | 78.780 |

This is an ordered familiar-case comparison, not randomized, matched-model or causal speed evidence. Initial setup readiness sampled 13 versus 12 times. Entry settle produced 9 versus 6 observations, explaining the lower total capture count. The modal portion actually grew from four captures including explicit followups to six. Passive collection cost 338.758ms on save and 335.629ms on confirm, delaying terminal delivery. Workbook byte hashes differ while scored cell values agree. No actual model token/cost measurement exists.

## Next validation

Before promotion, keep focus on observation latency and recovery semantics: test a persistent unrelated focus change, blocked capture/output, and cancellation/close while passive collection is active. Compare explicit terminal-now versus passive followup delivery so an agent can inspect the interruption immediately when useful. A finite capture budget alone is not a wall-clock bound, and an automatic view of a different window must not imply permission to type there. Preserve both historical runs and failures.

Timing label caveat: the result scope says 'two samples 80ms apart', but implementation sleeps 80ms before each capture. Actual capture spacing also includes capture/publication work and must be computed from capture_ns; it is not an exact 80ms cadence.
