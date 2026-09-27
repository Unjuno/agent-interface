# A1 — Exact unchanged-frame suppression on four real applications

Date: 2026-09-13 JST. Decision: **PASS as a scoped research baseline** for frozen
revision 3. O0 and O1 each completed **96/96 tasks**; all **1,446 sampled frames**
passed independent archive reconstruction. False suppression, missed sampled
changes and reconstruction errors were all **zero**.

O1 eliminated **17.15%** of images on the exact same recorded frame sequences
(95% pair-bootstrap interval **13.86–20.65%**). The separately executed live
streams sent **722 images with O0 versus 604 with O1**, a **16.34%** reduction
(12.14–20.64%). **A local latency improvement was not established.**

These are real GUI executions with a scripted controller and a local image
receiver. There were **zero model calls**. This result does not measure actual
model tokens, API costs, model accuracy or end-to-end agent latency.

## H — Hypothesis and the work removed

The [frozen protocol](results/frozen-a1r3/source/PROTOCOL.md) predicts that exact
image equality can remove at least 10% of images across the defined suite while
preserving task correctness and every sampled visual state. A benefit in every
individual app is not assumed.

O1 compares dimensions, image mode and immutable pixel bytes against the retained
image. It omits only the duplicate image body. Each observation still carries a
sequence number, base-image reference, action ID, capture timestamp, window titles
and active-window ID. A fresh stream always sends a full image; missing or stale
image references are errors requiring resynchronization.

Capture and RGB serialization still occur. The eliminated work is forwarding
duplicate images at the intended model boundary. Gate equality uses **no hash and
no perceptual threshold**. SHA-256 and PNG encoding are used after timing for
evidence storage and verification.

## T — Environment and test

| Component | Measured version |
|---|---|
| OS | Ubuntu 24.04.4 LTS, WSL2 Linux 6.6.87.2, x86-64 |
| Display | Xvfb 21.1.12, 1280 x 800 x 24; Openbox 3.6.1 |
| Python | 3.12.3 |
| Input | Python-Xlib 0.33, XTEST |
| Images / array audit | Pillow 10.2.0, NumPy 1.26.4 |
| Workbook oracle | openpyxl 3.1.2 |
| XTerm | 390 |
| Chromium-family browser | **Google Chrome for Testing 145.0.7632.6** |
| Calc | LibreOffice 24.2.7.2 |
| Inkscape | 1.2.2 |

The browser is the locally available Chromium distribution, not the Ubuntu
`chromium` snap. Exact package strings, source hashes and diagnostics are retained
in [the freeze manifest](results/frozen-a1r3/freeze.json).

There are two fresh replicates, each with 12 paired seeds/app: 490101–490112 and
590101–590112. That is **24 pairs/app, 96 pairs, 192 live episodes**. Each replicate
randomizes app/seed pair order, and each app alternates O0/O1 and O1/O0 order.
Both replicates completed 96/96 episodes. Runs are sequential, with a new Python
worker, X server, WM, application process, application HOME/XDG directories and
profile for every episode. OS caches are not flushed.

Both strategies use the same logical inputs, goals, input policy, public
conditions, sampling cadence, deadlines and final oracle. The archive analyzer
verified matching action IDs/order, logical-operation counts and input-event
counts for every pair. Timing and number of wait samples can vary; the exact
same-trace estimate removes this source of image-count ambiguity.

| App | GUI task | Final oracle, after control returns |
|---|---|---|
| XTerm | Type a seeded token, press Enter | Exact terminal-reader output text |
| Chromium family | Navigate through omnibox, fill and submit a local HTML form | Exact HTTP POST field/token |
| Calc | Enter seeded numbers in A1/A2, save XLSX, confirm format | Independently load the saved workbook and compare both cells |
| Inkscape | Visually acquire a red rectangle, select, drag right, save SVG | One rectangle moved right; y, width and height preserved |

The controller is not passed the output path and cannot use file/HTTP oracle
results to choose or retry input. The form has no injected network delay. Target
acquisition and selection guards use public images, not fixed application
coordinates. The Inkscape contract is movement direction and geometry preservation,
not exact motor gain.

The frozen local input policy uses 2 ms between text characters, **30 ms between
button press and motion**, and 4 ms between drag motion steps. A visible selection
barrier precedes the drag. Calc's worksheet and Inkscape's target must be painted
before task timing; setup captures are counted separately. Public effect waits
sample immediately and then use a 16 ms cadence, with a 4 s deadline. The separate
final oracle has a 3 s deadline. Elapsed time never declares success.

## Results: correctness, images and pixels

