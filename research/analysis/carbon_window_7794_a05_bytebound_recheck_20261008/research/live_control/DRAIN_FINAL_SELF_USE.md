# Same-call collection of an already available final evaluation

The prior Calc run emitted final evaluation 12.862 ms after early effect evidence,
but the assistant started its next read about 18.319 s later. Candidate
prepared_exchange_v2.py adds opt-in --drain-final. After ordinary early-result
processing/image selection, drain_final.py issues at most one read-only,
request-scoped final read with server timeout=0. It does not sleep, submit input,
poll repeatedly or query status. Original and tail batches are preserved and
their records concatenated in the report.

If final evaluation is present, the same command returns evaluated with both
evidence records retained. If absent, it returns the early effect with a final
continuation at the latest received cursor; unrelated records are retained.
Missing/conflicting identities require reconciliation. Transport errors retain
early evidence and an explicit drain error. The zero timeout bounds server event
waiting only: connection/I/O uses the existing 35-second socket timeout and is
not a hard real-time or zero-cost operation.

Six recorded/control cases cover ready final, delayed final followed by a later
read, another request, missing identity, wrong program and a transport exception.
These controls use EventCursor/injected exchange, not live delayed-network tests.

The assistant then used both modes on Calc with the same seed 991031 and exact
step arrays as prepared-calc-self-use-01. It viewed the initial and format-dialog
images before their respective programs. Confirmation's early evidence and final
evaluation were returned together with success, eliminating the separate outer
final-read command in this run. The socket count is still four before cleanup;
the final read moved inside the client. Caller commands fall from four to three.

| Interval | Measured |
|---|---:|
| First capture to early socket return | 45.506 s |
| First capture to end of client processing | 45.541 s |
| Early socket return to end of client processing | 34.275 ms |
| Early emission to final emission | 12.054 ms |
| Modal socket return to confirmation admission | 10.899 s |

The earlier separate final client returned at 66.408 s from initial capture.
That endpoint differs from processing_finished_ns, which excludes the final
report write/print and model receipt. Both variants are single familiar sequential
runs with uncontrolled outer latency, so do not claim a causal 20-second speedup.
The directly demonstrated change is that the final result no longer required a
separate outer caller command in this successful episode.

Audit checks the full 23-record prefix, thirteen exact AIT/PNG frames, both input
releases, saved cells and artifact hash, preparation regeneration, identical
steps, request lineage and absence of rejected programs. The process exits zero.
Model receipt timestamps, actual tokens/costs and human reference timings are
missing. Default behavior is unchanged. Next test live delayed evaluation through
the integrated CLI to ensure the option returns early when final is not ready,
including transport faults before any broader recommendation.

Evidence: results/drain-final-01, results/drain-calc-self-use-01 and
results/drain-calc-self-use-audit.json. All measured sources and raw batches are
preserved. No architecture promotion.
