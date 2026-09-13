# Asynchronous live control: development evidence

Latest geometry result: [seed-991002 OpenTTD transfer](OPENTTD_GEOMETRY_V5.md).
The dynamic scorer derives target/forbidden/guard tiles from the baseline and
the new fixture moves the visible target. A preregistered negative control and
fixed-Astra episode both pass their declared gates. The positive run takes
89.097s with7 calls/114,177 input tokens/32 frames/24 durable calls. More
boundaries and tokens than the prior geometry are masked by shorter sampled
model waits, so no speedup or general-route claim is made.

Latest changed-state result: [pre-opened OpenTTD road toolbar](OPENTTD_INITIAL_STATE_V4.md).
One preregistered fixed-Astra episode retains the canonical task and independent
guard but changes the initial UI. It passes in89.272s with6 calls/97,696 input
tokens. The route skips main-toolbar discovery but spends the same total model
turns and durable calls on targeting confirmation. This is one UI-state transfer,
not a speedup, geometry generalization or human comparison.

Latest timing result: [typed OpenTTD finish outcome](OPENTTD_FINISH_V3.md).
A fresh zero-input/no-model control preserves independent score=false as a typed
failure with driver exit0. The same v3 path then completes a third fixed-Astra
episode in92.377s with6 calls/97,729 input tokens, taking the exact-task record to
3/3. Different task states and a human baseline remain.

Prior timing result: [matched OpenTTD replication](OPENTTD_MATCHED_MODELS_V2.md).
Across two preregistered blocks, fixed Astra passes2/2 in98.351s and94.929s,
adaptive passes1/2 and fixed Luna passes0/2. The new adaptive failure is a visual
completion false positive caught by the engine score. This rejects promotion of
the authored adaptive route; two episodes cannot promote Astra. Windows/WSL
audits cover47 model calls,172 durable calls and270 exact frames. New tasks,
fuller order balancing and the human baseline remain.

Prior timing result: [OpenTTD adaptive live control](TIMING_ENVELOPE_OPENTTD_V1.md).
One fresh v8 episode builds the guarded three-tile road and independently passes
all four checks in111.853s. It uses two Luna-low then six Astra-medium calls;
wrapper-observed model wait totals91.781s and actual reported input is126,420
tokens. Batched delayed-hover contact sheets preserve three tooltip observations
per planner boundary. The prior Calc envelope remains
[here](TIMING_ENVELOPE_V1.md). A human baseline and repeated matched blocks remain
before any speed claim.

Latest observation-boundary result: [actual pixel redaction](REDACTED_OBSERVATION.md).
One fresh Chromium frame yields exact text in 4/4 full calls and explicit policy
UNKNOWN in 4/4 redacted calls. V2 fixes and audits half-open region geometry;
metadata raises input by 112 tokens/call, so this is not compression evidence.
A follow-up completes the same adjacent visible Save task 2/2 under full,
unmarked-redaction and explicit-redaction conditions, with zero actions into the
hidden region and six independent successes.
A required-field mutation follow-up succeeds in the full condition and produces
zero post-observation input in both redacted conditions; both model calls stop
before the local gate. The first unsupported setup string is retained as an
atomic pre-input refusal.
A policy-race follow-up gives two fresh sessions the same full presentation and
prompt; both model calls propose the edit. The unchanged policy executes and
verifies, while a policy tightened after model return causes
`policy_binding_mismatch` and zero input. This proves one actual stale-proposal
refusal, while alternate-channel/history bypass remains.
The next seed254 session exercises that refinement: identical redacted pixels
produce stop without authority, then a new observation/policy permits one exact
whole replacement and Save. The task independently verifies, the private old
value is absent from model I/O, and stale replay refuses.
The follow-up presentation bundle accepts one current full-coverage redacted
artifact and refuses 13 crop/history/alternate-channel variants before model
delivery. Eight plan-shape controls exclude append, partial selection and
caller-supplied steps from whole-replacement authority.

Latest live integration: [bounded effect wait after a partial terminal](PARTIAL_TERMINAL_WAIT.md).
The model again distinguishes expiry before and after Return; one verifier query
replaces ten caller queries on the fresh-submission path.

Latest round-trip experiment: [bounded verifier wait](EFFECT_WAIT.md). One
declared long poll replaces ten caller checkpoint calls in a fixed delayed-effect
A/B while retaining explicit UNKNOWN/VERIFIED evidence.

Latest measured boundary: [partial-terminal live decisions](PARTIAL_TERMINAL_LIVE.md).
Two same-seed Chromium programs expire before versus after Return; strict evidence
drives one fresh submission versus zero-resend waiting and both finish with an
independent saved-value check.

Latest: [optional compact presentation and actual assistant pair](PRESENTATION.md)
in `interactive_v10.py`. Full output remains the default.

Latest trial: [bounded pixel-quiet observation](PIXEL_QUIET.md) in
`interactive_v9.py`. Quietness is advisory, never task completion.