| App | O0 success | O1 success | O0 images | O1 candidates | O1 images | O1 suppressed |
|---|---:|---:|---:|---:|---:|---:|
| XTerm | 24/24 | 24/24 | 72 | 72 | 71 | 1 |
| Chromium family | 24/24 | 24/24 | 294 | 289 | 280 | 9 |
| Calc | 24/24 | 24/24 | 174 | 174 | 99 | 75 |
| Inkscape | 24/24 | 24/24 | 182 | 189 | 154 | 35 |
| **Total** | **96/96** | **96/96** | **722** | **724** | **604** | **120** |

O1 suppressed 120 of its own 724 candidate images (16.57%). It generated two more
candidate samples than the separate O0 runs, so its live total is 118 images
lower. This is why live reduction and within-stream suppression are different
numbers.

| App | Live image reduction, 95% CI | Exact same-trace reduction, 95% CI |
|---|---:|---:|
| XTerm | 1.39% [0.00, 4.17] | 0.69% [0.00, 2.08] |
| Chromium family | 4.76% [-1.41, 10.30] | 4.46% [3.32, 5.56] |
| Calc | 43.10% [39.31, 46.37] | 43.10% [41.23, 44.76] |
| Inkscape | 15.38% [10.06, 20.77] | 19.14% [16.80, 21.58] |
| **Pooled** | **16.34% [12.14, 20.64]** | **17.15% [13.86, 20.65]** |

The same-trace column uses both live trajectories within each pair, counting all
their exact repeat opportunities: **248 repeats / 1,446 captured samples**. The
bootstrap resamples whole app/seed pairs, retaining the two trajectories together,
with 10,000 resamples and fixed seed 65537. Frames are not treated as independent
experimental units. XTerm's small result is consistent with no benefit in this
short task; Chromium's live interval also includes zero. The dominant benefit is
in Calc and Inkscape.

O0 captured and forwarded **739.328 million pixels**. O1 captured **741.376 million
pixels** and forwarded **618.496 million pixels**. These are full-frame pixel
counts, **not image tokens**; capture work was not reduced by the gate.

In O1, **111 of the 120 suppressions occurred immediately after a logical action**;
only nine occurred during public-effect waits. No initial image was suppressed.
The measured benefit is therefore not produced mainly by repeatedly sampling a
long idle wait. No duplicate frames or idle phases were inserted for the metric.

## Results: latency and local cost

Each cell below is **p50 / p95 / p99 in milliseconds**. Task wall time includes
the final output check and excludes launch/readiness and evidence archiving.

| App | O0 task wall | O1 task wall | O0 action-to-first-fresh-feedback | O1 action-to-first-fresh-feedback |
|---|---:|---:|---:|---:|
| XTerm | 51.90 / 57.93 / 60.02 | 52.35 / 57.94 / 62.27 | 18.18 / 28.38 / 30.06 | 18.77 / 30.35 / 31.09 |
| Chromium family | 347.05 / 384.82 / 419.03 | 342.33 / 364.97 / 390.50 | 18.52 / 74.84 / 76.08 | 17.96 / 77.07 / 80.72 |
| Calc | 112.70 / 142.02 / 145.87 | 115.68 / 143.90 / 150.18 | 13.24 / 18.54 / 19.97 | 13.10 / 18.01 / 19.80 |
| Inkscape | 276.78 / 305.12 / 309.41 | 284.91 / 322.90 / 339.17 | 14.88 / 84.92 / 91.02 | 13.66 / 81.15 / 86.00 |
| Pooled | 190.26 / 366.88 / 387.57 | 198.75 / 350.08 / 367.70 | 15.12 / 74.68 / 85.24 | 15.12 / 76.24 / 82.49 |

The median **paired** task-wall difference, O1 minus O0, is **+0.59 ms**, with 95%
interval **-2.36 to +4.73 ms**. The experiment establishes neither a local speedup
nor a local latency equivalence margin. Per-app paired intervals all include
zero. Tail values are descriptive sample quantiles, not evidence of stable p99
performance from 24 episodes per strategy/app.

First fresh feedback means that the local receiver has either a new image or a
timestamped exact-image reference plus public state. It does **not** prove app
consumption or semantic completion. Input acknowledgment, public-condition-known
time, and final oracle time are saved separately. Some logical actions do not
have a separately known semantic completion time.

The separate first **changed** visual/context feedback metric is:

| Strategy | Actions with observed change | p50 / p95 / p99 ms | Actions with no observed change |
|---|---:|---:|---:|
| O0 | 317/408 | 16.06 / 75.39 / 85.86 | 91 |
| O1 | 318/408 | 15.33 / 77.78 / 82.64 | 90 |

Unobserved change times remain null; they are not counted as zero latency. These
timestamps measure local feedback availability. The harness has no asynchronous
model adapter and does not measure when a real agent resumes thinking.

