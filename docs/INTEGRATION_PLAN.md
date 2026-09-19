# Integration priority — 2026-09-19

**Agent-first clarification:** the primary user is the agent itself. Drive this
task by actual assistant use: observe a difficulty, improve the interface, then
use the same path again. Research supplies evidence for design choices. Prioritize
fewer avoidable tool boundaries, usable observations/results and recovery in the
agent's own loop. The [receipt self-use example](../runtime/results/receipt-self-use-01/README.md)
records the first concrete result-presentation improvement from this loop.
The [composed exchange](../research/live_control/AGENT_EXCHANGE.md) now removes
manual clock-request and steps-file assembly in that research path. Actual
assistant use covered a viewed draft followed by correction and independent
scoring, with the first rejected development attempt retained. This does not
yet connect the golden semantic compiler to the native CLI.
Its [review companion](../runtime/results/composed-review-01/README.md) returns
the receipt and referenced image together, avoiding a separate host image read
and WSL path conversion. This is a verified presentation path on retained data;
live-tempo and model-token effects remain unmeasured.
The [live Calc use](../runtime/results/calc-live-review-01/README.md) now connects
these through `agent_exchange --review`. It passed independent saved-cell
evaluation, while exposing delayed dialog pixels and 18–25 second outer gaps.
Next address observation/result continuation and caller assembly; native input
speed alone does not explain the remaining tempo gap.
The [final-drain integration](../runtime/results/calc-final-drain-01/README.md)
now reads an already-available independent result once after early saved-effect
evidence. Actual Calc use returned evaluation in the action response; a missing
result remains pending. It removes one outer continuation turn in this example,
not a socket exchange or the remaining deliberation gaps.

The user's current direction is to concentrate this task on integration while
other contributors continue benchmarks and experiments. Product Hunt publication
has already happened according to the user. The engineering objective is a
usable, coherent interface; launch ranking is not a runtime acceptance criterion.

This implements the sequencing of [Issue #57](https://github.com/Unjuno/agent-interface/issues/57).
The bounded admission-audit work in [PR #2014](https://github.com/Unjuno/agent-interface/pull/2014)
is finished. Integration starts now and does not wait for the full research backlog.

## Selected starting path

Starting repository revision: `2d78394e4128d9274030dcc52cf0957be2eb312d`.
Use the existing [golden desktop v3 entry point](../runtime/golden-demo-v3.sh) and
its [retained six-task result](../runtime/GOLDEN_DESKTOP_DEMO_V3.md) as the first
end-to-end desktop route. The retained route already covers cold acquisition,
warm reuse, stale-layout refusal, repair and post-repair reuse. A successor must
retain that result and its sources as evidence rather than rewrite the old run.

The [unified native CLI/API](../runtime/cli_v1/README.md) is the mechanical runtime
entry point. Its admission and native sessions are useful integration surfaces,
but their existence alone does not connect the golden route's semantic compiler,
feedback, accounting and repair. That boundary needs an explicit adapter before
claiming one unified end-to-end runtime.

| Responsibility | Starting component | Integration requirement |
|---|---|---|
| Setup and diagnostics | `runtime/setup-golden-demo-v3.sh`, v3 doctor | Check the actual route's dependencies before spending a model call. |
| Model interaction and accounting | Existing golden v3 grounding adapter and shared caller | Preserve every attempted call and actual usage; keep provider coupling at the adapter boundary. |
| Representation and local continuation | Existing compiled desktop workflow | Intermediate evidence must influence continuation; retain cold/warm/repair accounting. |
| Native execution and admission | `runtime/cli_v1`, `selector_v1`, `core_v1`, selected backend | Preserve caller freshness, explicit target identity and release semantics; own and close resources. |
| Feedback and task result | Existing exact observations and independent desktop scorer | Expose concise results and retrievable evidence; distinguish program completion from task success. |
| Invalidations and recovery | Existing stale-layout refusal and bounded repair path | Retain completed effects, stop on uncertainty, and avoid blind replay. |

Start with Linux/X11 desktop integration. Existing Win32/Quartz work remains
available, while portability expansion, additional benchmark families and new
compression mechanisms stay outside this first integration increment. DOOM
remains a later continuous-control stress domain alongside desktop coverage.

## Delivery order and acceptance

1. **Make the existing entry points dependable.** Verify setup/doctor/result
   behavior and fix resource ownership and error propagation at the public API.
   First repair: the one-shot API closes the backend connection it creates after
   completion, refusal or execution failure; close failure retains the execution
   result/error and produces a non-success response.
2. **Connect one desktop vertical slice.** Follow installation, observation,
   grounding, guarded operation, useful effect and recovery through the selected
   route. Reuse the existing caller/continuation implementation. Resolve each
   missing adapter on that path before bringing in more optional mechanisms.
3. **Run the integrated acceptance workload.** Carry the six-task cold/reuse/
   invalidation/repair/reuse structure into a separately identified successor.
   Map the #57 requirements below to executable checks before live allocation.
4. **Retain the result and make the route understandable to a new user.** Provide
   reproducible setup, a stable entry point, typed results and a clear recovery
   route. Assess end-to-end correctness, latency and token use on this assembled
   path. Extend to an existing second desktop domain after the first report.

| Requirement | Enforcement / verification |
|---|---|
| Validated model output | Existing schema preflight, separately accounted. |
| Fresh target after model wait | Existing dependency revalidation before input; changed-target negative case. |
| Bounded continuation and release | Core/backend admission plus terminal release evidence; error and cancellation cases. |
| Correct task effect | Independent exact submission/effect check, not only a completed program. |
| Honest failure and usage reporting | Keep partial effects, failed calls, unavailable usage and recovery costs. |
| Resource ownership | Public API completion/refusal/exception regression tests; backend close failure cannot report success. |
| Comparative benefit | Reuse #56/#57 matched model/task/environment design and all-attempt accounting. |

The lifecycle regression tests exercise the API boundary with test doubles;
they establish no new GUI behavior or speed improvement. The existing golden
result remains scoped to its retained host/task/allocation.

## Intake from parallel research

Review Issues and merged results for a concrete gap in the selected route.
Record the applicable evidence, source version, assumptions, integration point
and regression case before adoption. Prefer one useful component at a time.
An isolated PASS is a candidate for integration, not an integrated product claim.
Keep failed ideas and revisit them when a stated condition has changed.

This task's new experiments should resolve an identified integration or
correctness gap, or measure the assembled route. Independent discovery remains
with the ongoing research work. The overall human-tempo goal remains open.