Latest: [recovery observation and actual Calc modal transition](RECOVERY.md).
`interactive_v8.py` permits observation after ambiguous focus without granting
input authority to the same program's tail.

Latest experiment: [observed-focus binding and wrong-target probes](FOCUS.md).
`interactive_v7.py` is experimental; observe-only recovery still needs work.

Latest: [independent input release under blocked logging/capture](INPUT_OWNER.md).
The [interactive owner follow-up](OWNER_SELF_USE.md) adds `interactive_v6.py`
and records actual assistant use, including a retained Calc task failure.

Follow-up: [cooperative intent expiry and input-boundary fault injection](LEASE.md).
Use `session_v4.py` for the current lease experiment; other revisions retain
their original behavior and evidence.

Follow-up: [revision 2 decision boundaries and assistant trial](DECISION_BOUNDARY.md).
The description below records the original `session.py` revision.

This research prototype separates command reading from a single GUI execution
worker. A planner can submit a finite program, receive early acknowledgements
and observations, and request cancellation while the worker is active.
It uses the existing private Xvfb application fixtures and exact O2 transport.
It is not yet a general desktop runtime or a human-speed agent benchmark.

## What is implemented

- Whole-program validation and a private copy before any input; 1–16 steps.
- One active program, explicit identifiers and rejection of implicit queuing.
- Text, key, chord, held keys, public-window-title wait and observation steps.
- Held-key duration up to 5 seconds per step; combined hold/wait budget up to
  10 seconds. These are nominal bounds, not hard deadlines under blocking I/O.
- A separate cancellation reader, per-character/loop cancellation checks,
  key release on every terminal path, and X11 keymap release verification.
- Periodic observations during holds and title waits, exact packet decoding,
  PNG reuse and separate input/observation/terminal timestamps.
- Independent task scoring only after execution ends.

`completed` means the submitted program ended; it does not assert task success.
Title matching uses public X11 window metadata and is not visual-only control.
No idle observation stream, pointer control, focus/stale-state guard, hard
watchdog, disconnect lease or production protocol hardening is implemented.
Only trusted local JSON producers are in scope. Blocking capture, file output
or stdout can delay cancellation; these measurements do not establish a bound.

## Recorded development runs

| Run | Result | Interpretation |
|---|---|---|
| `development-01` | Initial reader failed before task input | An Xlib setup warning polluted stdout; retained source snapshots and events document the failure. Setup diagnostics were then separated from JSON. |
| `development-02` | 6/6 scripted tasks; 54 exact frames | XTerm and Calc, three seeds each. Tests cancellation, input release, invalid-tail/busy rejection and timeout stopping subsequent steps. |
| `development-03` | 6/6 scripted tasks; 54 exact frames | Fresh seeds 820301–820303 after copying accepted programs and rejecting unverified release. Same functional checks pass. |
| `dogfood-01` | Assistant missed cancellation; recovered task succeeds | The five-second hold finished and its trailing text ran before the assistant's cancel arrived. Cancellation reported `matched: false`. The assistant inspected the image, cleared the line with Ctrl+U and submitted the required token; independent output equals `t830101`. |

In `development-03`, server cancellation-request timestamp to verified key
release ranged from **0.50 to 20.79 ms** across six scripted probes. These are
local, uncontrolled development observations, not model response times or a
latency guarantee. See each `probe.json` and `events.jsonl`; source snapshots
and inherited source hashes are retained with the runs.

The actual assistant's missed cancellation is the important counterexample:
the cancel request arrived roughly **176.20 seconds after program completion**,
across a conversation context handoff. This is not a typical-latency estimate.
It shows why a responsive local cancel channel alone cannot ensure timely
planner intervention. The trailing `must-not-run` string was ordinary test
input, not an executor invariant: it ran because no cancellation had arrived.

Next design work should give movement intents an explicit expiry policy and
stop/deoptimize before actions requiring another decision. A normal finite
hold currently ends successfully and continues to the next submitted step.
Do not infer a lease or a semantic guard from its duration field.

## Reproduce

Run under the documented Ubuntu/WSL X11 research environment, from this folder:

```sh
python3 -m unittest test_executor -v
python3 probe.py --out results-local-fresh --seed 840101 --pairs 3
python3 session.py --app xterm --seed 840201 --out results-local-session
```

Choose unused output paths; generated local folders above are examples, not
ignored repository paths. Use the repository's `results-local/` directory for
unpublished work. The interactive process accepts newline-delimited JSON:

```json
{"op":"submit","id":"move-1","steps":[{"op":"hold","keys":["Left"],"duration_ms":1000}]}
{"op":"cancel","id":"move-1"}
{"op":"finish"}
```

Use pipes for machine consumption; the assistant's PTY adds terminal wrapping
to displayed output, while `events.jsonl` retains the original event records.
The ready event supplies the fixture task. `finish` cancels any active program,
then scores the actual application output and closes its private session.

