# #2254 live two-surface scheduler deadline/fairness rung — allocation02

## Disposition

**PASS_LIVE_SCHEDULER_BOUNDARY_SCOPED** for the frozen model-free component rung. Parent Issue #2254 remains **HOLD_MODEL_TASK_UNTESTED**: no real planner/model, task effect, token cost, ACK/resolution policy or end-to-end recovery was exercised.

Allocation01 remains `STOP_OUTER_EXECUTION_TIMEOUT / HOLD_EVIDENCE_INCOMPLETE`; it was not rerun or pooled. Allocation02 changed only the retention envelope to one case per external invocation with immediate immutable case JSON. Scientific source, schedules and 8ms/100ms/burst3/50ms/70ms gates were unchanged.

## H/T/D/C/U

- **H:** on the same native-derived two-surface record stream, global FIFO can miss a 100ms critical deadline behind unrelated state; pure critical-head priority can avoid that miss but starve unrelated state; burst-3 deadline/fair scheduling can preserve per-session FIFO, mark already-expired evidence, and bound the selected unrelated-state wait to 50ms in the frozen schedules.
- **T:** six directed private-X11 schedules x three fresh Xvfb lifetimes = 18 cases. Real core-X11 FocusIn/FocusOut and 32x32 XGetImage state captures feed three in-process scheduler policies. Synthetic service cost is fixed at 8ms/item.
- **D:** exact18 denominator, process/source/identity/FIFO/authority integrity, three deadline/fairness gates, expiry typing, cross-session isolation, raw-only audit and corruption controls.
- **C:** workload and 8ms service are directed; criticality is fixture-authored; policy threads share one CPython process; watcher receipt time is not physical focus-transition time.
- **U:** no model/provider, actual planner interruption, task recovery/effect, tokens, input actuation, production runtime, natural event rate, human-tempo or product claim.

## First formal outcome

18/18 cases completed. 90/90 watcher/actor/Xvfb exit receipts are zero. Raw-only audit errors are empty. All 13 copied-evidence mutations are rejected. Formal reruns/replacements are zero.

### Backlog critical deadline

A `FOCUS_LOST` arrived behind twenty B-state records. Latency from watcher observation to scheduler delivery:

| Policy | rep0 | rep1 | rep2 |
|---|---:|---:|---:|
| GLOBAL_FIFO | 221.067 ms | 213.573 ms | 215.970 ms |
| CRITICAL_HEAD_FIRST | 58.234 ms | 51.651 ms | 52.161 ms |
| DEADLINE_FAIR | 58.196 ms | 51.606 ms | 52.102 ms |

GLOBAL_FIFO exceeded the frozen 100ms boundary in 3/3 cases. Both priority policies delivered the critical record within 100ms in 3/3.

### Unrelated-state starvation

Ten A focus transitions were queued before the selected B STATE entered the frozen scheduler snapshot.

| Policy | rep0 | rep1 | rep2 |
|---|---:|---:|---:|
| CRITICAL_HEAD_FIRST | 84.438 ms | 85.860 ms | 84.775 ms |
| DEADLINE_FAIR | 27.735 ms | 28.182 ms | 27.934 ms |

Pure critical-head priority exceeded the frozen 70ms starvation floor in 3/3; DEADLINE_FAIR stayed within the frozen 50ms bound in 3/3.

### Expiry and ordering

DEADLINE_FAIR typed all three delayed A focus-loss records `EXPIRED` at [151.157, 151.76, 151.381] ms (>100ms). Critical-pair A loss/gain order, per-session FIFO, cross-session identity and `authority=false` all reconcile.

## Scope

This is real X11 observation plus synthetic scheduler service, not a real model-facing planner result. A PASS only supports the finite scheduler boundary. It does not close #2254 and does not establish that the model will use an event correctly or that task safety/recovery improves.
