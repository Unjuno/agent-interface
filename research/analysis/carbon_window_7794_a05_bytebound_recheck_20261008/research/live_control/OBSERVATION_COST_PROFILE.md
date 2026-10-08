# Observation cost attribution changes the next experiment

The recent field task took68.49 s from initial capture to final evaluation, but
only1.91 s was inside completed runtime steps. All18 observation brackets total
1.15 s. Reducing capture work alone cannot explain away the tens of seconds spent
outside those measured execution steps. Prioritize reducing unnecessary outer
review/action boundaries before introducing a more complex capture-skipping policy.

This is attribution of preserved wall-clock records, not a claimed speedup or a
claim that every remaining millisecond is model inference. Tool startup, scheduling,
human-readable output generation/review, deliberate pauses, transport and work
outside the measured step spans are not separated in that residual.

## Existing mechanisms checked

- Exact unchanged-frame gating still captures/serializes pixels; it reduces image
  forwarding, not capture count. The frozen A1 report already establishes this.
- Current `session_v8` settle observes, checks pixel quietness, then waits at most
  20 ms before sampling again. QuietWindow includes actual frame pixels and focus;
  it does not establish semantic task completion.
- `session_v13` samples owner state around capture/publication. The first sampled
  state's start through observation emit-start gives a useful wall-time bracket,
  but omits entry work before that sample and output after emit-start.
- The existing presentation projector can omit intermediate images and has known
  transient-visual limitations. It was not enabled or promoted here.

## Same-trace measurements

`profile_observation_cost_v1.py` reconstructs and checks all48 exact PNG/AIT frames
across two recent Inkscape traces and one earlier Calc trace. It associates captures
with step-start/end events and compares actual decoded frames with the preceding
frame. It preserves per-observation and per-step measurements in its output.

| Preserved trace | Capture→evaluation | Completed steps | Observation brackets | Frames / exact repeats |
|---|---:|---:|---:|---:|
| field-table-live-01 | 68.491 s | 1.911 s | 1.145 s,18/18 covered | 18 /6 |
| gui-effect-live-01 | 99.725 s | 2.516 s | 1.266 s,19/19 covered | 19 /6 |
| presentation-assistant-02, Calc | 46.202 s | 1.290 s | unavailable,0/15 covered | 15 /4 |

Missing Calc brackets are unavailable timing, not zero observation cost. These
traces have different versions/tasks/conditions and cannot serve as a causal
cross-application comparison. Capture/image-publication measurements overlap the
bracket and must not be added to it. Initial bracketing starts slightly before the
initial capture boundary, so it is not an exact component partition of the entire
capture→evaluation interval.

For the latest X field edit, click/Ctrl+A/text/Return each produced one changed
frame. Settle produced four observations, two exact repeats. The whole edit's
step durations total about0.972 s; its observation brackets total about0.509 s.
Individual image captures took about3–4 ms, whereas changed-image publication took
about28–30 ms. A bracket also includes state/context/encoding work. These are wall
times, not CPU/GPU attribution. Exact repeats are known only after sampling; they
are not proof that the samples could safely have been skipped.

## Registered next comparison: existing multi-step execution

No new executor is needed for the first experiment. The current interface already
accepts up to16 bounded steps. Run one fresh familiar-layout Inkscape pair with the
same initial fixture seed223 and target X69.5, Y50/W40/H30, absolute tolerance0.01:

- A first: separate select(2 steps), edit(5), save(2), as in the current caller.
- B second: the identical nine ordered steps in one explicitly submitted program.

Both arms inspect the initial image and final saved image, retain all runtime
captures, full receipts and state companions, commit GUI judgments before independent
scoring, and independently score the saved geometry. A has the intermediate review
opportunities; B intentionally changes that interaction contract. A failed admission,
unexpected state, failed task or timeout must remain in the fixed pair, with no
silent rerun to obtain a clean result. Record all recovery actually needed.

Compare GUI decision time, task accuracy, actual socket/model-visible operation
boundaries, and observed recovery cost. Keep the program deadline/admission limits
unchanged. This ordered single pair is exploratory and conversation learning/model
configuration are not independently controlled: do not promote its timing as a
causal speedup. Unknown model tokens remain unknown. Capture savings are not the
hypothesis; all captures remain.

Bundling may remove opportunities to notice a wrong selection before later input.
Retained archives do not restore an intermediate intervention opportunity. A later
cross-domain/layout comparison and real focus/error interruption test are required
before broader adoption; the initial pair cannot establish those properties. Keep
default runtime behavior and Research Freeze unchanged. This protocol is registered,
not executed in this profiling turn.

## Reproduction

The output directory is exclusive and preserves original evidence:

```sh
python3 research/live_control/profile_observation_cost_v1.py
```

Results: `results/observation-cost-01/report.json`, with source-event hashes and
profiler hash. This profiler verifies frame reconstruction and timestamp ordering;
it is not a replacement for the existing task/transport audits. No new GUI session
was launched in this profiling turn.