Five executor unit tests and the fresh six-task live probe passed. A separate
unit test mutates the caller's accepted program while execution is paused and
verifies that the originally accepted steps run to completion.
This is a development record, without preregistered efficacy comparisons,
measured model tokens, a comparable human baseline or a DOOM run.

## OpenTTD changed-objective allocation

The [five-tile L objective](OPENTTD_L_OBJECTIVE_V1.md) changes the task from one
straight segment to two connected directional segments sharing a guarded
corner. Its seed-991003 fixture, two fresh restores, dynamic score and zero-input
negative control pass on Windows and WSL. The first preregistered Astra
allocation is retained as a harness failure before pointer input: the new driver
incorrectly supplied an identity that the durable journal owns. A separately
preregistered v2 fixes that path and runs eight actions, but Astra then falsely
declares completion. The B-to-C leg is correct; the A-to-B leg remains empty and
a four-tile road is built one map row above it. The independent score rejects
the run after 148.339 seconds and 146,736 reported input tokens. No task success
or speed result is claimed. The next candidate is magnified changed-region
feedback with full-frame fallback. Its archived diagnostic is now negative:
full-only and composite both return `uncertain`, while the composite costs 526
more reported input tokens. The next candidate is an explicit semantic-subgoal
checkpoint before the next mutation.

That checkpoint has now run live. It prevents a second task mutation and the
earlier false verify, but Astra spends 11 turns and 182,284 input tokens before
an uncertain safe stop; the task remains incomplete. The frozen checkpoint-v1
parser incorrectly rejects that stop, and checkpoint v2 fixes the rule in
cross-OS probes. A no-model Ctrl+2 recovery probe makes the obstructing trees
transparent while preserving every scored road/owner field and save bytes.
Exposing that verified view method to the planner is the next live candidate.

That live candidate now exists. Fixed Astra calls the typed tree-transparency
method three times, performs no task mutation after its first drag and safely
stops on turn 12. It consumes 198,746 input tokens and does not complete the
task. The repeat calls reveal that a toggle is the wrong typed abstraction.
Fresh zero-model calibration shows the model's offset-0 drag coordinates can
build intended tiles 977..979, and the tool state survives a 15-second program
boundary. `semantic_checkpoint_v4.py` replaces the method with a tracked,
one-way `openttd.ensure_trees_transparent` candidate and refuses repeat or
unknown-state use. Its admission probe passes on Windows and WSL. Fresh model
efficacy is now measured: a preregistered v5 allocation applies the transition
before turn1 in428.854ms with no model boundary. Astra uses7 turns/115,045 input
tokens, but falsely verifies after placing A-to-B one row high. V6 adds only the
general sign-to-map-square relation and uses12 turns/199,613 tokens with no
verify or safe stop. The driver exits at its proposal limit before consuming
the abort, leaving the formal finish outcome unavailable. A later posthoc audit
of263 continuous observer records proves partial A-to-B construction and a
missing B-to-C leg. The model repeats the same A-to-B drag three times. See
[OPENTTD_EFFECT_POSTHOC_V1.md](OPENTTD_EFFECT_POSTHOC_V1.md). The run remains a
hard failure and no retry was made.

That finish handshake is repaired in `timing_envelope_openttd_l_driver_v5.py`.
The model-free limit probe reaches12 observe-only proposals and records the
independent bounded failure with50 durable calls,39 observations and exit0.
Ctrl+1 sign-transparency probes then preserve task/save state while changing
custom sign presentation on the L fixture and held-out seed991002 geometry.
Because normal simulation progress is present between frames, treat the paired
view as feasibility only. See [OPENTTD_VIEW_PAIR_V1.md](OPENTTD_VIEW_PAIR_V1.md).

The paused held-out probe isolates that view change to1,151 pixels after an
exact zero-change stability frame. A fixed Astra A/B/B/A endpoint diagnostic
then passes2/2 for opaque signs and2/2 for transparent signs, with30,572 input
tokens per condition. The sign transform has no detected grounding/token benefit
and is not promoted. Next target live tool/effect-state evidence.

That retained effect-state audit now exists. The final172 observer records keep
owned road on tiles977..979 while1043/1107 remain empty, with forbidden and
surrounding checks intact. Automatically derived drag-region sheets measure
3,628 changed pixels on the first A-to-B drag versus250/451 on its repeats.
These pixels do not score construction; the independent observer does. Next use
the evidence builder in a changed preregistered live comparison.

The first such live allocation succeeds. V7 keeps the seed991003 task,
Astra-medium route, checkpoint rules and engine scorer, then adds the current full
frame plus bounded drag before/after/difference panels. Turn6 recognizes A-to-B
and builds B-to-C; turn7 independently verifies the complete L. The run uses7
turns,116,879 input tokens,26 durable calls,32 frames and109.034s, with zero
repeated A-to-B drag. Retained v6 failed after12 turns/199,613 tokens and two
repeats. See [OPENTTD_EFFECT_LIVE_V1.md](OPENTTD_EFFECT_LIVE_V1.md). Retain for
replication; this one sequential same-task result is not a general speedup.
