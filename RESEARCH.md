# Research index

Agent Interface is being developed by experiment, not by locking an API early. This file is the evidence ledger for the public repository.

## Research question

Can a strong planner control arbitrary GUI applications through a local interface that:

- works on an unknown app immediately,
- reduces model boundaries and repeated observations,
- learns reusable routes from successful use,
- survives UI/environment drift by invalidating only stale layers,
- and preserves correctness as a hard gate?

## Experimental ladder

### Compact planner evidence and caller binding

Path: [`research/live_control/`](research/live_control/COMPACT_PLANNER_EVIDENCE.md).
Sixteen fixed-image model calls preserved 8/8 expected decisions in both full and
compact conditions while reported input fell 3.33%. One fresh compact-driven
Chromium action then completed with independently verified saved output and two
lost checkpoint replies recovered without resend. The newer v3 presenter binds
the checkpoint to the caller's expected request ID and completion contract;
nine adversarial identity/contract controls refuse before model delivery. A
partial-evidence model comparison is retained as confounded because its common
prompt disclosed the fact removed from one condition. None of this establishes
general reliability, human tempo, privacy-safe redaction or default adoption.

Primary artifacts:

- [`COMPACT_PLANNER_EVIDENCE.md`](research/live_control/COMPACT_PLANNER_EVIDENCE.md)
- [`COMPACT_LIVE_FORM.md`](research/live_control/COMPACT_LIVE_FORM.md)
- [`PLANNER_EVIDENCE_BINDING.md`](research/live_control/PLANNER_EVIDENCE_BINDING.md)

### First DOOM-engine transfer

Path: [`research/doom/`](research/doom/README.md). The assistant used X11 screenshots
and OS keys in ViZDoom/Freedoom's basic room, reaching completion in two development
runs. An async-clock probe is consistent with 35 tics/second; 50 recorded frames
audit exactly across three operated sessions. Initial window, cached-telemetry
and binding failures are retained. This is not full-game or human-speed evidence.

### Moving-screen tracking — local visual motor feedback

Path: [`research/visual_tracking/`](research/visual_tracking/README.md).
Twelve frozen synthetic X11 episodes compare the same pixel-based policy at
50 ms local updates versus 250/1000 ms decision cadence. All completed with
verified release; application-side scoring favored local updates in all six
pairs. One assistant-selected local method also completed. This is a narrow
dynamic motor study, not LLM inference overlap, generic GUI understanding,
human comparison or a DOOM result. Failures and raw scoring records are retained.

### Live control — asynchronous functional prototype

Path: [`research/live_control/`](research/live_control/README.md).
A separate command reader and GUI worker support early feedback, held inputs,
cancellation and verified key release. The latest six scripted XTerm/Calc
probes passed with 54 exact frames. Local cancel-to-release observations ranged
from 0.50 to 20.79 ms; this is not model end-to-end latency or a speedup claim.
An actual assistant cancellation arrived after the program ended; the raw
failure and successful GUI recovery are retained. Intent expiry and stale-state
guards remain necessary before claiming dependable real-time planner control.

### Real Apps v1 — input delivery and sparse observation

Path: [`research/real_apps_v1/`](research/real_apps_v1/)

Apps: XTerm, Chromium, LibreOffice Calc, Inkscape.

What it established:

- fixed `100 ms` sleeps do not guarantee correctness;
- input delivery and application consumption are different events;
- Calc required about `1 ms` character pacing in the tested X11 setup;
- Inkscape long-run drag stability improved when the press-to-motion barrier was increased from the short-screen `2 ms` candidate to `5 ms`;
- sparse/reactive observation can cut full-screen observation substantially while improving success in the development screen.

Primary artifacts:

- [`results/REPORT.md`](research/real_apps_v1/results/REPORT.md)
- [`results/real_app_summary.csv`](research/real_apps_v1/results/real_app_summary.csv)
- [`real_app_suite_v1.py`](research/real_apps_v1/real_app_suite_v1.py)

### Real Apps v2 — semantic method lifetime vs route lifetime

Path: [`research/real_apps_v2/`](research/real_apps_v2/)

Question: when an optimized route fails, should the semantic method be discarded too?

Result: not by default. Across three fresh Inkscape replicates (72 episodes total), keeping the semantic method while suspending/reheating only the route preserved 72/72 success while reducing method redefinition churn, planner-byte proxy, and visual observation.