| O1 local component | p50 / p95 / p99 ms per sample |
|---|---:|
| Exact comparison | **0.025 / 0.337 / 0.729** |
| Screen capture | 4.528 / 8.233 / 10.467 |
| RGB serialization | 1.244 / 3.230 / 4.108 |
| Public X11 context collection | 4.677 / 8.161 / 14.720 |

Hash cost in the gate is zero because the gate does not hash. Public context is
collected after the image capture; this is not an atomic snapshot of all OS state.
Full gate, receiver, launch, public-condition and oracle timing summaries are in
the machine-readable [summary](results/a1r3-summary/summary.json).

## D — Decision and verification

**PASS, scoped to the revision 3 protocol.** Both planned fresh replicates
completed; correctness is equal; all exact-reconstruction checks pass; pooled
same-trace reduction exceeds 10% and its interval excludes zero. Retain O1 as the
research baseline for the next observation experiment. This is not a promotion
of the whole control harness into `runtime/`.

Verification completed:

- Reloaded every archived PNG, checked its byte hash/geometry, recomputed exact
  equality independently with NumPy, and validated image-reference continuity.
- Checked every scheduled pair, action order, logical operation and input-event
  count. There were no missing or duplicate planned runs.
- Independently reopened and rescored all **192 saved task outputs** after the
  benchmark; all passed. [Verification record](results/a1r3-summary/verification.json).
- Verified all six frozen source/protocol hashes remained unchanged through the
  evaluation; both replicates used matching app/dependency versions.
- Synthetic gate tests cover single-byte changes at all positions in a small
  image, shape/mode changes, malformed storage and stale/missing/reordered bases.
  They are separate from the real-GUI evidence.

## C — Rejected explanations and retained failures

This result was **not** obtained by accepting the first successful development
screen. [The development ledger](DEVELOPMENT.md) records the entire repair history:

1. An initial Xvfb startup check failed under WSLg because the pathname socket was
   absent while an abstract socket was usable. Readiness now uses an X11 handshake.
2. A 32/32 successful screen was excluded after visual inspection showed Calc's
   unpainted grey client contributing apparent redundancy. Painted-document
   readiness is now a setup prerequisite.
3. Frozen revision 1 stopped at an Inkscape O0 drag failure (9 successes / 10
   attempts). Visible selection was not established before the dependent drag.
4. Frozen revision 2 also stopped at an Inkscape O0 drag failure (3 / 4 attempts),
   despite selection being visible. Selection verification alone was insufficient.
5. Revision 3 uses a conservative 30 ms local press dwell and introduces balanced
   pair order during development. It passed renewed development and both new
   fresh replicates. The 30 ms value is not claimed to be minimal or universal.

Old fresh failures are never pooled into revision 3's efficacy estimate. They
remain failures of their respective baselines, with the original manifests,
sources, action traces and images retained. Development success under a single
run order was insufficient to validate the earlier input policy.

Other competing explanations remain: redraw cadence and cursor blinking govern
duplicate opportunities; screenshots/public-context collection can affect GUI
scheduling; WSL host load and warm OS caches influence timing; simple fixtures
may overrepresent deterministic operations. Same-trace and live estimates address
different parts of these concerns. Neither is a model-in-the-loop counterfactual.

## U — Limits and next research boundary

Zero observed errors across 24 pairs/app does not establish a rare-failure bound
for arbitrary workloads. Exact comparison preserves sampled image bytes, not
events between captures, a hardware cursor absent from ImageGrab, or undeclared
nonvisual state. The ordered in-process receiver retaining its previous image
is an explicit assumption; a remote transport needs resynchronization semantics.

The two failed input revisions show why a microbenchmark's 100% result and a
previous environment's dwell value are not universal correctness guarantees.
Local latency, model-visible pixel counts and a scripted controller's success
must remain distinct from model tokens, real agent idle time and model accuracy.

O1 now satisfies the prerequisite for **A2: exact tile delta**. The next question
is how much changed-region forwarding can remove when a full frame usually
changes, especially in Chromium. A2 requires its own development/freeze/evaluation
and exact receiver reconstruction; no O2 runtime or O2 performance claim is part
of this A1 result.

## Primary artifacts

- [Protocol and frozen source](results/frozen-a1r3/)
- [Fresh replicate 1 raw runs](results/fresh-a1r3-r1/runs.jsonl)
- [Fresh replicate 2 raw runs](results/fresh-a1r3-r2/runs.jsonl)
- [Summary CSV](results/a1r3-summary/summary.csv) and [full JSON](results/a1r3-summary/summary.json)
- [Rejected/invalid development and fresh evidence](DEVELOPMENT.md)
- [Harness and reproduction instructions](README.md)
