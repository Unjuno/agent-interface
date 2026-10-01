# Choosing input feedback on the live primary route

Use the same primary caller and connection to observe, ground an explicit target,
issue input once, and inspect its original response before choosing the next call.
The host delivers evidence; the primary decides what the application means.
This guide covers the production API on main, including the optional
`inputWithFeedback` helper integrated in PR #6077. See [host setup](README.md)
and [public MCP configuration](../cli_v1/MCP.md) for connection and image sinks.

## Choose the response needed for the next decision

| Need | Existing mechanism | What the response establishes |
| --- | --- | --- |
| See the immediate state and decide the next step | `primary.input(...)` | Original input outcome and its image; application processing may still be pending. |
| Obtain a later image after a small known redraw delay | Public `inspect_after` with an explicit region and optional `inspect_after_wait_ms` | Capture after neutral release and a requested fixed delay; no redraw or semantic detection. |
| Wait within a declared budget for a reliable app title convention | `primary.inputWithFeedback(..., policy)` | Input evidence plus the cue outcome and original image; a matched title is not an independent effect oracle. |
| Resolve an ambiguous result or image | Review the retained original evidence first | A new decision about uncertainty; never a reason to resend the input automatically. |

Choose before dispatch. A fixed wait and an explicit cue wait are different
mechanisms; neither belongs on every input. `inputWithFeedback` defaults to
2000 ms only when the helper is explicitly selected. Ordinary `input` does not
enable this cue wait. Its budget is not a hard end-to-end deadline: transport,
capture and primary inspection add time, and blocking operations may exceed it.

The first response and the first useful completion feedback are separate
endpoints. A slower first reply can save a later primary observation round trip
when the application needs time to finish. That tradeoff does not imply faster
model comprehension, lower tokens, or lower cost.

## Issue once, then inspect before continuing

These calls are separate primary decisions, not a script that automatically
reviews its own output. Start with an existing guarded caller and an alias
already minted from a screen that the primary actually reviewed. Do not invent
an alias or reuse one after a target, guard, or lifetime mismatch.

For immediate feedback:

```js
const response = await primary.input('save', [0, 0], 'click', []);
```

For an application whose declared title convention distinguishes this task's
acknowledgment from rejection:

```js
const response = await primary.inputWithFeedback('save', [0, 0], 'click', [], {
  expected_title: 'SAVED-<this-task-id>',
  rejected_titles: ['REJECTED-<this-task-id>'],
  timeout_ms: 5000,
});
```

Replace the example title strings with the actual declared convention before
use. If the application exposes no reliable task-bound title, choose immediate
observation instead of guessing a title. A title can already exist before input
and therefore cannot prove this input caused the effect. The helper does not
install a sensor, select the action or determine independent task success.

The response has already been presented through the configured text/image sinks.
Read the metadata and inspect the delivered original image. Only then record
the state actually seen, using `response.attempt`:

```js
await primary.review(response.attempt, {
  task: taskId,
  phase: 'after-input',
  reason: descriptionOfTheOriginalImageActuallyInspected,
});
```

The caller supplies both variables. A review record attributes an inspection;
it does not prove that the description is correct. An empty image callback is
not image delivery, and a text acknowledgment cannot substitute for image review.
If the perceived image seems blank or contradicts the metadata, retain the
original file and inspect the same bytes again before attributing the problem
to capture. Do not silently replace the image or replay the operation.

## Keep execution, cue, and task effect separate

Inspect `response.result.isError`, the original execution/release evidence,
the requested cue outcome, the image, and `primary.state().stopped` together.

| Outcome | Primary decision on the current main API |
| --- | --- |
| Input completed, neutral release verified, immediate image still Pending, caller not stopped | Treat the task as unresolved. If the task's previously chosen observation budget permits, explicitly call `primary.observe()` on the same connection and inspect that new response. Do not resend input. |
| Requested cue matched and caller not stopped | Inspect the original image and the task's effect criteria before continuing. A title alone grants no authority, lease renewal or durable success. |
| Requested cue pending, rejected, unstable, missing or inconsistent | The caller latches STOP. Preserve the original response; ordinary observe, mint and input calls remain blocked. |
| MCP refusal, uncertain delivery, presentation or evidence failure | Preserve the original attempt and reconcile the retained receipt. Do not retry through a fresh caller or connection. |

When an ordinary observation is still admitted, it is an explicit new read:

```js
const later = await primary.observe();
```

Inspect and review `later.attempt` before judging completion. Set the number or
time budget for these reads before issuing input; stop with an unresolved outcome
when it is exhausted. This API does not automatically poll until success.

On current main, a stopped primary permits explicit close, not another ordinary
observation or result request:

```js
const closed = await primary.call('interface_close', {});
```

Read its cleanup outcome too. Closing the transport alone is not proof that all
application input was released. Retained receipts are historical evidence, not
current application state or permission to resume input. Proposed stopped-read
helpers in closed PR #6101 have not been adopted on main; do not assume they exist.

## Evidence and performance limits

[The packaged feedback cases](../results/feedback-primary-presentation-01/README.md)
retain matched and pending original images, native receipts and exact-once app
effects. Known matched metadata can use the fixed-path lossless reference schema;
critical or uncertain outcomes retain full feedback. Wire JSON byte reduction is
not measured model-token reduction.

A later [single paired comparison in draft PR #6114](https://github.com/Unjuno/agent-interface/pull/6114)
used the same app, seed, initial image and Save input: immediate feedback took
about 86 ms and five public requests; explicit cue waiting took about 3170 ms
and four requests. The app acknowledged at about 3000 ms in both arms. The first
baseline image was initially misread by the primary, and that error is retained.
One fixed-order pair with inspection delays does not establish general speed or
efficiency. Its combined usage window is not an arm-specific cost comparison.

For a new task comparison, record each endpoint separately: exact effects and
forbidden effects, operation-to-first-useful-feedback time, primary completion
judgment boundary, waiting, requests/captures, recovery work, and actual provider
usage with cached and reasoning counters identified as subsets. Keep unresolved
and failed attempts. Choose a route because the task needs its feedback contract,
then test any broader performance claim under matched conditions.
