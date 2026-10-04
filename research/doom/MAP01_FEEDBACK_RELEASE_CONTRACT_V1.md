# MAP01 per-key release and useful-feedback contract v1

Status: **PASS for offline construction only; main already contains opt-in
v13 per-key release-RPC interval telemetry, but its live use and recovery
efficacy remain untested.**

## H / T / D / C / U

- **H:** Conservative per-key occupancy bounds are reconstructible by joining
  each owner admission acknowledgement to a same-intent, same-program-ID, same-step, same-key v11 `input_release_rpc` caller bracket only when the receipt proves release application and its resolved keycode matches the admission. Program ID is separate from the intent token and prevents otherwise-identical steps from different programs sharing a receipt. A source-pinned fake-Xlib probe showed V11 publishes its XSync-shaped success flag for an aliased-symbol up that issues no KeyRelease and no sync, so that flag alone cannot certify application. Cancellation intervals use resolved X keycodes; admissions sharing a keycode group into one physical interval. Without a matching verified keycode interval, a verified asynchronous empty-owner release in `input_released.owner_release` with its intent token on the outer event and `grants_input_authority=false` supplies only an upper censoring bound. Receipts establish neither continuous physical state nor application consumption.
  Useful feedback
  requires an exact observation paired to an independent task scorer; pixel
  change alone is not sufficient.
- **T:** Run `python research/doom/test_map01_feedback_release_contract_v1.py
  -v` over matched two-key release brackets, the executor's nested verified
  cancellation receipt,
  scorer-backed kill/exit progress, adverse score, mismatched scorer/observation
  identity, controller-visible scorer evidence, wrong release program/step/keycode, no-op or unproven ordinary release, alias-grouped cancellation intervals, missing release, and out-of-window recovery evidence; plus the separate source-pinned V10/V11 fake-Xlib probe.
- **D:** PASS for the construction oracle when all release brackets match
  their admissions by identity and order, cancellation intervals remain explicitly
  censored at the verified nested empty-owner release, mismatched/controller-visible scorer
  evidence stays unknown, and a score outside the declared recovery window does
  not pass. The retained synthetic suite passes 11/11 cases, including cross-program receipt rejection, keycode alias grouping, malformed keycode intervals, and fail-closed no-op or unproven ordinary release receipts.
- **C:** Release may occur asynchronously between the last observation and
  terminal; its nested owner receipt is a valid censoring bound, not an exact normal
  key-up time. A standalone `owner_release` row is not the executor wire format
  and fails closed. A scorer sample may be exact yet show no task progress. A
  kill-count increment is a progress signal, not equivalent to map completion.
- **U:** The oracle has synthetic receipt coverage plus retained-run negative
  conformance checks below. No current runtime source was changed; no
  live game, GUI, model, physical input, matched condition, recovery result,
  performance effect, or #59 exit criterion is established.

## Existing integration boundary and remaining gap

The refreshed `origin/main` at `6a22a43ce6ed3a3acc687c561e0dfcc37a5f294b`
contains `input_owner_v11.py`, which brackets ordinary key-up release RPCs, and
`doom_typed_release_backend_v2.py`, which can attach program/step, owner, and
intent provenance to those receipts. These are opt-in components; the retained
v39 live run did not emit that schema. Executor V13 publishes verified cleanup
as an outer `input_released` event containing the intent token and nested
`owner_release` record; the local oracle now consumes that exact envelope and
rejects a standalone owner record. A direct read of
`research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl`
found 39 `input_admission` events, zero `input_release_rpc` events, one generic
`input_released` event, and nine terminal events. An admission row contains only
the key, admission/acknowledgement times, deadline, and emission time; it lacks
the intent, owner, and step identity required by this join. Applying
`reconcile_key_intervals` to the real trace correctly stops at
`invalid_admission`. The raw run therefore cannot yield per-key occupancy
intervals; the synthetic suite proves only the oracle behavior.

The separate PR #7529 proposes per-key intervals for cancellation cleanup and
is still open, so it is not current-main evidence. Any new allocation would
need a freshly frozen runner that selects the attributed backend, captures
normal and cancellation release paths, and keeps the interval endpoints
explicitly censored. The consumed v39 allocation is not reusable.

Useful feedback should be a separate event joined to the exact observation
identity and independent scorer sample. The scorer receipt must name the
observation ID, sequence, and capture time, remain explicitly independent and
controller-invisible, and carry a monotonic sample time. The before/after
observations must advance sequence and capture time, keep the same pointer
binding, and place the baseline scorer sample before the follow-up capture.
Existing MAP01 terminal fields include
map exit, episode-finished, death state/count, and kill count. The test calls
the existing `ProgressClock` implementation (blob
`2a7d4ff9a68d073d425a40c87c96e7d99201ece1`) rather than duplicating its
scoring rules. It labels scorer-backed kill increments as useful progress and
map exit as terminal progress; episode completion without map exit is adverse.
Simultaneous gains and losses remain mixed. Missing scorer evidence,
stale/ambiguous identity, and visual-only change are unknown. Recovery efficacy
still requires a preregistered matched live condition with an explicit finite
deadline; this test only rejects scores outside a supplied window.

The retained v39 report contains only one post-control scorer refresh, so it
cannot identify first useful-feedback onset during control. The raw trace has
218 exact observation rows but only 10 distinct `id` values, because program
IDs repeat across frames; a valid join therefore needs sequence and capture
time as well as `id`. The sole score event was emitted 2.022 s after the last
model call ended and 50.053 s after the first model call ended. These retained
timestamps establish the gap in scorer sampling, not the time of any earlier
kill or other useful effect. The repository's
`independent_progress_clock_v1.py` already defines scorer-only positive and
negative events but documents integration as deferred. Joining that stream to
exact observations while keeping privileged scorer state out of the controller
channel remains open. The V11 no-op receipt probe also shows that the existing ordinary release producer does not yet satisfy the strengthened contract: it can assert the XSync-shaped flag for a no-op. Receipts without explicit `release_applied=true` and a matching resolved keycode are therefore rejected by the oracle. The adjacent v13/backend-v2 suite could not be executed
on this Windows host because its import closure requires PyXlib, which is not
installed; no dependency was added. No live game or model run was started.

## Reproduction

```sh
python research/doom/test_map01_feedback_release_contract_v1.py -v
python -m py_compile research/doom/map01_feedback_release_contract_v1.py research/doom/test_map01_feedback_release_contract_v1.py
git diff --check
```
