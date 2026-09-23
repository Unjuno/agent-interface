# A1: exact unchanged-frame suppression

Status: frozen A1 protocol, 2026-09-13 JST. Source and parameters are snapshotted
in `results/frozen-a1/freeze.json` before either fresh replicate.

## H — Hypothesis

In the defined four-application X11 workload, suppressing an image only when its
dimensions, mode and pixel bytes exactly match the receiver's retained image
preserves every sampled visual state and task correctness, and removes at least
10% of images in the pooled suite. A per-app benefit is not assumed.

The work removed is forwarding a duplicate image across the intended model
boundary. Capturing and serializing candidate frames still happen. Every sample
still carries its timestamp, action ID, sequence, image-base reference, window
titles and active-window ID. No perceptual hash or similarity threshold is used.

## T — Minimum test

- Real applications: XTerm, a headful Chromium-family browser, LibreOffice Calc,
  and Inkscape. The locally available browser is **Google Chrome for Testing
  145.0.7632.6**, a Chromium distribution; do not report this as a different
  distro's `chromium` package. Exact versions are saved by the harness.
- Environment: Ubuntu 24.04 under WSL2, Xvfb 1280 x 800 x 24, Openbox,
  Python-Xlib/XTEST. This is real GUI execution on a virtual X display.
- Reset: new worker process, X server, WM, app process, app profile, HOME and XDG
  directories per episode. OS filesystem/font caches are not flushed.
- Development: baseline smoke, then four paired seeds 1201–1204 per app. Preserve
  and diagnose every failure; repair the baseline before interpreting candidates.
- Reject the original development screen's Calc startup confound. The accepted
  development set is `development-painted-02`: Calc must visibly paint its
  worksheet before task timing (more than 20% near-white pixels and more than
  128 colors). This is a setup-only readiness heuristic, common to O0/O1, not
  an image-suppression threshold. Setup captures are counted separately.
- Freeze all controller/gate parameters and source hashes after development.
- Fresh evaluation: two independently launched replicates, 12 pairs/app each,
  seeds 91021–91032 and 182701–182712, **24 pairs/app, 96 pairs total**. These seeds
  are not used for tuning. They are fresh task parameters, not concealed security
  secrets. The same distribution of tasks is used in development and evaluation.
- Shuffle app/seed pairs deterministically. Alternate O0/O1 and O1/O0 order by
  seed within each fresh replicate. GUI runs are sequential, never concurrent.
- Same logical action script, goal, input-delivery policy, public condition,
  timeout, polling cadence, process reset and scoring oracle for both strategies.
  Physical event/capture times can differ; retain timestamps and also report
  counterfactual O0/O1 counts on each exact same captured trace.
- O0 sends a full image after each logical input and on each explicit wait/update
  sample. O1 visits those same observation sites and suppresses exact repeats.
  There are no inserted duplicate frames or extra idle phases to increase savings.
- Local input parameters inherited from prior development evidence: 2 ms between
  text characters, 5 ms press-to-motion dwell, 4 ms between drag motion steps.
  They are backend policy, not universal completion guarantees.
- Public effect wait: at most 4 s, sample immediately, then 16 ms cadence.
  Sampling sleep is never treated as evidence of success.
- Final file/HTTP oracle: at most 3 s **after the controller has returned**.
  The controller is not passed the output path and cannot use oracle results to
  choose or retry an input. Worker outer deadline is 90 s.
- Stop on the first task or reconstruction failure, retaining the failed run.
  A baseline failure invalidates candidate comparison until diagnosed. A fresh
  failure may not be tuned away and merged into the same frozen evaluation.

### Tasks and scoring

| App | Input through GUI | Public feedback during control | Post-controller oracle |
|---|---|---|---|
| XTerm | Type a seeded token and press Enter | Terminal title acknowledges receipt | Output text exactly equals token |
| Chromium family | Navigate via omnibox to a local form, type token, submit | Page titles indicate form readiness and receipt | Local HTTP POST body exactly equals expected field/token |
| Calc | Enter two seeded numbers in A1/A2, save XLSX, confirm format | Format dialog appears/disappears | Independently load saved workbook; exact A1/A2 values |
| Inkscape | Acquire visible red rectangle, select, drag right, save SVG | Rectangle visibly moves right | One rectangle moved right; y, width, height preserved |

The browser form and terminal reader are transparent workload fixtures, not
simulated GUI backends. There is no injected network delay. App-specific file
readers are scoring instruments, not the control route. The Inkscape contract is
direction and geometry preservation, **not exact motor gain**. Red segmentation
is common controller target acquisition; it does not decide whether an image is
suppressed. This is a scripted controller with a reconstructing image sink;
there is no model in the loop.

## D — Decision

**FAIL** if any candidate success falls below its paired baseline, any changed
frame is suppressed, any receiver frame differs from the captured frame, any
image reference is invalid, or source/parameter freeze is violated.

**INVALID / repair baseline first** if a baseline task fails, a pair is missing,
or the suite stops before completing its planned sample.

**PASS (scoped experiment only)** if both frozen replicates finish with all
paired tasks correct, false suppressions/missed changes/reconstruction errors
are zero, and pooled same-trace image reduction is at least 10% with a 95%
episode-pair bootstrap interval strictly above zero. Report actual live stream
counts and per-app results alongside the same-trace estimate.

**HOLD** otherwise. A PASS supports retaining the O1 research baseline and permits
O2 research; it does not automatically promote a user-facing runtime, establish
universal safety, or prove model latency/token savings.

## Measurements

Record per sample: capture time, RGB serialization time, public-context time,
exact compare time, gate/receiver time, candidate and forwarded counts, suppressed
count, captured pixels and model-visible pixels. Hashing is not used by the gate;
archive SHA-256 and PNG compression happen after task timing.

Record each action's issue, XSync input acknowledgment, first fresh observation
receipt, and public-effect-known timestamps separately. Fresh observation receipt
can be an unchanged-image reference; it **does not imply app consumption or task
completion**. Report the first changed visual/context feedback as a separate
metric and leave it missing when no such change was seen. Report final oracle
time separately from the controller's public observations. Some logical actions
do not have a separately known semantic-completion timestamp.

Report p50/p95/p99 using linear sample quantiles, include failures in counts, and
do not selectively discard slow successful episodes. Resample whole app/seed
pairs for confidence intervals, not correlated frames. Include both live runs
within a resampled pair for same-trace image estimates. Use a fixed bootstrap
seed of 65537 and 10,000 resamples.

## C — Competing explanations

- Duplicate opportunities depend on app redraws, cursor blink and poll cadence.
- Screenshots and the Python/public-context work can slow the GUI and change the
  next observation. Live counts and exact same-trace counts answer different
  questions; neither is an LLM counterfactual.
- App startup/readiness, process ordering, WSL scheduling and warm OS caches can
  affect latency and apparent savings despite fresh app profiles.
- A correct scripted task and identical images do not establish identical LLM
  behavior. Byte/pixel reductions are not token measurements.
- The workload has a local form and simple documents; it is not representative of
  arbitrary applications, remote latency, long tasks or transient unseen events.

## U — Uncertainty and limits

Twenty-four fresh pairs per app are insufficient to establish rare-failure rates
or stable p99 estimates. Exact equality preserves **sampled image pixels**, not
events between captures, a hardware cursor omitted by ImageGrab, or nonvisual
state outside the declared context. A receiver retaining a correct image base
and ordered reliable transport is an explicit assumption. Tests cover gaps,
reordering and reconnect by requiring resynchronization; transport implementation
is future work. No neural model, token meter, remote transport or model latency
is part of this experiment.
