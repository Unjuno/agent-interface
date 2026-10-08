# #2255 first live degraded-evidence rung

Allocation: `degraded-temporal-monitor-2255-20260922-01`.
Owned branch/path: `research/degraded-temporal-monitor-2255-20260922-v1`, `research/live_control/degraded_temporal_monitor_2255_v1/**`.

## H
A compiled `A_THEN_B_WITHIN` monitor can be semantically correct on complete evidence yet become unsound when delivery coverage, order, or clock comparability is degraded. A fail-closed wrapper that receives explicit evidence-quality flags should return `UNKNOWN` for declared loss/reorder/cross-clock cases. If loss is not declared, the same wrapper can still falsely return `SATISFIED`; this limitation must be retained rather than inferred away.

## T
Private authenticated TCP-disabled Xvfb with one ordinary Tk window. Its visible label and `WM_NAME` carry `epoch:phase:tag`. A separate Xlib observer receives real `PropertyNotify` events and retains the complete raw stream. A controlled delivery layer then produces complete, declared-gap, undeclared-gap, reordered, or cross-clock packets for two separate policy processes: `NAIVE_COMPILED` and `FAIL_CLOSED`. The raw observer stream is scoring-only.

Eight scenarios × two fresh repetitions = 16 fresh app/Xvfb/observer lifetimes in two immutable eight-case batches. One formal invocation per batch; no retry/replacement/exclusion/tuning. Construction uses other output paths and is excluded.

The contract is `A` followed by `B` in the same epoch within 80 ms, unless `CANCEL` for that epoch intervenes. This cancellation gives the degraded-delivery experiment a falsifiable false-satisfaction case.

## Variable table

| Symbol | Meaning | SI unit | Definition | Domain/assumption | Type |
|---|---|---|---|---|---|
| `t_A` | X-server time of accepted A event | s (stored as ms) | `server_ms/1000` | same X-server clock and epoch | scalar time |
| `t_B` | X-server time of candidate B event | s (stored as ms) | `server_ms/1000` | same X-server clock and epoch | scalar time |
| `Δt` | A→B event-time separation | s | `(t_B-t_A)` modulo 2^32 ms | computed only for comparable X-server timestamps | scalar duration |
| `τ` | contract bound | s | 0.080 s | frozen | scalar duration |
| `e` | obligation epoch | dimensionless | event `epoch` | positive integer | scalar integer |

Dimension check: `Δt` and `τ` are both durations. The candidate refuses cross-clock packets before subtracting timestamps from different clock domains. Diagnostic host `monotonic_ns` brackets are never subtracted from X-server milliseconds.

## D
`PASS_DECLARED_DEGRADATION_FAIL_CLOSED_SCOPED` requires all16 cases/source/process/effect records; the fail-closed policy returns UNKNOWN in all six declared degraded cases (declared gap/reorder/cross-clock ×2), zero false SATISFIED against the complete raw oracle in those cases, and exact semantics on complete evidence. The two `CANCEL_DROP_UNDECLARED` cases must expose the declared limitation: fail-closed candidate falsely SATISFIED against the complete oracle because no coverage loss is signaled. That comparator remains `FAIL_UNDECLARED_LOSS_LIMITATION`, not erased by the scoped PASS. All app/observer/Xvfb/case/batch exits must be observed and effects match the final authored title. Independent raw-only audit and >=8 copied-evidence corruptions required.

Missing source/process/denominator evidence is STOP/HOLD. Complete contrary candidate behavior is FAIL. No partial subset PASS.

## C
Barrier-directed title updates and controlled delivery degradation; not a natural loss-rate experiment. Same-author independent auditor is not external human review. `PropertyNotify` is evidence only and grants no action authority.

## U
No model/provider, task action, second GUI family, hidden predicate sampling, reconnect, multiple overlapping obligations, production monitor, latency/token gain, or full #2255 acceptance. Undeclared loss remains fundamentally undetectable in this rung without additional channel/sequence evidence.
