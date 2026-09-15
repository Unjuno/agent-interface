# Real MAP01 scheduled-cutoff comparison v1

Status: **development PASS for control-authority timing; owner deadline is the preferred scheduled-cutoff candidate. Gameplay superiority is not established.**

## Question

The retained cutoff study at `478cde3621733bd601152dcec4c2079f6f7fda79` rejected pulse segmentation and promoted owner-enforced expiry as a candidate. This follow-up compares three ways to end an approximately 600 ms authority interval on actual ViZDoom/X11 execution:

1. owner deadline — a long ordinary hold whose independent InputOwner authority expires at the planned cutoff;
2. explicit cancel — a long ordinary hold followed by a controller cancel targeted at `input_ack + 600 ms`;
3. no-capture motor — an experimental hold with no screenshot/artifact work while held, duration measured after the final key-down acknowledgement, explicit release at 600 ms, then one post-release observation.

The comparison is mechanism-only, uses zero model calls, and makes no general gameplay-efficacy claim.

## Evidence base

Disposable container runtime source base: `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`, ViZDoom 1.3.0, Freedoom MAP01, `map01-threat-contact-v2`, skill 1, ASYNC_SPECTATOR 35 Hz, CPython 3.13.5, Linux 6.18.44, INTEL XEON PLATINUM 8573C, affinity 0..4, ephemeral private Xvfb/Openbox. Core v13/v12/release-telemetry sources were byte-identical to retained main-line blobs used by the preceding benchmark.

All pooled sessions use a 60 s episode timeout and strict five-field terminal scorer agreement. A first no-capture smoke accidentally used 20 s while the loaded fixture already exceeded that engine-time threshold; historical wall-time scoring and the timeout-aware independent scorer disagreed on `map_exit`. That run is excluded and retained as a harness failure.

## Damage-exposure matched triplets

A deterministic `Up + space` 1000 ms prelude moves the saved fixture into a timing-sensitive damage exposure. The comparison action is `Shift_L`, chosen to occupy keyboard authority without independently translating or attacking. Seeds `992500..992502` are each run once under all three methods.

The endpoint is **planned cutoff -> independently verified empty input**, not worker terminal publication. Expiry/cancel use the owner interruption `verified_ns`; normal motor release uses the post-batch owner-state verification timestamp.

| Method | n | cutoff -> verified-empty median | ack -> verified-empty median | final health |
|---|---:|---:|---:|---|
| owner deadline | 3 | **0.466 ms** | 600.300 ms | 100, 93, 93 |
| explicit cancel | 3 | 2.864 ms | 602.864 ms | 93, 93, 93 |
| no-capture motor | 3 | 0.804 ms | 600.804 ms | 93, 93, 93 |

All nine sessions ended with verified empty input, 0 deaths, 0 kills and no MAP01 exit. Strict terminal scorer agreement passes 9/9. The one owner-deadline run ending at health 100 prevents a causal health ranking; ASYNC_SPECTATOR wall timing at the pickup/damage boundary is too variable for a three-sample health claim.

## Useful-action triplet

One same-seed (`992600`) triplet uses `space`. All three methods independently produce **1 kill / 0 deaths / no exit**, and the independent scorer emits `KILL_COUNT_INCREASE`. Final health is 100 in all three.

| Method | cutoff -> verified-empty | ack -> verified-empty | outcome |
|---|---:|---:|---|
| owner deadline | **0.447 ms** | 600.375 ms | 1 kill |
| explicit cancel | 1.535 ms | 601.535 ms | 1 kill |
| no-capture motor | 0.610 ms | 600.610 ms | 1 kill |

This only establishes that tighter scheduled cutoff did not destroy the useful attack effect in this one exposure. It is not a population efficacy result.

## Decision

**Owner deadline: PROMOTE** as the preferred scheduled authority-cutoff primitive. It is independent of capture/worker completion and has the lowest median cutoff-to-empty delay in the three damage triplets.

**Explicit cancel: KEEP** for reactive invalidation. It traverses the controller command channel and is slower for a predeclared cutoff here.

**No-capture motor: do not promote solely for cutoff timing.** It mechanically removes capture-coupled hold inflation, but adds a new step semantic while owner expiry is tighter in median using the existing authority layer.

**Program lifecycle must remain separate from input-authority lifetime.** Expected scheduled authority cutoff should not be represented as an unexpected stale-program failure.

## H / T / D / C / U

**H.** On real MAP01, independent owner deadline expiry ends input authority closer to a predeclared cutoff than explicit controller cancellation while preserving observed task effects at least as well as the no-capture motor primitive in these exposures.

**T.** Three matched damage-exposure triplets plus one useful-action triplet, fresh sessions per arm, same fixture/seed within triplet, zero model calls, independently verified empty-input endpoint, strict scorer agreement.

**D.** **PASS for authority-timing mechanism selection; UNCERTAIN for gameplay benefit.** Owner deadline has lower median cutoff error than cancel; all release/scorer gates pass; the useful triplet preserves the same kill outcome.

**C.** Shared-host scheduling affects sub-ms values; ASYNC_SPECTATOR makes health timing nondeterministic; the no-capture path is experimental; one useful triplet is sparse.

**U.** Dominant uncertainty is transfer to planner/model workloads and larger gameplay samples. No hard-real-time, human-reaction, general DOOM or general GUI claim follows.

## Architecture implication / next gate

Prototype a **dual-lifetime control contract**: an owner-enforced input-authority deadline distinct from the program/observation lifecycle deadline. Planned authority end should be a normal event while reactive cancellation, focus loss and stale-program failure remain separate causes. Then integrate the mechanism into one recovery/planner-wait path.