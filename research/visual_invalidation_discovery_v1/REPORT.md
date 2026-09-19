# Visual invalidation discovery v1

Status: **development evidence / isolated disposable fixture**. This is not a formal MAP01 allocation and does not establish gameplay efficacy.

Base commit: `5ea234d204e776774a6cdd46972cc0daa9b79766`
Issue: #104
Branch: `research/visual-invalidation-discovery-5ea234d`

## Question

What is the smallest visual invalidation mechanism that can stop a renewable local policy quickly without turning unrelated screen motion into a false abort?

The experiment ladder changed one important factor at a time:

1. detector family on synthetic images;
2. rendering-jitter magnitude;
3. effect magnitude;
4. ROI size;
5. sampling cadence;
6. real X11 capture through Xvfb/Tk/Pillow;
7. unrelated visual mutation outside the declared ROI.

## Environment

- Linux 6.18.44 x86_64, glibc 2.41
- Python 3.13.5
- NumPy 2.3.5
- OpenCV 4.13.0
- Pillow 12.3.0
- reported CPU count: 5
- X11 development fixture: Xvfb `:99`, Tk 8.6

These are container-development measurements. No physical compositor/GPU/display latency is included.

## R1: detector-family screen

Fixture: 256x256 grayscale image; 64x64 declared ROI; 24x24 target change; intensity delta 40; independent Gaussian rendering jitter sigma=2; 2,000 no-change + 2,000 changed pairs per detector. Fixed thresholds were chosen before the run.

| detector | FPR | FNR | median compute | p95 compute |
|---|---:|---:|---:|---:|
| full-frame any-change | 100% | 0% | 8.64 us | 10.03 us |
| ROI any-change | 100% | 0% | 4.38 us | 5.93 us |
| full-frame MAD | 0% | 0% at sigma=2 only | 46.33 us | 74.68 us |
| ROI MAD | 0% | 0% | 8.88 us | 12.61 us |
| ROI changed-pixel fraction (NumPy) | **0%** | **0%** | **5.35 us** | **7.92 us** |
| ROI changed-pixel fraction (OpenCV) | 0% | 0% | 11.92 us | 13.20 us |

Noise ablation exposed two important failures:

- `any-change` became 100% false-positive at sigma >= 0.5.
- full-frame MAD failed to detect the true change at sigma 0/0.5/1, then began detecting at sigma=2 because background noise lifted the mean difference across threshold. Its apparent success therefore depended on nuisance noise.
- the fixed ROI changed-pixel-fraction detector stayed at 0 FPR / 0 FNR through sigma=2, reached 1.8% FPR at sigma=4, and reached 100% FPR at sigma=8.

Disposition: reject exact/global change gates as a semantic invalidation primitive. Retain ROI changed-pixel fraction as the simplest candidate for the next rungs, with explicit noise limits.

## R2: effect magnitude

With sigma=2, 64x64 ROI, 24x24 target, the retained fraction detector had a sharp sensitivity boundary under the fixed pixel threshold: 0% hit at delta 8 and 100% hit at delta 12. ROI MAD switched from 0% to 100% at delta 16. This is not a universal detector; thresholds and expected effect size are part of its contract.

## R3: scope-size ablation

A smaller 12x12 target (delta 16, sigma=2) was evaluated while changing only ROI size. Fixed detector: abs-difference >=12 on at least 5% of ROI pixels; 1,500 pairs/class.

| ROI | target area fraction | FPR | FNR | median compute |
|---:|---:|---:|---:|---:|
| 24x24 | 25.0% | 0% | 0% | 3.84 us |
| 32x32 | 14.1% | 0% | 0% | 4.03 us |
| 40x40 | 9.0% | 0% | 0% | 4.33 us |
| 48x48 | 6.25% | 0% | 0% | 4.52 us |
| 64x64 | 3.52% | 0% | **100%** | 5.09 us |
| 96x96 | 1.56% | 0% | 100% | 6.69 us |
| 128x128 | 0.88% | 0% | 100% | 8.50 us |
| 256x256 | 0.22% | 0% | 100% | 23.57 us |

