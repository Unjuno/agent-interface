# Real MAP01 control-cutoff study v1

Status: **development PASS for owner-enforced lease cutoff; segmentation candidate refuted under this runtime path; no gameplay efficacy claim.**

## Purpose

Run real ViZDoom in the disposable container and choose between control-shaping mechanisms rather than spending the allocation on construction. Historical real MAP01 evidence showed requested holds can be extended by synchronous capture work. This study first tests pulse segmentation, then tests an alternative: submit one long hold while the independent InputOwner lease deadline ends physical authority.

## Runtime / evidence base

- immutable runtime source bundle: `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`; exported by GitHub Actions run `34973453255`, artifact `10398313098`;
- ViZDoom 1.3.0 / Freedoom MAP01, threat-contact-v2 saved fixture, skill 1, ASYNC_SPECTATOR 35 Hz;
- CPython 3.13.5, Linux 6.18.44, INTEL(R) XEON(R) PLATINUM 8573C, affinity 0--4, frequency not pinned;
- private Xvfb/Openbox, 640x480 visible game;
- zero model calls.

The current repository main moved independently during the experiment. No runtime or historical allocation was mutated.

## Experiment A — segmentation sweep

Twelve fresh sessions: coast 250 ms, normal `d` hold 1x250 ms, 2x125 ms, and 5x50 ms; three sessions per condition. Split conditions add an explicit observe after each pulse, matching the previously explored recovery-pulse shape.

| condition | physical-retention upper median | program-duration median | typed observations median |
|---|---:|---:|---:|
| coast | 0 ms | 310.504 ms | 2 |
| normal 1x250 | 255.706 ms | 391.352 ms | 4 |
| split 2x125 | 312.576 ms | 581.087 ms | 7 |
| split 5x50 | 362.186 ms | 1031.061 ms | 15 |

All 12 completed with verified empty release, zero scorer leaks and zero missed scorer periods. Health stayed 97 and terminal independent score stayed 0 kills / 0 deaths / no exit. **Segmentation does not reduce overshoot here.** More pulse boundaries create more capture/release/re-admission work and substantially increase total program duration.

## Experiment B — owner-enforced lease cutoff

Nine fresh sessions submit a 2000 ms `d` hold but set runtime authority to expire at 100, 150, or 250 ms; three sessions per cutoff. The program is expected to terminate `expired`; that status is not relabelled as normal completion. The measurement question is physical release timing.

| cutoff | admission→verified-empty upper median | deadline→verified-empty median | terminal-after-deadline median |
|---|---:|---:|---:|
| 100 ms | 99.105 ms | 0.514 ms | 10.934 ms |
| 150 ms | 149.227 ms | 0.659 ms | 50.596 ms |
| 250 ms | 249.461 ms | 0.728 ms | 58.303 ms |

Every owner interruption is `reason=expired`, `verified=true`, with empty physical key/button state. All scorer checks pass and health/terminal scores remain unchanged. The result separates **input-authority end** from **Executor/observation terminal**: input is verified empty in under 1 ms after the deadline in all nine samples, while terminal publication can lag by tens of milliseconds. This is scheduler-dependent evidence, not a hard real-time guarantee.

## Experiment C — matched normal 250 ms vs lease-cutoff 250 ms

Three same-fixture/same-seed fresh pairs, order normal→lease, lease→normal, normal→lease. The lease upper bound includes verified-empty time and is therefore conservative relative to just issuing the release.

| pair | normal hold upper | lease cutoff upper | lease - normal | deadline→empty |
|---|---:|---:|---:|---:|
| 1 | 313.077 ms | 249.187 ms | -63.889 ms | 0.573 ms |
| 2 | 259.160 ms | 249.321 ms | -9.838 ms | 0.528 ms |
| 3 | 313.668 ms | 249.654 ms | -64.014 ms | 0.831 ms |

All 3/3 pairs favor lease cutoff. Normal upper median is **313.077 ms**, lease upper median **249.321 ms**, and the median within-pair difference is **-63.889 ms**. Only three pairs exist, so no population confidence interval or broad speed claim is justified.

## Failures retained

1. First startup failed before `ready` because `openpyxl` was absent. No GUI/Doom measurement was produced. The retained offline wheel was installed before any measured case.
2. The first 12-session shell allocation hit its outer tool timeout after seven completed cases; the next case had only setup files and no ready/input evidence. That incomplete directory is preserved. Remaining fresh sessions were executed as small blocks; the incomplete setup is not pooled.

## H / T / D / C / U

**H.** Physical input authority bounded by the independent owner deadline can track the intended cutoff more tightly than capture-coupled `hold` duration or repeated pulse segmentation.

**T.** 12 fresh segmentation sessions, 9 cutoff-sweep sessions, and 3 fresh matched pairs (6 sessions), all from the same saved threat fixture with zero model calls; raw events and independent terminal scorer agreement audited.

**D.** Segmentation: **REJECT for overshoot reduction on this path**. Lease cutoff: **PROMOTE as a separate mechanism candidate**, not as a production runtime change.

**C.** The advantage may come from bypassing capture-coupled worker completion, not from better gameplay. Expected expiry is currently represented as an exceptional terminal status. A production semantic could accidentally hide a real stale-authority failure if it treats all expiry as success. Different hosts may have worse owner scheduling.

**U.** n=3 per condition/pair, shared-host frequency, one fixture, one key, no model/planner, no positive game outcome. Health is unchanged in this fixture, so safety/efficacy under active damage is unresolved.

## Next high-information experiment

Do **not** add more segmentation variants. Compare expected owner-deadline cutoff against explicit controller cancellation and against a short no-capture motor primitive under a fixture where health actually changes. Primary endpoints: deadline/cancel-to-verified-empty, physical occupancy bounds, health delta, and independent useful/harmful events. Keep terminal lifecycle separate from input-authority lifetime.