Primary artifacts:

- [`REAL_APP_SELF_COMPILE_V2_REPORT.md`](research/real_apps_v2/REAL_APP_SELF_COMPILE_V2_REPORT.md)
- [`route_suspend_summary.csv`](research/real_apps_v2/route_suspend_summary.csv)

### Real Apps v3 — Guarded Hierarchical Deoptimization

Path: [`research/real_apps_v3/`](research/real_apps_v3/)

Question: if a fast route has observable dependencies, can we avoid predictable failures before executing the route?

Result: yes, in the tested X11 cases.

- XTerm focus guard: 72/72 success; failed routes eliminated; p99 reduced by about 77.5%.
- Chromium geometry guard: 72/72 success; failed routes eliminated; p99 reduced by about 75.4%.
- Chromium binding replacement + geometry drift: semantic method remained valid while binding was repaired and route deoptimized independently.

Primary artifacts:

- [`GUARDED_HIERARCHICAL_DEOPT_REPORT.md`](research/real_apps_v3/GUARDED_HIERARCHICAL_DEOPT_REPORT.md)
- [`GHD_ALGORITHM_SPEC.md`](research/real_apps_v3/GHD_ALGORITHM_SPEC.md)
- [`guarded_hidden_summary.csv`](research/real_apps_v3/guarded_hidden_summary.csv)
- [`complete_hidden_summary.csv`](research/real_apps_v3/complete_hidden_summary.csv)

## Observation Gating — A1 scoped result

Path: [`research/observation_gating/`](research/observation_gating/)

On 2026-09-13 JST, frozen A1 revision 3 completed two fresh replicates, 24 paired
episodes/app across XTerm, a Chromium-family browser (Chrome for Testing), Calc
and Inkscape under Ubuntu/WSL2/Xvfb. O0 and O1 each achieved **96/96 success**.
All **1,446 sampled frames** reconstructed exactly, with zero false suppressions
or missed sampled changes.

- Exact same-trace image reduction: **17.15%**, 95% pair-bootstrap interval
  **13.86–20.65%**.
- Live intended-model-boundary images: **722 → 604**, **16.34%** reduction
  (12.14–20.64% interval). The receiver is a local reconstructing sink; no LLM
  was invoked.
- Median paired local task-wall delta (O1 minus O0): **+0.59 ms**, interval
  **-2.36 to +4.73 ms**. A speedup was not established.
- O1 exact compare cost: p50/p95/p99 **0.025/0.337/0.729 ms** per sample.

Decision: **PASS as a scoped O1 research baseline**, enabling the next O2
experiment. This is not a user-runtime promotion or evidence of token savings.
Captures still happen, and benefits differ strongly by application.

The result retains a rejected Calc startup-grey screen and two earlier frozen
Inkscape baseline failures. A visible selection barrier alone did not repair the
drag failure. The final local policy uses a conservative 30 ms press dwell,
validated with both pair orders; it is not a universal input specification.

Primary artifacts:

- [`REPORT.md`](research/observation_gating/REPORT.md)
- [`PROTOCOL.md`](research/observation_gating/PROTOCOL.md)
- [`DEVELOPMENT.md`](research/observation_gating/DEVELOPMENT.md)
- [`summary.csv`](research/observation_gating/results/a1r3-summary/summary.csv)
- [`frozen source and environment`](research/observation_gating/results/frozen-a1r3/)

## Observation tiles — A2 scoped result and actual assistant use

Path: [`research/observation_tiles/`](research/observation_tiles/).

On 2026-09-13 JST, frozen A2 revision 2 completed **64/64 fresh episodes**, eight
O1/O2 pairs/app across the same four real apps. All **553 sampled frames** passed
independent archived-wire/raw-PNG reconstruction and saved-output checks.

- Same-trace serialized-byte reduction: **70.73%**, 95% pair-bootstrap interval
  **64.72–75.19%**. Both representations use identical zlib level 1 and metadata.
- Live bytes: **13,562,871 → 3,853,968**, **71.58%** reduction.
- Paired task-wall delta (O2 minus O1): median **+2.00 ms**, interval
  **−4.00 to +12.27 ms**. A local speedup is not established.
- Full images are reconstructed before controller/model viewing. This does not
  establish image-token savings, and captures still occur in full.

