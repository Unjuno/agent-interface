# Fixed 10 ms watcher: short-cue duration and onset boundary

**Decision: SAMPLING_LIMIT_OBSERVED. Reject a universal transient-event guarantee for the fixed 10 ms polling watcher.** This is a negative applicability result, not a new controller or a production promotion.

Task `QUIET-WATCH-SHORT-CUE-20260916-002`, Issue #186; predecessor #174 / PR #181. Publication BASE `1308b57d3209bc32b3bea5b84efb4911c915d8e9`; upstream evidence HEAD `c2888fb57c1f82ad4d843b1acfcdde3f35bcea8a`; runtime BASE `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`.

## What actually ran

120 first measured live-X11 cases, in one frozen randomized serial schedule. The 90 watched target cases cover nominal cue widths 2, 5, 8, 10, 15 and 20 ms, five onset offsets (200, 202, 204, 206, 208 ms after app KeyPress), and three repetitions per cell. Fifteen 20 ms quiet-target controls and fifteen 20 ms watched-nuisance controls are interleaved. Four setup cases use only the already tested 80 ms cue; they are excluded.

The fixture is byte-identical to the predecessor. Only its existing duration/offset arguments and the allocation schedule change. The 32x32 ROI, exact-colour predicate, 10 ms nominal watch loop, independent 600 ms InputOwner deadline, cancellation path and deadline-plus-60 ms final observation are unchanged. `provenance.json` retains the exact three-change case-function diff. No model, game, shared-runtime or workflow changes were made.

Pre-measurement Issue #186 comment `5685237136` froze the schedule and source hashes. Full preregistration SHA-256: `5742386f1c9c035a38ae28f517dd09a2d2679a5e6a8840ce3d7f24a766cc385f`. The explicit schedule uses `random.Random(18620260916).shuffle` once before measurement. No measured case was retried, replaced or added after outcomes.

## Environment

| Property | Recorded condition |
|---|---|
| Hardware | AMD EPYC 9V74 80-Core Processor; affinity 0..4; shared host |
| CPU clock | Not pinned; no fixed frequency claimed |
| Software | CPython 3.13.5, Linux 6.18.44, python-xlib 0.33 |
| Display / input | Private Xvfb 640x400x24; actual XTEST Right key input |
| Observation | Root XGetImage, 32x32 ROI at (48,48), checked depth24/32-bpp BGRX |
| Detector | At least 512/1024 pixels match declared BGR (50,50,220) |
| Authority | Unchanged InputOwner v10 and Lease; 600 ms fixed deadline |
| Concurrency / batch | One fresh app per case, cases serial; separate watcher and owner threads |
| Clock | Local CLOCK_MONOTONIC through perf_counter_ns; reported resolution 1 ns |
| Model / game calls | 0 / 0 |

The controller reads the fixture's event log only after owner closure. Event logs therefore do not provide a privileged signal for online cancellation. Separate X connections do not prove fault isolation from a shared X server hang.

## Detection boundary

All values below describe this allocation, not population detection probabilities.

| Nominal cue width | Actual draw-end duration median [range] | Detected | Missed |
|---:|---:|---:|---:|
| 2 ms | 1.925 [0.886, 1.987] ms | 3/15 | 12/15 |
| 5 ms | 4.941 [4.886, 5.022] ms | 6/15 | 9/15 |
| 8 ms | 7.939 [7.881, 8.553] ms | 12/15 | 3/15 |
| 10 ms | 9.934 [9.738, 11.063] ms | 15/15 | 0/15 |
| 15 ms | 14.935 [14.827, 15.009] ms | 15/15 | 0/15 |
| 20 ms | 19.968 [19.750, 20.064] ms | 15/15 | 0/15 |

The actual timer intervals differ from the requested durations. In particular, one nominal 2 ms cue measured 0.886 ms between draw-completion timestamps. Nominal widths are not silently substituted for measured intervals.

### Onset-offset matrix

Each cell is detections out of three first cases. Offsets are relative to app KeyPress, **not a verified phase lock to sampling**. Acquisition brackets and the measured distance from the preceding acquisition are retained separately.

| Width | 200 ms | 202 ms | 204 ms | 206 ms | 208 ms |
|---:|---:|---:|---:|---:|---:|
| 2 ms | 0/3 | 0/3 | 0/3 | 0/3 | 3/3 |
| 5 ms | 0/3 | 0/3 | 0/3 | 3/3 | 3/3 |
| 8 ms | 0/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| 10 ms | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| 15 ms | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| 20 ms | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |

## Why the misses matter

All **24/24 missed watched targets** have their entire app-draw bracket between the end of one ROI acquisition and the start of the next. None has a fully contained acquisition during the cue. Rechecking every retained pixel payload reproduces the original predicate. At the retained clock/fixture scope, these are missed sampling opportunities, not misclassification of an acquired red image.

For the 66 detected watched target cases, cue draw-completion to app KeyRelease is median **5.478 ms**, range **1.746-13.594 ms**. For the 24 missed cases it is median **397.394 ms**, range **392.542-399.601 ms**: the key remains held until the independent deadline fallback. The successful-subset latency is explicitly conditional on detection; it is not a full-workload response-time claim.