This was the key discovery: target-scoped observation is not merely a performance optimization. Under a fixed evidence rule it determines whether a small semantically relevant change is even observable.

## R4: cadence ablation

Using the retained 48x48 ROI candidate with pre-generated frames, only sampling cadence changed. Event phase was randomized within one sampling interval; 60 trials/cadence.

| cadence | median event-to-detect | p95 | max | estimated detector compute share* |
|---:|---:|---:|---:|---:|
| 30 Hz | 15.611 ms | 30.860 ms | 33.162 ms | 0.013% |
| 60 Hz | 6.875 ms | 15.181 ms | 15.971 ms | 0.027% |
| 120 Hz | 3.708 ms | 8.099 ms | 8.265 ms | 0.053% |
| 240 Hz | 2.241 ms | 4.031 ms | 4.172 ms | 0.107% |

`*` detector-only median 4.457 us multiplied by cadence; this is a compute-budget proxy, not measured process CPU utilization.

Conclusion: once the detector is this small, cadence/capture dominates reaction latency.

## R5: real X11 capture increment

A real Tk window was painted on Xvfb and captured through Pillow ImageGrab. The 48x48 direct ROI capture was compared with a 256x256 full capture followed by crop; 30 state-change trials/method, max-speed capture loop.

| method | median X11 capture call | p95 | median paint-event-to-detect | p95 |
|---|---:|---:|---:|---:|
| full 256x256 then crop | 0.323 ms | 0.556 ms | 0.456 ms | 0.687 ms |
| direct 48x48 ROI | **0.276 ms** | **0.471 ms** | **0.385 ms** | **0.582 ms** |

The gain is modest in Xvfb, but capture already costs roughly two orders of magnitude more than the detector itself. Physical display/compositor/GPU conditions remain unknown.

## R6: irrelevant visual mutation

Same Xvfb fixture, same changed-pixel threshold of 100 pixels. A 12x12 relevant target lived inside the 48x48 policy ROI. A separate 16x16 nuisance object lived outside it. 30 trials/cell.

| observer | relevant target hit | unrelated nuisance hit | median capture |
|---|---:|---:|---:|
| global 256x256 | 30/30 | **30/30 false invalidations** | 0.319-0.362 ms |
| scoped 48x48 ROI | **30/30** | **0/30** | 0.226-0.233 ms |

This isolates the strongest current result: **semantic scoping prevents an invalidation guard from treating unrelated screen activity as a reason to revoke the active policy.** No object recognition was required in this fixture.

## H / T / D / C / U

### H
A planner-declared visual invalidation scope plus a simple local change predicate can provide fast invalidation evidence with lower false-abort exposure than whole-frame change monitoring.

### T
Disposable synthetic frames first, then Xvfb/Tk/Pillow. One factor was added per rung. No model calls, Doom allocation, shared runtime writes, or existing preregistration changes.

### D
**PASS / RETAIN for further development**, limited to the tested fixture class. The retained candidate is not "generic image diff"; it is **scoped ROI + explicit change predicate + bounded cadence**. Global any-change is rejected. Whole-frame aggregate difference is rejected as a default invalidation mechanism.

### C
The benefit may disappear if the target moves outside the ROI, if relevant changes are subtler than the declared pixel/effect threshold, or if the application itself produces high-frequency animation inside the ROI. A semantic ROI can also become stale.

### U
Synthetic noise model; small sample counts; Python/NumPy implementation; Xvfb rather than a physical display; no OS-input release path in these visual rungs; no learned detector; no target identity tracking; no model/network latency; no MAP01 efficacy evidence.

## Next smallest experiment

Do not add a learned vision model. Add exactly one failure: **target motion relative to the declared ROI**. Determine the spatial drift at which the current scoped detector stops being valid. Only if that failure is observed should a bounded local revalidation/search margin be introduced and compared against simply enlarging the ROI (which may reintroduce nuisance false invalidations).
