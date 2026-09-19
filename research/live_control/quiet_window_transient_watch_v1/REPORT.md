# Quiet motor windows: transient-event blind spot and an independent ROI watcher

**Decision: SCOPED_WATCH_CANDIDATE. Reject extending endpoint-only quiet sensing to tasks requiring transient stop-event detection.** This is a synthetic task with live X11 input and rendered pixel acquisition, not a Doom, planner, or production-runtime result.

Task: `QUIET-WINDOW-TRANSIENT-WATCH-20260916-001`, Issue #174; discovery coordination #105.
Publication BASE: `7f42fd577dff98d6a27a8eceb79d86bee0358bf9`.
Runtime BASE: `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`.
Only new research files are added. Existing runtime, scorer, fixtures and historical allocations are unchanged.

## Question and scope

Previous retained quiet-hold evidence improved post-release observation timing by removing capture/artifact work from a short held-input interval. It explicitly did not qualify tasks requiring intermediate feedback. Separately, #105 already has caller integration, live X11 two-dispatch and real MAP01 freshness transfer. Repeating those would not test this remaining limit.

The new question is narrower: can a stop cue appear and disappear during a quiet window, leaving a fresh final observation with no evidence of the event? Does one independent, bounded, declared-region pixel watcher prevent continued held input, without cancelling for the same change outside that region?

The stop-cue semantics, location, colour and threshold are fixture-declared. This is not automatic target grounding or a general threat detector. Both conditions keep the same InputOwner, lease, action and final observation schedule. Only the watcher and its cancellation path are enabled in the candidate.

## Frozen experiment and environment

Before measured cases, Issue #174 comment `5684887873` recorded source/preregistration hashes, schedule and gates. Exactly 48 first measured cases completed: 12 matched quiet/watched pairs for target cues, then 12 pairs for nuisance changes. Arm order alternates Q/W and W/Q; onset offsets 100, 160, 220 and 280 ms repeat three times per category. No measured case was repeated, replaced or appended after outcomes.

| Condition | Value |
|---|---|
| CPU | AMD EPYC 9V74 80-Core Processor, affinity 0..4, shared host |
| CPU frequency | Not pinned; not recorded as a fixed operating frequency |
| Software | CPython 3.13.5, Linux 6.18.44, Tk 8.6, python-xlib 0.33 |
| Display and input | Private Xvfb 640x400x24; actual XTEST Right KeyPress/KeyRelease |
| Runtime | Unchanged InputOwner v10, Git blob `341b3c01649943ddaad5f28431a792c4889cc36e` |
| Authority | 600 ms from Lease construction, independently enforced by InputOwner |
| Cue | Nominal 80 ms red interval, scheduled relative to app-observed first KeyPress |
| Watcher | Separate thread/X connection; 32x32 XGetImage ROI at (48,48), 10 ms nominal period |
| Predicate | At least 512 of 1024 pixels match the declared BGR red triplet; depth24/32-bpp layout checked |
| Final observation | Deadline plus 60 ms, including early-cancel cases |
| Allocation | Serial fresh application process per case; 48 measured cases; four excluded construction cases |
| Model/game calls | Zero / zero |

The watcher acquires the small ROI directly. It does not capture the whole screen and crop afterward. Raw bytes/timestamps are buffered in memory and persisted outside the input-owner thread. Upon a matching image, it latches the detection and sets cancellation on the existing Lease. It never extends authority or restarts input after the cue disappears. The owner deadline remains a fallback.

The controller does not consume fixture event logs to select cancellation. Those logs are read after owner closure, for independent app-side evaluation. Both arms receive the same post-deadline observation, so this block does not benchmark earliest fresh-frame return.

## First measured results

| Metric | Endpoint-only quiet | Quiet motor plus independent watch |
|---|---:|---:|
| Target cue detected and latched | 0/12 | 12/12 |
| Target cue to app KeyRelease, median | 409.626 ms | 10.956 ms |
| Target cue to app KeyRelease, observed range | 319.512-499.804 ms | 9.574-11.602 ms |
| Nuisance false cancellation | 0/12 | 0/12 |
| Verified empty physical input, both categories | 24/24 | 24/24 |
| Final monitored ROI equal to initial clear ROI | 24/24 | 24/24 |

The median **within-pair** target release-latency reduction is **398.951 ms**, range **308.180-489.501 ms**. This is computed per matched pair before taking the median, not by subtracting the two arm medians. All 12 watched target releases are within the predeclared 50 ms gate. The median paired reduction exceeds the predeclared 100 ms gate.

The watched target detection delay is 9.298 ms median. Cancellation-set to owner-verified-empty is 1.674 ms median, range 0.486-2.418 ms. These are distinct from the app-observed release endpoint.

All 48 final monitored-region images have the same digest as their initial clear image. Therefore a fresh final ROI sample alone cannot distinguish these transient target-cue histories from a no-cue history. This claim is only about the monitored region: the entire screen need not be identical because the moving object can end at a different position. The candidate's latched record remains present after the visible cue clears.

## Cost and adverse observations

In the 12 watched nuisance cases, the whole 600 ms window remains active and the watcher acquires 60 samples per case. The cumulative acquisition-call wall time is **7.213 ms median**, range **5.484-12.050 ms**, per case. This excludes predicate processing, threading and other controller work: it is **not** whole-monitor CPU consumption or end-to-end task latency.