Revision 1 stopped at a baseline Inkscape drag failure after 31 attempts; its
entire fresh efficacy comparison is retained as rejected. Revision 2 adds a
shared segmented gesture with observations while the button is held. This does
not isolate motor reliability from pacing and is not adaptive path correction.

The parent assistant also directly used the new stdin research interface to
operate Calc, Inkscape and XTerm through reconstructed screenshots. These three
exploratory sessions led to bounded change waits, unchanged PNG reuse, explicit
image/context timestamps, command logs and atomic unsupported-text rejection.
All three outputs and 18 observations were re-verified. This is actual use, but
not a controlled model latency/token comparison or a universal runtime.

Decision: **PASS for exact transport research; HOLD for a speed/token/runtime
claim**. A bounded Luna sourcing/review pilot was useful but needed fresh-source
verification after stale findings; no controlled model ranking was obtained.

Primary artifacts: [report](research/observation_tiles/REPORT.md),
[protocol](research/observation_tiles/PROTOCOL.md),
[failures and actual use](research/observation_tiles/DEVELOPMENT.md),
[primary-source research](research/observation_tiles/RELATED_WORK.md), and
[fresh summary](research/observation_tiles/results/a2r2-summary/summary.json).

### Continuing hypothesis

Image preparation was subsequently isolated in an [offline replay study](research/observation_tiles/IMAGE_ARTIFACT.md).
On the two archived A2 replicates, exact PNG reuse reduced local preparation
time by 10.81% / 16.59%; PNG level 1 instead of level 6 reduced reuse-path time
by a further 15.89% / 16.03%, with larger PNG files. All 1,659 validation outputs
decoded exactly. This is not new live-task, model-token or end-to-end evidence.
The shared sink is integrated into dogfooding with an explicit compression option;
the default remains 6. Actual assistant use at level 1 completed XTerm correctly,
but revealed a roughly 10.22-second inter-command interval despite local images
being ready in 41–56 ms after action issue. The next priority is the real
agent/tool interaction boundary, not further isolated image micro-optimization.

The next major question is whether image feedback can be treated as a local state-change signal rather than automatically forwarding every screenshot to a model.

Candidate ladder:

```text
O0 full screenshot after each step
O1 exact/fast unchanged-frame suppression
O2 + spatial change vector / changed-tile mask
O3 + relevant-region gating
O4 + local VERIFY
O5 + persistent visual state + ROI delta
O6 + GHD deterministic-route observation skip
```

The primary metric should be:

> percentage of model-visible image observations eliminated while preserving the same task correctness.

Secondary metrics: observed pixels, false update detection, missed update, local compute time, tail latency, and escalation rate.

## Promotion policy

A candidate is promoted only when:

1. correctness is not worse under the defined hard gate;
2. parameters are frozen before hidden/fresh evaluation;
3. baseline and candidate see the same task/environment schedule;
4. result survives at least one fresh replicate or explicitly remains `HOLD`;
5. claims are scoped to the actual environment measured.

## Claims taxonomy

| Term | Meaning in this repository |
|---|---|
| `planner bytes` | serialization byte proxy, **not tokens** |
| `observed pixels` | pixels captured/processed by the harness, **not image tokens** |
| `wall time` | local harness timing, **not model-in-loop latency** |
| `hidden/fresh` | task/seed not used to tune the candidate; not a security claim |
| `real app` | actual desktop application under X11/Xvfb, not a synthetic widget model |

## Rejected or held ideas

Negative results are retained because they constrain the design space.

- fixed sleeps as a correctness mechanism — rejected;
- method-wide invalidation for every route failure — rejected as default;
- blind re-anchor-and-continue — unstable in fresh runs;
- aggressive predicted ROI without clipped-observation rejection — caused centroid bias/failures;
- event filtering across a high-frequency Python/stdio boundary — observer overhead erased gains;
- replacing all observation with a single global perceptual hash — insufficient for local motion/change.

## Next experiments

1. Paired agent-in-the-loop adapter measurement: PNG/reference reuse, real image tokens and resume latency.
2. Isolate adaptive motor feedback from additional pacing/observation cost; retain the failed drag regression.
3. Longer mixed-app sessions with app restarts, focus drift, geometry drift, and modal transitions.
4. ROI/visual-state experiments with full-base recovery, plus guard placement cost vs expected failure cost.
5. Only after algorithmic semantics stabilize: production-oriented implementation work.
