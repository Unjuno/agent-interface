# Progress from the initial baseline

Status date: 2026-09-14. This is an evidence-based progress map, not a release
claim. The repository grew from an initial coordinate-and-screenshot research
baseline into a Linux/X11 control candidate with durable recovery, scoped local
execution and independent effect checks. It still does not deliver human-tempo
general computer use or an installable Agent Market product.

## What changed

| Stage | Initial state | Current evidence | Status |
| --- | --- | --- | --- |
| Observation | Repeated full screenshots around individual actions | Exact unchanged-frame suppression, exact tile transport, changed-region and compact planner views | Proven in scoped fixtures; general visual/token policy remains experimental |
| Input | Coordinates and short scripted keyboard/pointer actions | Absolute intent deadlines, focus/surface binding, held input, cancellation/expiry, verified release and tail suppression | Strong scoped Linux/X11 evidence |
| Execution | One action followed by another model boundary | Bounded multi-step programs, phased submit, passive followups and local continuation | Working in selected desktop/game tasks; semantic replans still need the model |
| Freshness | Screenshot age was mostly implicit | Observation identity/age, stale refusal, route and binding guards, re-observation after interruption | Mechanism exists; model delay can still age a frame by seconds |
| Recovery | Transport uncertainty risked repeated work | Durable journal, request IDs, read-only outcome recovery and lost-query reconciliation without resend | Live input and saved-effect recovery demonstrated |
| Completion | Program completion could be mistaken for task success | Program terminal, application effect and independent task score are separate states; UNKNOWN is preserved | Demonstrated on Calc, Chromium, Inkscape and game fixtures |
| Model evidence | Full durable records were passed to the planner | Strict typed compact view retains action/effect authority and retry rules | Fixed 16-call check passed; first live action passed; adversarial adoption gate remains |
| Benchmarking | Four small desktop fixtures | Domain matrix spans desktop apps, DOOM, Mindustry, OpenTTD and Luanti | Useful breadth; no formal benchmark suite or aggregate score yet |

The initial repository snapshot dates to 2026-09-12. Iteration volume is not a
progress metric; the claims above depend on retained runs, source hashes,
negative controls and independent audits.

## Closest current live loop

The newest Chromium episode is the clearest small end-to-end sample. A fresh
screenshot and a 621-byte strict compact UNKNOWN record drove one real model
decision. The resulting program saved the exact requested value, survived two
deliberately abandoned saved-effect query connections through read-only recovery,
and reached independent evaluation in 9.706 seconds from the first runtime
capture. The model runner consumed 6.542 seconds; the caller handoff consumed
230 ms. This is one sample, not a latency distribution or human comparison.

Earlier actual-use samples were slower: the current-runtime known Mindustry bend
task took 84.967 seconds to its final input terminal and 117.358 seconds to
independent evaluation, with 18–23 second gaps between programs. The corrected
OpenTTD visual placement took 43.42 seconds to its last terminal. These numbers
include model/tool/host gaps and show why local millisecond execution alone does
not yet produce ordinary human interaction tempo.

The present bottleneck is the semantic boundary. Local admissions, cancellation,
recovery reads and feedback production commonly operate in milliseconds to
hundreds of milliseconds, while model decisions in recent measured samples take
seconds. The architecture now has enough correctness structure to reduce the
number and size of those boundaries; it has not yet shown that reduction across
unseen, long-running tasks.

## Domain coverage

Each domain exposes a different weakness. There is no single king benchmark and
the rows must not be averaged into one difficulty score.

| Domain | What has actually been shown | Main missing proof |
| --- | --- | --- |
| Desktop apps | Small Calc, Chromium, Inkscape and XTerm tasks; dialogs, focus loss, interruption, saving and independent effect checks | Unknown applications, richer window/scroll/drag workflows and repeated held-out tasks |
| DOOM | Shared held-key/cancel/expiry readiness and later directional-input repair/assistant gameplay evidence | Stable continuous useful-feedback loop, reaction distribution and public real-time demo |
| Mindustry | Actual assistant construction of eight directed conveyors on a known route; 112-tile guard and 49-copper post-control delivery; shared caller scripted replay and cancellation | Fresh route planning, multi-object control, event-driven recovery and much shorter decision gaps |
| OpenTTD | Actual visual toolbar/drag placement; corrected 42-tile side-effect guard; shared caller scripted replay | Fresh repeated GUI tasks, scroll/window complexity and long-horizon transport planning |
| Luanti | Current-engine launch, deterministic tiny pad/pose and read-only node/pose feasibility | Normal navigation, camera-mode contract, inventory, interaction and successful construction |

DOOM remains valuable for continuous motor pressure. Mindustry and OpenTTD are
already catching errors that an FPS benchmark would miss: long planner gaps,
overlong placement drags, local side effects and resource-flow completion.
Luanti remains a feasibility candidate rather than demonstrated agent control.

## Quantified evidence so far

- Sparse reactive control reached 8/8 development-screen successes in each of
  XTerm, Chromium, Calc and Inkscape.
- Exact unchanged-frame suppression preserved 96/96 tasks per strategy and cut
  same-trace image count by 17.15%, with zero measured false suppressions.