The nuisance app-observed hold duration is 599.963 ms median without watching and 599.880 ms with watching. This small difference is not claimed as a speedup. The maximum nuisance deadline-to-verified-empty delay is 2.390 ms with watching versus 0.935 ms without; monitoring is not free of scheduler effects. In target cases, early cancellation is intentional and negative deadline-relative timestamps must not be mislabelled as negative latency.

A total of 972 intermediate watcher samples are retained, plus both endpoint samples for all cases.

## Timing interpretation and units

The primary cue reference is the fixture's Tk draw-completion timestamp after `update_idletasks`, not a physical monitor scanout or photon timestamp. App KeyRelease is separately logged by the fixture; InputOwner also records its own independent release verification. These endpoints are not interchangeable.

The environment records `clock_gettime(CLOCK_MONOTONIC)`, non-adjustable, with reported resolution 1 ns. All process timestamps use the same local monotonic clock domain. Integer nanosecond timestamp differences are converted to milliseconds by dividing by 1,000,000; dimensions remain elapsed time. Clock resolution is not a bound on scheduling, drawing, input delivery or measurement error. Python's documented clock semantics are at https://docs.python.org/3.13/library/time.html.

## Failures and audit

Construction failure 1 was missing Xauthority configuration, before any input. Construction failure 2 was the preinstalled python-xlib 0.15 returning an incompatible image-payload type, also before input. The old sources and failure records are retained. Installing retained python-xlib 0.33 and using a private local display resolved setup; four construction cases then passed and were excluded. No GUI policy was tuned on measured outcomes.

An independent-code, offline audit recomputes the outcomes from raw app events, verifies all 48 schedule identities and original raw-file hashes, checks the frozen source hashes, decompresses and rehashes every referenced ROI payload, re-evaluates the predicate, and reconciles medians and paired medians with the result JSON. It returns `PASS_RAW_AUDIT`.

Five post-measurement audit corruption controls are rejected: unverified release, missing app release, missing pixels, stale final capture and duplicate KeyPress. These are audit tests, not additional live samples or preregistered efficacy outcomes. This is not an independent human/agent review.

## H / T / D / C / U

**H:** Endpoint-only sensing misses a transient declared stop cue; independent bounded sensing and a latched event can cancel current input through existing authority controls.

**T:** Frozen 48-case live-X11 comparison with matched target and nuisance conditions; no new model/game call; first outcomes retained. Offline audit and five negative audit controls follow the measured block.

**D:** All frozen gates pass. Retain the independent scoped watcher as a mechanism candidate. Reject a blanket inference that making the motor path quiet permits stopping all environment monitoring. No production/runtime promotion or general task-performance claim follows.

**C:** The detector could be too fixture-specific; known exact colours and ROI make this easier than arbitrary GUI warnings. Shorter events, ROI movement, rendering changes, scheduler stalls or a hung X server can defeat polling. A shared server hang could affect both watcher and owner; separate connections do not prove fault isolation. No new authority is granted by the detected event.

**U:** Twelve paired positive examples and twelve paired negative examples, one host, blocked category order, unpinned frequency, nominal timer periods and app draw-completion timing limit transfer. No numeric combined uncertainty or coverage factor is invented: scheduling and presentation uncertainty were not calibrated. Observed ranges are not confidence intervals or hard real-time bounds.

**Next single question:** Keep this watcher and its 10 ms period fixed; in a newly frozen allocation, shorten the cue and vary its onset phase to identify the missed-event boundary. Do not retune the detector or declare a universal 10 ms reaction guarantee.

## Complete retention and reconstruction

The six binary `.xz.partNN` files are two lossless JSON archives, not partial placeholders. `manifest.json` records every chunk's byte count, SHA-256 and Git blob identity, and both complete archive digests. `sources.json.xz` contains the exact executable study sources, frozen preregistration and construction failures. `evidence.json.xz` contains all 48 original raw records, every distinct compressed ROI payload, environment, results and audit. Duplicate pixel content is deduplicated by digest; no sampled observation is omitted.

From this directory, using Python's standard library:

```sh
python reconstruct.py /tmp/quiet-watch-retained
python /tmp/quiet-watch-retained/study/audit.py /tmp/quiet-watch-retained/measured-01 /tmp/quiet-watch-retained/study
```

Reconstruction refuses an existing output directory and verifies both archive hashes, all part hashes/Git blob identities, original raw-file SHA-256s and frozen source hashes. Neither command launches GUI input or a new benchmark. A new experiment requires a new identity and output directory; do not rerun this consumed measured allocation as though it were its first outcome.

Frozen `fixture.py`: `83fa1e6d30fc2fddfebf40bccc15317b55817d0df59069eef8eac254cd4d25cf`.
Frozen `run.py`: `d3f2260ddbe6a5bbf2d5313ebe8c8b4d39d0a3bfacfdad0ab09a604b79dcaa8c`.
Frozen `prereg.json`: `b57600973164b32c5b7fe13047458e6237d54bbd43bb19585b89d5fbb322bbae`.

The old runtime source comes from the separately retained bundle with SHA-256 `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`. An offline audit does not require that runtime or X11 dependencies.
