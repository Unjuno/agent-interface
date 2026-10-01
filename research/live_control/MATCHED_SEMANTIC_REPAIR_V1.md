# Matched semantic repair comparison v1

The frozen comparison was intended to measure cached target-handle repair against
Luna-low visual reacquisition after the same Chromium width change. Both arms
would pay for initial visual grounding; only the reacquisition arm would pay for
a second image turn. Four fresh sessions, fixed `local/model/model/local` order,
seed213, complete call/image/token/wait accounting and independent task/release
checks were frozen in commit `c03fd4fd` before execution.

The first and only allocation did not produce a comparison. Arm1 navigated to
the private form, entered the exact token and captured its coherent source frame.
Its required initial Luna-low call then returned `Selected model is at capacity`
and exit1. The runner stopped immediately under the no-retry rule. One model
thread started, but no model message or completed turn exists and no usage record
was emitted. No target handle, resize, semantic probe or submission action began.

The two completed GUI prefix programs each completed four steps and released to
empty input. Owner close also verified no held key or button. The preflight was a
compatible cache hit with zero fresh calls. The 34-file/469,683-byte pre-receipt
manifest preserves the exact source frame, events, model request, process result
and capacity error. Independent Windows and WSL audits pass all11 diagnosis
checks.

This failure says nothing about local repair versus visual reacquisition. It does
show that service availability is currently discovered after GUI setup and task
entry. A new version should expose model invocation as a typed outcome and keep
`capacity_unavailable` distinct from a completed semantic result. It should
admit the GUI comparison only under a frozen availability policy and preserve a
later capacity refusal as a deferred, no-authority outcome. The v1 allocation
remains failed and will not be rerun.

There is no token advantage, recovery-time advantage, semantic completion,
general reliability, portability or human-tempo claim from this allocation.

The first repair is now implemented without another model call. The v2 invocation
adapter classifies the retained capacity trace as `DEFERRED_UPSTREAM`; the
admission layer converts it to `TASK_DEFERRED` with no grounding reference,
usage or authority. A retained completed Luna trace becomes task-mutation
eligible but still requires ordinary Executor admission. See
`SEMANTIC_GROUNDING_ADMISSION_V1.md`.

## Capacity-aware v2 result

V2 moved initial grounding before form-value entry and integrated typed deferral.
Capacity was available. Arm1 completed the local path correctly: one9,351-input-
token model call, local repair122.670ms after resized capture, useful feedback
263.130ms after Submit admission,3.460ms probe compute, exact saved `t000214` and
empty release.

Arm2 completed both Luna-low calls. The second returned the correct unchanged
Save point `[270,243]` after8,262.886ms. The source observation's freshness limit
was3,000ms, so constructing and immediately resolving a handle against that old
observation refused `STALE` before contract derivation or Submit. A deterministic
retained-image reconstruction holds point, pixels and binding constant: the same
patch resolves when evaluated at capture+1ms and refuses after the model-wait
interval. This is a freshness failure rather than coordinate error.

The frozen allocation stopped after arm2; arms3-4 never started. Across the two
started arms, three successful Luna calls report28,053 input tokens. Ninety
files/1,415,626 bytes before retention receipt pass all11 Windows/WSL audit
checks. No balanced comparison exists. V3 may change one condition: after model
reacquisition, take one passive current exact observation and require the
model-derived patch to revalidate there before contract derivation or input.


## Matched v3 result

V3 changed only that freshness boundary and passed its first frozen allocation.
After each model reacquisition it retained the model-visible Save patch, captured
one passive exact current observation and emitted a no-authority receipt binding
source/current sequence, capture clocks, model call ID, current point and exact
patch hash. Both model arms revalidated current pixels before contract derivation
or Submit.

All four fresh seed215 sessions independently saved `t000215`, reconciled useful
semantics to exact PNGs and released empty input. The fixed order and results were:

| Arm | Route | Input tokens | Resize capture→recovery | Post-model refresh | Patch revalidation | Useful feedback |
|---:|---|---:|---:|---:|---:|---:|
| 1 | local | 9,351 | 106.618ms | — | — | 254.617ms |
| 2 | model | 18,702 | 8,015.380ms | 75.592ms | 0.071ms | 263.617ms |
| 3 | model | 18,702 | 8,215.156ms | 66.802ms | 0.066ms | 244.828ms |
| 4 | local | 9,351 | 113.315ms | — | — | 246.416ms |

Local recovery median was109.966ms versus8,115.268ms for model reacquisition, an
8,005.302ms difference. Input medians were9,351 versus18,702, a9,351-token
difference. Six unique Luna-low calls and visible images are fully accounted;
preflight was a cache hit with zero fresh calls. The189-file/3,622,385-byte
pre-receipt record passes formal and retained audits on Windows and WSL.

This supports retaining cached local repair for this calibrated unchanged-target
resize case. It does not establish general token savings, unknown-layout recovery,
reliability, other operating systems or human-tempo performance. The next step is
to put this route decision into the shared caller: try fresh local revalidation
first, fall back to typed model reacquisition only when local evidence is missing,
ambiguous or changed, and account for every branch.