- Exact tile transport preserved 32/32 tasks per strategy and cut serialized
  bytes by 70.73% across 553 exactly reconstructed frames. This is transport
  reduction, not a token or latency claim.
- The strict compact planner experiment preserved the expected decision in 8/8
  full and 8/8 compact calls. Reported input fell from 80,564 to 77,880 tokens,
  a 3.33% reduction across the fixed calls. The first fresh live compact-driven
  form action then succeeded with one model call.
- A same-image delayed-effect comparison exposed a compression limit. Retaining
  prior execution used 9,759 input tokens/call and produced wait/check 4/4;
  omitting it used 9,485 but represented a different state and produced
  submit-once 4/4. Those 274 tokens are necessary semantics in this case.
- One fresh live follow-up used that evidence to choose wait/check while the
  delayed effect progressed. Model computation took 6.494 seconds, leaving zero
  additional sleep; one read-only checkpoint then verified the exact value with
  no post-UNKNOWN input. This is overlap evidence from one authored task.
- Two fresh same-seed partial-terminal cases expired before versus after Return.
  Strict evidence drove submit-once for the 3/6 prefix and wait/check for 4/6;
  only the former admitted new input and both independently succeeded. The new
  submission needed ten effect polls, so event-driven readiness remains missing.
- A fixed follow-up replaced those ten caller queries with one bounded verifier
  query. Both fresh tasks succeeded; post-UNKNOWN detection fell from 5,060.458
  to 4,897.769 ms. The worker still made 97 filesystem samples, so this proves
  round-trip reduction rather than event-driven readiness or compute savings.
- Lost-response recovery has been exercised for input outcomes and saved-effect
  queries. The current form episode recovered two queries by identity with zero
  resend and admitted no input after VERIFIED.

## Distance to the stated goal

| Goal gate | Current assessment |
| --- | --- |
| Trustworthy low-level Linux/X11 control | Substantial scoped evidence; still a research candidate |
| Continuous live model operation | Partial; works in bounded episodes, but seconds-long semantic gaps dominate |
| Human-like speed and iteration | Not demonstrated |
| Broad task judgment | Not demonstrated; successful tasks are small and often known during development |
| Token-efficient operation | Small measured planner-input reduction; large image transport reduction has not become an equivalent model-token reduction |
| Cross-platform Windows/macOS | Outside the current architecture-discovery scope and untested |
| Easy installation and agent-agnostic API | Design intent only; no runnable distribution |
| Product Hunt / Agent Market demonstration | Research material exists; public demo and product packaging are not ready |

The adversarial boundary rejects nine wrong or missing request/contract cases
before model delivery. Corrected delayed and partial-terminal experiments now
show that prior execution and the completed prefix change wait-versus-submit
decisions in three fresh states. The next promotion gate covers conflicting
evidence and actual redacted observations, followed by current-runtime Mindustry/OpenTTD
tasks with new geometry and the same recovery semantics. Human baselines and
model-boundary timestamps must then be collected on identical task allocations.
Only after those pass should the runtime/API be frozen and packaged.

Primary evidence: [research index](../RESEARCH.md), [current architecture](architecture.md),
[domain feasibility](../research/benchmark_discovery/README.md),
[Mindustry current-runtime self-use](../research/benchmark_discovery/MINDUSTRY_BEND_V2_SELF_USE.md),
[OpenTTD guarded placement](../research/openttd_task/GUARDED_PLACEMENT.md),
[compact fixed comparison](../research/live_control/COMPACT_PLANNER_EVIDENCE.md), and
[compact live form](../research/live_control/COMPACT_LIVE_FORM.md), and
[delayed-effect decision evidence](../research/live_control/DELAYED_EFFECT_DECISION.md), and
[model-driven delayed-effect live use](../research/live_control/DELAYED_EFFECT_LIVE.md), and
[partial-terminal live decisions](../research/live_control/PARTIAL_TERMINAL_LIVE.md), and
[bounded effect wait](../research/live_control/EFFECT_WAIT.md).
Latest round-trip candidate: a same-seed fresh Chromium A/B compares 500ms caller
polling with one6000/50ms verifier wait. Both independently save t000246. The
post-UNKNOWN path changes from10 durable calls/5060.458ms to1/4897.769ms; total
calls15->6. It retains10 exact frames per episode and passes14 invalid controls
plus cross-OS audit. The verifier still makes97 filesystem samples and holds the
single-writer exchange; no event-subscription, CPU/IO, token or model benefit is
claimed. See research/live_control/EFFECT_WAIT.md.

Latest partial-terminal evidence: two fresh Chromium sessions with the same seed,
goal and page expire at3/6 before Return versus4/6 after Return. Luna-low chooses
submit_once versus wait_and_check; only the former gets one fresh-admitted input
program, and both independently save t000245. Model runners8.143/6.126s,
input9803 each, expired admission-to-VERIFIED15.423/7.602s. The first path needs
ten post-decision queries; the second needs one and admits zero new input. Exact
frames, raw model events, effects and calibration failures audit cross-OS. See
research/live_control/PARTIAL_TERMINAL_LIVE.md. Authored absent-title expiry and
explicit boundary prompt; no broad reliability or human-tempo claim.
