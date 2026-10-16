# Actual assistant reads admitted outcomes by originating request ID

EventCursor v4 / private socket v10 permit request-scoped accepted, terminal,
effect_evidence and independent_evaluation boundaries through admitted_request.
The declared action must agree with the event's action field, and an embedded
effect action must agree when present. Matching rejections interrupt a wait even
if rejected was not explicitly requested. Other requests' records remain in the
prefix but cannot satisfy the requested boundary. This checks identity metadata,
not semantic effect truth or authenticated causal attribution.

The assistant viewed Calc's initial and format-dialog images, entered 532/590,
and submitted Excel confirmation through the combined send/wait interface. The
enter terminal was read by request ID enter. Early effect and final evaluation
were separately read by request ID confirm. Both carry the identical admitted
runtime receive sequence 4, declared action confirm_excel and transport ID confirm.
Final retrieval repeated the same request ID/payload without another input write.

Independent workbook bytes match the effect digest and cells [532,590]. Twelve
exact AIT/PNG frames, complete 25-record read prefix, output receipts and identical
terminal/effect/final admitted metadata are audited. There are two accepted
programs, no rejections, two clocks and five caller operations before cleanup.

| Measurement | Actual run |
|---|---:|
| First capture to effect socket return | 57.082 s |
| Modal terminal to confirmation admission | 24.658 s |
| Final terminal to early effect emit | 20.329 ms |
| Early emit to socket return | 8.268 ms |
| Final terminal to final evaluation emit | 35.706 ms |

The local early socket return precedes final emission, but model wakeup timing is
not measured. Total time is close to the earlier unscoped combined run (57.422 s),
not evidence of a speedup or zero overhead: these are familiar sequential tasks
with uncontrolled model/tool scheduling. Actual model token counts remain absent.

Six replay controls built from the real effect cover matching/other requests,
missing/conflicting admitted identity, and matching/other rejection. Records are
retained in every case. Results: results/request-outcome-self-use-01,
request-outcome-self-use-audit.json and request-boundary-controls.json.

This verifies the previously unexercised Calc early-effect lineage path. It does
not solve session restart identity, unbounded admitted-binding retention, permanent
writer stall, or causal attribution of application changes. No default promotion
or freeze credit. Next return to an end-to-end planner benchmark: metadata now
supports tracing each decision boundary, while the measured modal decision gap
still dominates local execution. Avoid further metadata-only speed claims.
