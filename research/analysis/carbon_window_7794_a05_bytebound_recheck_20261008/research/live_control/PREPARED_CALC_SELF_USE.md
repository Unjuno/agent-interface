# Prepared caller across a visible Calc decision boundary

Actual assistant use of prepared_exchange.py now covers terminal mode followed
by an outcome mode program. In Calc seed 991031, the assistant viewed the initial
image, entered 612 and 129, and saved. Terminal mode returned the format dialog
image; the assistant inspected it before issuing Return through a second prepared
program. Both programs derive evidence fields from their received batch.

The confirmation returned VERIFIED early effect evidence with task_success unset.
The assistant then used outcome_client.py in final-only mode and received an
independent successful evaluation. The saved workbook matches both expected cells
and the early artifact hash. Twelve exact frames, two released programs, request
lineage, prepared commands and the complete 23-record prefix are audited. Cleanup
exited zero. No runtime rejection occurred.

| Interval | Measured |
|---|---:|
| First capture to early socket return | 48.084 s |
| First capture to final client return | 66.408 s |
| Modal socket return to confirmation admission | 12.991 s |
| Early socket return to final client start | 18.323 s |
| Early emission to final evaluation emission | 12.862 ms |
| Local entry / confirmation program | 753.276 / 106.071 ms |

The key finding is the last extra caller boundary: final evaluation was already
emitted roughly 18.319 seconds before the assistant started the final-only read.
It was not waiting on the evaluator. This does not isolate model generation time:
model receipt/start/end timestamps are missing, and outer orchestration/tool
work also occupies that interval. Four socket exchanges precede cleanup.

Issue #46, read with its comments during this experiment, asks for explicit clock
domains, missing endpoints and matched Calc/OpenTTD comparisons. The audit now
lists missing model endpoints as NOT_RECORDED and retains endpoint-specific
intervals. It does not satisfy that issue's full timing envelope or two-domain
experiment. Same-session Linux perf_counter comparability is assumed here; no
exported clock epoch/uncertainty mapping exists. No issue closure is warranted.

This is a known Calc dialog path with new values, not a held-out branch benchmark
or a causal comparison against prior seeds. The prepared caller works across
the visible boundary, but returning early evidence alone can add an unnecessary
outer turn when final evaluation is already available. Next test an optional
immediate final-result drain inside the same client invocation, preserving both
events and retaining early return when final evaluation is delayed. Do not hide
intervening records or turn early scoped evidence into whole-task success.

Evidence: results/prepared-calc-self-use-01 and
results/prepared-calc-self-use-audit.json. Runtime/client source manifests and raw
requests, batches, reports, images and workbook are retained. No speedup or human
tempo claim and no default promotion.
