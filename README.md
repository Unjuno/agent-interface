# Agent Interface

**A faster interface between AI agents and computers.**

> **Research thesis:** AI agents are becoming highly capable, but the computer-control tools they use are still primitive. If the model is held fixed, a better interface should let the same agent use computers with less waiting, fewer redundant observations, fewer model boundaries, and less recovery work at the same correctness.

> **Status: Research Preview.** This repository is the public research record. User-facing GitHub Releases will be reserved for runnable distributions that people can actually download and try.

[Landing page](https://unjuno.github.io/agent-interface/) · [Principles](docs/principles.md) · [Research index](RESEARCH.md) · [Architecture](docs/architecture.md) · [Roadmap](ROADMAP.md) · [Open an idea](https://github.com/Unjuno/agent-interface/issues/new?template=idea.yml)

Current progress from the initial baseline: [achieved capabilities, measured
bottlenecks and remaining release gates](docs/PROGRESS_FROM_BASELINE.md).

Latest research handoff: [measured progress, failures and next steps](docs/LOCAL_RESEARCH_HANDOFF.md).

Current Linux research caller: [components, usage and evidence limits](research/live_control/CURRENT_CLIENT.md).
The first preregistered live bounded-effect allocation now completes the OpenTTD
five-tile L objective. After the first drag, the interface appends path-local
before/after/difference panels below the current full frame. Fixed Astra recognizes
A-to-B, proceeds directly to B-to-C and passes the independent guard in7 turns,
116,879 input tokens and109.034s. The retained v6 baseline used12 turns/199,613
tokens, repeated A-to-B twice and failed. This is one sequential same-task result;
retain for replication, with no causal percentage or general speed claim. See
[live effect evidence](research/live_control/OPENTTD_EFFECT_LIVE_V1.md).

An unchanged preregistered replication then builds A-to-B once but cannot resolve
the effect beneath sign/transient occlusion. It performs two observation-only
inspections and safely stops on turn8, with no repeated A-to-B mutation. The
candidate is now1/2 for same-task hard success and2/2 for preventing that repeated
completed-segment drag, so it remains HOLD. The run also exposes and repairs a
finish classifier that mislabeled typed safe stop as a turn limit. See
[effect replication](research/live_control/OPENTTD_EFFECT_REPLICATION_V2.md).

The diagnosed presentation boundary discarded the original drag evidence after
each inspection-only turn. A bounded effect-memory candidate now carries one
unresolved drag as original before/after, latest inspection and action difference.
In two preregistered archived v8 contexts, the raw outputs are uncertain2/2 while
new Astra-medium samples with memory classify observed2/2 and choose the same
B-to-C continuation. Input rises764 tokens across the two calls. This is a fixed-
context signal for a fresh live test, not promotion or a correctness claim. See
[bounded effect memory](research/live_control/OPENTTD_EFFECT_MEMORY_V1.md).

The first preregistered fresh live allocation of that memory independently passes
the five-tile L score. It inspects once after each of two distinct drags, carries
the matching effect across both inspection boundaries and verifies on turn9.
There are zero repeated completed-segment drags and all17 terminals release input.
The episode costs151,853 input tokens and153.027s to semantic completion, slower
than v7. Retain for unchanged replication; do not promote. See
[live bounded effect memory](research/live_control/OPENTTD_EFFECT_MEMORY_LIVE_V1.md).
An unchanged preregistered replication follows the same two inspect/resolve
boundaries and independently succeeds on turn9. The live memory candidate is now
2/2 hard success and2/2 zero completed-segment repeats. V10 uses151,842 input
tokens and160.837s, so the speed deficit remains. Advance to changed geometry,
without promotion. See [memory replication](research/live_control/OPENTTD_EFFECT_MEMORY_REPLICATION_V2.md).

The first changed-geometry allocation uses a new seed991004 save and moves the
five-tile L contract to tiles684,685,686,750,814. The two distinct drags complete
the task with zero surrounding changes and zero repeated completed-segment input,
but Astra needs five inspection turns to accept the first effect and leaves the
second uncertain at the12-turn bound. The independent engine score succeeds;
controller-verified hard success does not, and semantic completion time is not
recorded. The run uses204,114 input tokens,195.604s model wait and50 durable
calls. A separate selector repairs the discovered result/failure filename
assumption in offline cross-OS controls. Hold the memory candidate and repair
completion feedback before another live geometry run. See
[changed L geometry](research/live_control/OPENTTD_EFFECT_MEMORY_GEOMETRY_V3.md).

A preregistered fixed-context follow-up rejects the first pixel-only effect
receipt prompt. Exact-prompt Astra recognizes the retained road effect2/2,
while the receipt condition remains uncertain2/2 and adds156 input tokens per
call. No live action is run. The next candidate will use an agent-authored visual
postcondition as a local in-program barrier, separate from input authority. See
[persistent visual-effect receipt](research/live_control/PERSISTENT_EFFECT_RECEIPT_V1.md).

The first local in-program form is also rejected by a fresh X11 correctness
control. It requests a24px Inkscape move but reaches12px; a single-ROI threshold
still counts163 persistent pixels and starts the later Save step. The paired
unmet condition correctly stops before Save, and all input releases verify.
Changed-pixel totals remain advisory only; continuation requires a task-relative
visual condition. See
[local visual continuation barrier](research/live_control/LOCAL_VISUAL_BARRIER_V1.md).

A target-relative replacement then passes one fresh X11 met/partial pair. After
bounded settling, two immutable-anchor samples admit Save for an independently
reconstructed24px move and stop before Save for a20px partial move. The target
SVG preserves the requested displacement;18 frames and both release terminals
audit cross-OS. This covers scripted object displacement only; whether a model
can author the condition remains untested. See
[local displacement postcondition](research/live_control/LOCAL_DISPLACEMENT_POSTCONDITION_V1.md).

Process-scoped timing envelopes now cover fresh Calc and OpenTTD tasks. Calc
saves 480/192 in 23.976s with 21.334s of wrapper-observed model wait. OpenTTD uses
batched delayed-hover contact sheets and an adaptive two-Luna/six-Astra route to
build a guarded three-tile road in111.853s with91.781s of model wait and126,420
reported input tokens. The OpenTTD task independently succeeds in two fresh
runs, although the first run exposed a result-schema packaging failure after
the positive score. Two matched blocks find fixed Astra2/2, adaptive1/2 and fixed
Luna0/2. A third fixed-Astra episode passes in92.377s with6 calls, taking its
same-task record to3/3. The second adaptive run falsely declares visual completion
before the independent score fails. A fresh v3 control now preserves that negative
score as a typed failure instead of an assertion. Different task allocations and
a human control remain before any route or speed claim. A preregistered fourth
fixed-Astra episode changes the initial UI by pre-opening Road Construction and
passes in89.272s with6 calls/97,696 input tokens. It removes toolbar discovery
but still uses the same number of model turns and durable calls because targeting
confirmation expands. This is one changed UI state, not a speedup or new-geometry
result. A subsequent preregistered seed-991002 task moves the engine contract
from tiles678..680 to465..467 and shifts the visible target. Fixed Astra passes
in89.097s, but uses7 turns,114,177 input tokens,32 frames and24 durable calls:
more interface work than the prior geometry despite a shorter sampled wall time.
The geometry-derived scorer is retained; no speed or general-route claim follows.
The next seed-991003 allocation changes the objective to a five-tile L with two
directional segments and a shared corner. Its fixture and negative control pass,
but the first preregistered Astra allocation stops before pointer input when its
new driver violates the durable journal identity contract. That harness failure
is retained without retry. A separately preregistered corrected allocation runs
eight actions, but Astra falsely verifies completion after 148.339s and 146,736
reported input tokens. The B-to-C leg is correct; the A-to-B leg is empty and a
four-tile road appears one map row above it. The route is rejected.
A checkpointed allocation prevents the second mutation and false verify, but
uses 11 turns/182,284 input tokens before an uncertain safe stop; it does not
complete the task. A model-free Ctrl+2 probe then makes the obstructing trees
transparent while independently preserving all road, owner and save state.
Exposing it as a typed method keeps a fresh allocation free of additional road
mutations, but Astra calls the toggle three times and safely stops on turn 12
after 198,746 input tokens without completing the task. Fresh scripted
calibration shows five nearby offsets build the intended A-to-B tiles and that
the tool state survives a 15-second program boundary. The next contract changes
the toggle into a one-way, state-aware pre-action view method.
The tracked pre-action OpenTTD view transition now has live evidence. It costs
428.854ms and adds no model boundary. Astra reaches a rejected verify in7 turns
and115,045 input tokens, down from v4's12/198,746, but again builds A-to-B one
row high. A follow-up adding only general sign-to-map-square semantics reaches
the12-turn limit with199,613 tokens and no verify or safe stop. Its formal finish
outcome is unavailable because the driver exits before consuming the limit
abort. A posthoc audit of263 continuous source-pinned observer records proves a
stable partial result: A-to-B is built, B-to-C remains empty and the model repeats
the same A-to-B drag twice. The failure is retained without retry; prose-only
anchoring is not promoted. See [effect-state diagnosis](research/live_control/OPENTTD_EFFECT_POSTHOC_V1.md).

The v6 limit-path evidence gap is repaired in driver v5: a model-free live probe
applies12 observe-only proposals, accepts the supervisor stop, emits an
independent `bounded_turn_limit` result and exits0. A separate zero-model view
study finds Ctrl+1 changes custom sign presentation on both seed991003 L and
held-out seed991002 straight geometry without changing scored task/save state.
Normal game progress contaminates full-frame difference counts, so this remains
an unpromoted paired-observation candidate pending a paused matched comparison.

The paused comparison now isolates1,151 changed pixels after a zero-change
stability frame. In a fixed Astra A/B/B/A targeting diagnostic, opaque and
transparent sign views both pass2/2 and each use30,572 input tokens. No
grounding or token benefit is detected, so the sign transform is not promoted.

The newest observation-boundary study physically withholds one live Chromium
region: full input reads the exact value 4/4 and redacted input preserves explicit
policy UNKNOWN 4/4. The region geometry audits exactly, but metadata adds 112
input tokens/call. A six-episode follow-up completes the adjacent visible Save
task in all three full/unmarked/explicit conditions with zero hidden-region
actions. A required-field mutation succeeds only with full evidence; both
redacted conditions stop with zero live input. A later same-prompt pair binds
the model proposal to its observation and policy version: a stable policy
executes and verifies, while a policy tightened after model return rejects the
model's actual edit proposal before any input. Crop/history/alternate-channel
bypass cases remain open. A subsequent scoped
refinement keeps the old value hidden but permits one exact whole replacement:
the unprivileged model call stops, the newly bound call executes and verifies,
and replay against the old policy is refused.
Pre-model bundle controls also refuse 13 crop/history/alternate-channel and
binding variants, while eight strict proposal controls exclude append, partial
selection and caller-supplied steps. These are scoped offline controls over the
live artifact, not a deployed privacy claim.
The assistant has used received-image references and bounded programs in Calc
and browser fixtures. An optional final-result read collected ready Calc early
and final evidence in one caller invocation, and skipped itself on a browser
direct-final result. These are small research episodes, not proof of general
speedup or human-like tempo; outer decision waits remain measured in seconds.

Recent recovery candidate: [bounded followup after input interruption](research/live_control/CALC_COMBINED_LIVE.md). In one actual Calc task, the caller collected short passive followups inside the original operation, avoiding two separate followup invocations while preserving interruption reasons and correct saved values. Socket round trips remained unchanged. This is an optional research path with report-compatibility work outstanding, not a general speed or token-saving claim.

## The hypothesis

Most computer-use systems still resemble:

```text
model -> one action -> screenshot -> model -> one action -> screenshot -> ...
```

Agent Interface asks whether the interface, not only the model, is now a major bottleneck:

```text
strong planner
    -> semantic method / short reactive program
    -> guarded local execution
    -> immediate useful feedback
    -> observe only meaningful change
    -> deoptimize only the stale layer
    -> return to the model when semantics require it
```

The clean experiment is simple:

```text
same model
same task
same environment
same correctness requirement

only the interface changes
```

Then measure model boundaries, serialization, observation cost, latency, retries, recovery, and eventually real token use separately.

## Component principles

The eventual tool should satisfy four constraints from the start:

1. **Install quickly.** A user should be able to install or unpack it, start it, connect an agent, and use it without app-specific setup.
2. **Work with every agent.** The core should be model- and vendor-agnostic. Model-specific adapters belong outside the runtime core.
3. **Do not stop the agent's thinking.** After an action, return the earliest trustworthy feedback instead of blocking on fixed waits or unnecessarily complete observations. Reduce **agent idle time**.
4. **React locally.** Input delivery, state-change detection, local verification, retry, and fine motor correction should stay in the local fast path when they do not require semantic reasoning.

Full rationale: [`docs/principles.md`](docs/principles.md).

## Ideas shaping the system

| Idea | Why it exists | Expected effect | State |
|---|---|---|---|
| **Universal fallback** | Optimizations must never be required for basic correctness | Unknown apps still work | Baseline |
| **Self-compiling semantic methods** | Repeated successful traces should not be replanned forever | Fewer model turns / less serialization | Baseline |
| **Layered lifetimes** | A stale coordinate, binding, or visual cache does not imply the task meaning changed | Less relearning | Promoted |
| **Guarded Hierarchical Deoptimization** | Predictably stale fast paths should be skipped before failure | Better reliability / lower tail latency | Promoted |
| **Latest-only visual state** | Old frames are not extra evidence about the current GUI | Less stale-state processing | Runtime principle |
| **Event-driven observation** | Polling without state change creates work but no information | Fewer captures / faster feedback | Experimental baseline |
| **Observation gating** | An unchanged or irrelevant screen should not consume another model-visible image | Lower visual/token cost | Active research |
| **Visual delta / changed-region feedback** | A small local change does not justify resending the whole frame | Lower visual bandwidth | Active research |
| **Local verification** | Deterministic postconditions do not always need model interpretation | Fewer model escalations | Active design |
| **Input delivery semantics** | Sending an OS event is not the same as application consumption | Higher correctness | Measured |
| **Closed-loop motor control** | Pointer movement and on-screen movement are not always identical | Better fine control | Experimental |

## Current evidence

These are scoped research measurements, not production claims.

| Experiment | Result | Scope |
|---|---:|---|
| Sparse reactive control | B1 reached 8/8 success on XTerm, Chromium, Calc, and Inkscape in the development screen | Linux/X11, small `n=8/app` |
| Route-level deoptimization | Inkscape observation reduced **51.9%** and planner-byte proxy **27.8%** vs method invalidation | 72 hidden episodes |
| XTerm focus guard | p99 reduced about **77.5%** | 72 hidden episodes |
| Chromium geometry guard | p99 reduced about **75.4%** | 72 hidden episodes |
| Layered binding + route guards | 72/72 success with predictable stale-route execution eliminated before execution | Chromium drift + process replacement |
| Exact unchanged-frame suppression (O1) | 96/96 tasks per strategy; 17.15% same-trace image reduction; zero false suppressions | [Four real apps, 24 fresh pairs/app](research/observation_gating/REPORT.md); scripted controller, no model/token measurement; local speedup unproven |
| Exact tile transport (O2) | 32/32 tasks per strategy; 70.73% same-trace serialized-byte reduction; 553 exact frames | [Four apps, 8 fresh pairs/app](research/observation_tiles/REPORT.md); reconstructed full images, no token saving or local speedup established |
| Assistant-operated research interface | Calc, Inkscape and XTerm tasks completed through reconstructed images; feedback wait and PNG-reference reuse exercised | [Three exploratory sessions](research/observation_tiles/DEVELOPMENT.md), not a controlled model performance comparison |

Raw reports and CSVs are under [`research/`](research/). `planner bytes` are not tokens, `observed pixels` are not image tokens, and local wall time is not model-in-loop latency.

## Repository map

```text
.
├── README.md                  # project entry point
├── RESEARCH.md                # evidence ledger
├── ROADMAP.md                 # research sequence
├── docs/
│   ├── README.md              # documentation index
│   ├── principles.md          # thesis + component principles
│   ├── architecture.md        # current promoted architecture
│   └── product-hunt.md        # launch notes
├── research/
│   ├── requirements.txt       # research-only Python dependencies
│   ├── real_apps_v1/          # input delivery + sparse reactive control
│   ├── real_apps_v2/          # method lifetime vs route lifetime
│   ├── real_apps_v3/          # guarded hierarchical deoptimization
│   ├── observation_gating/   # frozen O0/O1 experiments and raw evidence
│   └── observation_tiles/    # exact transport, assistant use and image preparation
├── runtime/
│   └── README.md              # future runnable runtime workspace
├── release/
│   └── README.md              # user-facing release contract
├── site/                      # GitHub Pages landing page
└── .github/
    ├── ISSUE_TEMPLATE/        # idea / research proposal / bug forms
    └── workflows/             # Pages + manual research archive
```

## Reproducing the research

Current real-app harnesses target Linux/X11 and can inject real keyboard and pointer input. Use an isolated X session or disposable container.

```bash
python -m pip install -r research/requirements.txt
python research/real_apps_v1/real_app_suite_v1.py --help
```

Read [`RESEARCH.md`](RESEARCH.md) before interpreting benchmark numbers.

## Ideas and contributions

This project explicitly accepts design ideas, not only bug reports.

If you can remove unnecessary observations, model calls, serialization, retries, latency, or fragile assumptions **without removing information the agent needs**, open an [Idea issue](https://github.com/Unjuno/agent-interface/issues/new?template=idea.yml).

A useful idea can be simple:

1. What work or information flow is wasteful today?
2. What is the smallest mechanism that removes it?
3. Why should correctness or precision be preserved or improved?

If it is mature enough to benchmark, use the stricter [Research proposal](https://github.com/Unjuno/agent-interface/issues/new?template=research-proposal.yml) form.

## Repository vs Releases

- **Repository:** research, experiments, rejected ideas, benchmarks, design notes, and evolving implementation work.
- **GitHub Releases:** future runnable distributions a user can download, install/unpack, and actually try.
- **Historical `v0.0.1-research.*` tags:** archival snapshots created while bootstrapping the public research record; not the target user-distribution format.

The user-release contract is documented in [`release/README.md`](release/README.md).

## What is not proven yet

- Cross-platform generality beyond current Linux/X11 evidence.
- Production-grade automatic method discovery.
- End-to-end real model/token savings.
- Stable runtime/API semantics.
- A finished user-facing runtime distribution.

Python remains the experimentation vehicle while semantics are changing quickly. A lower-level production implementation comes after the algorithmic boundary stabilizes.

## Research discipline

Every promoted change should define H/T/D/C/U: hypothesis, minimum test, decision rule, competing explanation, and uncertainty. Correctness is a hard gate. Small noisy wins are not promotions. Negative results remain part of the record.

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
