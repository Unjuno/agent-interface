# Integrated acceptance boundary for successor #2337

Status: `HOLD_ADAPTER_BOUNDARY_UNEXECUTED`

This report freezes the requirements and evidence boundary for the live
golden-v3-to-CLI adapter successor. It reuses the immutable result at
`runtime/results/golden-desktop-app-server-v3-live-01/golden-report.json` and
does not rerun or alter that allocation.

## Retained evidence

The retained Golden v3 route is a real six-task desktop result with routes
`cold/reuse/reuse/repair/reuse/reuse`, three planner generations including
preflight, 27,892 input tokens, 477 output tokens, 132 reasoning tokens, six
independent exact submissions, zero old-target pointer admissions, and verified
release of every terminal program. Six-task elapsed time is 37,714.870 ms and
whole-command time is 52,180.750 ms. Its own scope explicitly makes no adapter,
baseline, general token-efficiency, or human-speed claim.

## H/T/D/C/U

- **H:** a live adapter can preserve typed lifecycle identity, freshness,
  authority, usage, effect, and cleanup fields while retaining the Golden route's
  safety outcome.
- **T:** run the same six-task cold/warm/invalidation/repair/reuse workload
  through `LIVE_GOLDEN_ROUTE` and `LIVE_GOLDEN_TO_CLI_ADAPTER`, with an
  independent effect scorer and all attempted model stages accounted.
- **D:** the retained JSON report, raw event evidence, adapter output, and
  independent scorer output; synthetic trace evidence remains a control only.
- **C:** RETAIN only if live field/order/identity preservation and effect
  outcomes pass; HOLD if only synthetic or retained-route evidence exists; FAIL
  on dropped lifecycle fields, process-exit-as-success, unsafe replay, or cleanup
  misreporting.
- **U:** no live adapter execution, second desktop-like workflow, baseline
  comparison, or causal token/latency benefit is established here.

## Requirement matrix

| Requirement | Existing enforcement | Current evidence |
|---|---|---|
| Fresh target after model wait | Golden dependency revalidation | PASS on retained route; adapter untested |
| Bounded dispatch and release | terminal release checks | PASS on retained route; adapter untested |
| Independent task effect | exact six-task oracle | PASS on retained route; adapter untested |
| Failed/unknown/ambiguous lifecycle | typed synthetic adapter control | Synthetic only |
| Adapter field/order/identity | live source-to-CLI comparison | Missing |
| All-attempt model/token accounting | retained usage fields and shared ledger | Adapter comparison missing |
| Stale invalidation and bounded repair | task 4 retained repair route | Adapter comparison missing |
| Second desktop-like workflow | integration plan requirement | Missing |

This is deliberately a HOLD, not a product PASS. The next experiment should
execute the adapter in an Ubuntu/Xvfb-capable container or runner and publish
the result through a successor PR for #2337.
