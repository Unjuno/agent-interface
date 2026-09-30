# Public six-task post-release feedback comparison

Decision: retain the composed runtime as a scoped candidate in PR #5639 under #2789 / #57. This package exercises the actual public relay and all six desktop task rows. It is not PASS_INTEGRATION_SPINE_SCOPED: caller source counters are assertions, not server-issued visual freshness; changed-target admission and bounded recovery through the guarded entry remain untested on this source. Human-comparable tempo is UNMEASURED.

## Executed allocation

Source 3161424cc31cca5dbac9659df4f262f831dd3572, seed 1001040, candidate-post then baseline-inline. The primary model was locally labelled gpt-6.1-sol / medium in both arms. Committed portable runtime archives ran through the ordinary public MCP relay in Ubuntu on WSL 3.0.1, Linux/X11/Xvfb and Chromium 145.0.7632.6. A fresh allocation served each arm; neither was restarted or input-replayed. Both original fixture handles and relay transports exited 0. Raw cleanup still has candidate [0,1,1] and baseline [0,1,0], so this is not a claim of clean child shutdown.

The primary viewed each actual navigation frame, grounded the field and Save positions, and submitted one finite fill+held-Save batch for the known task family. It then viewed the returned pixels, requesting at most one fresh read-only observation if SAVED was absent. All six independent exact tokens were saved once in each arm, with no missing, unexpected or duplicate submissions. The oracle was read only after explicit close. The form and completion frames are retained separately from review attribution; metadata titles and completed dispatches are not semantic-success proof.

Both arms request 400ms navigation sleep and 300ms fill+Save sleep. Baseline holds Save for 200ms, captures before release, then releases. Candidate holds for 100ms, releases, sleeps another 100ms, then inspects and captures. Wait/capture placement and held duration change jointly. All compared navigation/Save calls actually returned summary presentation; their normalized input operations otherwise match. This fixed order and known workload cannot isolate a universal latency effect or establish a universal settling bound.

| Measurement | Baseline inline | Candidate after release |
|---|---:|---:|
| Independent exact task rows | 6/6 | 6/6 |
| Extra read-only completion observations | 6 | 0 |
| Public calls, including clocks/controls/lookup/close | 38 | 32 |
| Delivered images | 19 | 13 |
| Text bytes for 12 navigation/Save dispatches | 48,994 | 69,862 |
| Same-report full presentation, offline text bytes | 69,868 | 105,268 |
| Median Save-send → useful presentation callback | 7,854.82ms | 386.87ms |
| Median Save-send → completion review record | 15,459.37ms | 7,999.95ms |

Candidate task-3 review was delayed to 240,978.10ms across a context continuation and user WSL steering. Other candidate review intervals are 7,271.96–9,705.69ms; baseline intervals are 13,791.41–22,821.83ms. Preserve the full per-task values in analysis.json: do not remove the interrupted row to manufacture a faster result. Presentation callbacks mark delivery, and review records are caller-declared attribution. Tool scheduling, model reasoning, user input and context growth confound these endpoints; neither is an independent semantic perception clock or a human comparison. Initial tool startup and all additional clocks/control calls are separately retained rather than hidden inside these Save intervals.

The candidate's dispatch text is about 42.6% larger than baseline. Summary reduces its own same-report full text by about 33.6%, and baseline by about 29.9%. project_full.py reconstructs the pinned full presenter offline, includes the public owner's session snapshot, and checks that re-summarizing reproduces each original wire metadata exactly. It sends no tool request, captures no pixels and presents no image. Full and summary share the same image reference, raw-report identity and outcome. This measures serialization bytes, not model tokens or actual dollar cost.

model-usage-projection.json retains actual local Codex usage counters around 33 primary tool calls, including input/cache/output/reasoning fields and first subsequent usage where available. The bounded 32MiB scan excludes private conversation text. Request/output association uses local call IDs; usage association is chronological, not a provider-attested foreign key. Before-output usage cannot include the new tool result. Later counters include whole conversation context and cache behavior, and candidate output remains in baseline context. Missing context stays null. Dollar billing is unavailable; no isolated image/token/cost saving is established.

## Integration correction and preserved stops

The predecessor source 22b9a18fc requested summary on a program without inline observations. It returned full presentation because the summarizer only accepted inline capture/provenance. Allocation 03 stopped before the first submit; its STOP_PRESENTATION_COMPOSITION, zero submissions, false independent six-task score, close and raw receipts remain in the archive. It was not relabelled PASS or resumed.

Source 3161424cc composes successful post-release capture with summary presentation using the server's pre-invocation copied program when the raw report has no normalization/compilation section. It only does so for a valid selected post image, verified neutral release, matching completed operations and fixed waits. Failed/unknown waits or unsupported states retain full fallback. Full retrieval retains the exact call arguments. The report digest identifies the raw report, not the separate program context; presentation explicitly states that distinction. The change affects presentation only, with no new automatic input, target selection, source refresh, retry or recovery.

The live controls after task completion reject expired and caller-stale admissions with unchanged 588 cumulative emissions and no image. Candidate refusals skip both settling wait and capture. Read-only retained lookup returns the same image reference and original invocation program and is not presented to the model. It neither renews review IDs nor demonstrates server-issued freshness. Explicit close verifies neutral input.

Projection construction initially failed because its offline presenter omitted the owner session snapshot. The construction stop and subsequent corrected offline script are retained; no GUI allocation or input was repeated for that correction.

## Recheck retained evidence

Run:

    python3 runtime/results/post-release-feedback-04/verify.py
    python3 -O runtime/results/post-release-feedback-04/verify.py
    python3 runtime/results/post-release-feedback-04/controls.py

The standalone verifier checks all 411 archive members, raw identities, exact-once scores, normalized input parity, actual summary schema, release/wait/capture order, delivered/retained/reviewed PNG identity, preserved controls/lookup/close, the original STOP, same-report full projection and usage labels. It never contacts a live application. Explicit checks work under -O. Countercontrols reject a corrupted archive, missing manifest member, incorrect independent score and wrong reviewed image.

Local shared protocol 335 tests and Linux harness 141 tests pass on the runtime composition fix; the raw commands/log hashes are retained under checks-01. These tests and archive verification are supporting evidence, not the guarded/recovery integration gate. Manifest consistency is not authenticated provenance, and an attribution record is not an independent semantic evaluator.

The earlier runtime/results/post-release-feedback-01 archive and its original negative findings remain unchanged. This additive archive retains allocation 03 and 04 raw requests, replies, PNGs, plans, callers, portable archives/source manifests, timing/reviews, submission history, cleanup, local check logs, usage projection and construction failures. The remaining substantive promotion work is the matched current-path setup/readiness → fresh target binding → guarded action/release → independent result → changed-state refusal → bounded recovery/read-only continuation comparison.