All **120/120** owner releases verify empty input. Watched nuisance false cancellation is **0/15**. Endpoint-only quiet targets detect **0/15**. Every final monitored ROI equals its initial clear ROI. Mechanical deadline cleanup works, but a missed stop cue still causes task-inappropriate continuation; release verification is not semantic success.

The maximum observed interval from one acquisition end to the next start is **20.854 ms**, despite the nominal 10 ms period. It occurs in a nuisance control, not a fabricated extra target failure. Consequently, 15/15 detections at nominal 10 ms do **not** establish a universal 10 ms minimum-visible-duration guarantee.

For fifteen watched nuisance windows, cumulative ROI acquisition-call wall time is median **6.894 ms**, range **5.436-15.516 ms**, per 600 ms window. This is not whole-monitor CPU use; predicate work and thread scheduling are excluded. All 3,791 intermediate acquisitions and 240 endpoint acquisitions are retained.

## Metric definitions and unit check

| Field | Meaning | SI unit (display unit) | Definition / condition | Type |
|---|---|---|---|---|
| nominal_width_ms | Requested cue interval | s (ms) | Fixture argument; {2,5,8,10,15,20}; not actual render duration | Scalar |
| actual_duration_ms | Measured cue duration proxy | s (ms) | Cue-off draw completion minus cue-on draw completion | Scalar, positive |
| cue_to_app_release_ms | Task reaction latency | s (ms) | App KeyRelease timestamp minus cue-on draw completion | Scalar |
| gap_around_cue_ms | Unobserved interval containing a cue | s (ms) | Next acquisition start minus preceding acquisition end; present only when the entire app-draw bracket fits | Scalar or unavailable |
| detected | Retained matching-pixel event | 1 | At least one matching ROI sample plus latched detection record | Boolean |

Timestamp arithmetic uses integer nanoseconds in one local monotonic clock domain, then divides by 1,000,000 for milliseconds. This is a time difference, not a frequency or a CPU-consumption measure. Draw completion is not physical scanout/photon time, and reported clock resolution is not calibrated timing uncertainty. CPython's clock and scheduling semantics are documented at https://docs.python.org/3.13/library/time.html.

## H / T / D / C / U

**H:** Fixed-period polling can miss short visible events as their timing moves between observations.

**T:** Frozen 120-case workload, one unchanged detector, four excluded 80 ms setup cases; no adaptive repeats. All original raw records, pixels, environment and source hashes retained.

**D:** **SAMPLING_LIMIT_OBSERVED**. The preregistered condition is met: sub-period misses exist, all fifteen 20 ms watched target controls are detected, and all release/provenance/nuisance gates pass. Reject unrestricted use for arbitrarily short stop cues; do not promote a new runtime from this result.

**C:** Rendering/timer jitter changes actual cue duration; initial watcher/keypress ordering is correlated; declared colours and ROI are easier than arbitrary GUI semantics. Sampling-time errors, frame visibility and detector errors must not be conflated. A post-detection latch cannot recover an event never sampled.

**U:** Three repetitions per width/offset, one synthetic fixture/host, shared unpinned CPU and software drawing timestamps. Counts are descriptive; no confidence interval for an i.i.d. population, calibrated combined uncertainty or coverage factor is asserted. All-15 success is not a hard real-time bound. No Doom efficacy, model understanding or GUI generality claim follows.

## Audit and retention

The separately implemented offline audit checks the explicit 120-case schedule, original raw-file SHA-256s, source/preregistration hashes, owner/fixture input transitions, cancellation versus expiry, final observation ordering and all referenced decompressed pixel payloads. It derives the tables from raw records rather than trusting online summary flags. **PASS_RAW_AUDIT**. Eight synthetic corruption controls (release, duplicate input, cue loss, stale observation, predicate, missing pixels, deadline rebinding, erased latch) are rejected; they are not additional live samples.

`manifest.json` binds the two complete lossless archives and every binary chunk to byte counts, SHA-256 and Git blob identities. The evidence archive contains all 120 original raw records and their sampled pixels. The source archive contains exact executed sources, preregistration, setup records, audit program, controls and reportable results. Lossless frame-delta encoding only reduces storage: reconstruction must reproduce each original raw.json byte-for-byte, including timestamps and formatting, before auditing.

Run offline from this directory:

```sh
python reconstruct.py /tmp/short-cue-retained
python /tmp/short-cue-retained/study/audit.py /tmp/short-cue-retained/measured-01 /tmp/short-cue-retained/study
python /tmp/short-cue-retained/study/test_audit.py /tmp/short-cue-retained
```

These commands do not launch GUI input. A new live benchmark requires a new allocation identity and output directory; this allocation is consumed. Previous #174 evidence and main runtime remain unchanged.

## One successor question

At a fixed 5 ms cue workload, does changing only polling period from 10 ms to 2 ms reduce misses without unacceptable acquisition cost or deadline-release regression? Freeze that comparison separately; do not infer its result from this matrix. Application-side retained events are a different alternative requiring an additional producer contract, not a free fix for arbitrary non-cooperative GUIs.
