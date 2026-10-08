# Strong form callback comparison against the compiled X11 graph

The compiled graph is integrated and usable, but it is not uniquely able to
continue conditionally without a model resumption. The existing portable
`form.fill_and_submit` exposes an on_step hook that can retain evidence, capture
fresh pixels, validate the effect and refuse before Save. This study compares
that strong baseline with the shared compiled adapter, not a deliberately
unbatched primary loop or blind unconditional Save.

**Disposition: correctness accepted in the fixed fixture; efficiency HOLD.**
Both routes made the same inputs and captures, used five control requests and
two original primary images per case, and never returned to the primary model
between Enter and Save. No route automatically repairs, remints or replays.
Compiled is retained as an opt-in structured graph, not promoted as faster or
cheaper on the basis of this task.

## Allocation and evidence

Source/archive and separate scaffolds are pinned to `eec397e2eaa2db760c9b48a2280cbd9189fa8198`.
Seed 1001067, four allocations, no fixture/input retries: form then compiled
for positive, compiled then form for changed. Each pair has the same token,
fixture, input programs, reference crops, 100 ms waits, requested ten-second
method budget, capture-freshness expiry and common compact presentation.
Baseline adds the supported read-only callback and a thin existing-deadline
argument wrapper; this application-authored callback composition is not the
unmodified helper's generic semantic guarantee. Both use the same visible RGB
predicate/verifier code. Graph budget begins inside the graph after validation;
form wrapper budget begins at method entry. No case approached either limit.

This primary caller (requested gpt-6.1-sol / medium) viewed each original source
PNG, grounded field [350,84]/Save [360,178], issued two explicit mints, invoked
one method, reviewed its original final PNG, then closed. Eight distinct primary
image files, zero same-file re-emissions, no extra model/subagent. Both positive
images show the exact token and SAVED; changed images show exact entry,
ACCEPTED and Removed. After each keeper and its children were terminal, the
independent app log confirmed one eligible exact Save for positive, zero Saves
for changed. Negative-control stops are not counted as completed save tasks.
All keepers exited 0; all child exit codes were [-15,0].

| Case | Route | Task/control outcome | Inputs | Local observations / all captures | Physical emissions | Local method ms | First local effect known ms |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: |
| positive | form callback | 1 exact Save | 2 | 3 / 12 | 44 | 354.234 | 196.296 |
| positive | compiled | 1 exact Save | 2 | 3 / 12 | 44 | 393.597 | 224.373 |
| changed | compiled | entered, stopped; 0 Saves | 1 | 2 / 7 | 39 | 227.485 | 226.404 |
| changed | form callback | entered, stopped; 0 Saves | 1 | 2 / 7 | 39 | 190.952 | 190.765 |

Positive includes 200 ms fixed waits; changed includes 100 ms. Local timings
are descriptive single-case observations. They include capture, ordinary
input checks, method/callback work and retention, but exclude primary grounding,
outside-method tool/model roundtrips and cold construction. They do not establish
that compiled is generally slower, or attribute a causal effect to any component.
Local effect-known timestamps are after callback/graph verdicts on the execution
host clock; they are not first useful feedback delivered to the model or model
semantic awareness. Those model metrics remain null. No human benchmark exists.
Initial positive images were byte-identical; changed initial images differ in
incidental caret blink phase, which did not affect target crops or cue reading.
This nuisance is preserved, not eliminated by a favorable rerun.

## Actual token accounting

| Control interval (observe/mint/method+final image) | Input | Cached input | Uncached input | Output |
| --- | ---: | ---: | ---: | ---: |
| positive form | 603,337 | 600,704 | 2,633 | 541 |
| positive compiled | 610,965 | 608,512 | 2,453 | 534 |
| changed compiled | 620,002 | 617,216 | 2,786 | 663 |
| changed form | 628,021 | 625,536 | 2,485 | 709 |

Each control interval has three actual response identities. Intervals exclude
startup/close and shared preparation and are not net per-route billed costs.
Context grows and caching varies; counterbalanced order does not remove all
context/order/caret/provider-state confounding. The same exposed model alias
and effort are recorded, without provider snapshot attestation. No behavior
shift is alleged; Issue #6001 is an unverified idea, not a new acceptance gate.

Joint preparation through four closes has 20 unique response identities:
4,071,324 input, 4,045,312 cached, 26,012 uncached, 14,310 output, 5,312 reasoning
included in output, total 4,085,634. It includes new scaffold authoring/debugging,
archive/allocation calls, primary controls/images, commentary and closing;
planning/inspection before the explicit start and audit/publication afterward
are excluded. Shared preparation is not assigned to favor either arm. Whole
and control views overlap and must not be added. Pricing/billing is unavailable.
Exact chronological whole-context counters were replayed against 60 original
source lines; this is not provider-attested isolated image/tool attribution.
Nothing here establishes lower tokens, cheaper operation or net construction
amortization. The control totals being close is descriptive, not equivalence.

## Checks, failures and remaining work

The first scaffold test failed because running the file directly omitted the
repository import path. It was corrected before allocation and is recorded as
a preparation failure, not discarded as a failed GUI trial. Three meaningful
method controls pass normally/-O: identical positive input tails, conditional
changed-control stop and release failure preventing Save. Full committed local
native CI passes (see exact counts/logs in native-ci). Finite audit verifies
paired input programs, original pixels and predicate records, image/hash links,
reference-freshness deadlines, task logs, request/capture inventories, verified
neutral raw releases and terminal owners. Positive plus seven mutations pass
normally/-O. These checks are finite evidence, not formal or general safety proof.
The separately imported scaffolds match their pinned Git source after execution;
allocation records pin the archive hash, not provider/process attestation of
scaffold execution. The previous frozen studies are unchanged.

For fixed two-stage workflows with an adequate application-specific effect
callback, evaluate the existing method before assuming a graph reduces model
roundtrips. Use the graph when its explicit states, prerequisites, yields and
retained transitions are needed; this trial does not establish their economic
benefit on larger workflows. General text verification, hover recovery, ordinary
desktop/other-domain coverage, actual model feedback timing and priced net-cost
comparisons remain open. No production algorithm or default route is changed
by this report. #57 and the broad product goal remain open.
