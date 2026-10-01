# Dual-lifetime / capture-placement discovery block v1

Status: **RETAIN dual-lifetime safety semantics; PROMOTE quiet/no-in-hold-capture for short scheduled motor windows in this development path; HOLD the fixed 100 ms guard-band candidate. No gameplay-efficacy or planner/model claim.**

## Why this block exists

The retained real-MAP01 cutoff comparison at `74e2d612d3344c3f35f71ab62c9ed29b426f58ac` selected the independent InputOwner deadline as the preferred scheduled input-authority cutoff and explicitly left the program/observation lifetime as the next gate. Existing `EXPIRY_OBSERVATION.md` had already shown that passive samples can be collected after verified expiry, but kept terminal status `expired` and did not test this on the current v13 MAP01 measurement path.

This block follows Issue #105's one-variable discovery rule. It uses the immutable runtime source bundle `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`, ViZDoom 1.3.0 / Freedoom MAP01 / `map01-threat-contact-v2`, ASYNC_SPECTATOR 35 Hz, private Xvfb/Openbox, CPython 3.13.5, Linux 6.18.44, shared Intel Xeon Platinum 8573C host, and zero model calls. CPU frequency is not pinned.

## Experiment A — dual lifetime, unchanged capture-coupled hold

Candidate change: when the independent owner ends input because its predeclared deadline expires, verified release is treated as a normal `authority_ended` event. The original program tail does not resume. Exactly one passive snapshot may run under a separate 400 ms observation-lifecycle budget, then terminal is published. Cancellation/focus/surface causes are not relabelled.

Baseline: unchanged v13/v12 expiry -> terminal `expired`, after which the harness must submit one separate observe-only program.

Three fresh matched pairs, seeds 993100..993102, 600 ms authority window, `Shift_L` hold request 2000 ms. A smoke-only attribution defect first counted an in-flight hold frame as the baseline's separate fresh observation; it was retained locally and the harness was corrected before the formal block by requiring the declared observation ID/sequence.

| Metric | baseline | dual-lifetime candidate |
|---|---:|---:|
| n | 3 | 3 |
| deadline -> verified empty median | 0.655 ms | 0.714 ms |
| verified empty -> declared fresh capture median | **33.738 ms** | 38.993 ms |
| extra observe submission after primary terminal | 1 | **0** |
| post-release input admissions | 0/3 | 0/3 |
| strict final scorer agreement | 3/3 | 3/3 |

All candidate runs emitted one post-authority observation inside the 400 ms lifecycle budget and terminal `authority_ended`. The preregistered decision code retains/promotes this as a mechanism candidate because it removes one extra submission without >2 ms release regression. **It did not improve fresh-observation latency**; its median was 5.255 ms slower. Treat this as a boundary/semantic result, not a speedup.

## Experiment B — remove observation work while input is actively held

The dual-lifetime executor is unchanged. The only mechanism change is that the keyboard hold performs no screenshots/artifact work while held; after owner expiry, the same one passive snapshot runs.

Three fresh matched pairs, seeds 993200..993202.

| Metric | capture-coupled hold | quiet hold |
|---|---:|---:|
| n | 3 | 3 |
| deadline -> verified empty median | 2.009 ms | **0.910 ms** |
| verified empty -> fresh capture median | 34.569 ms | **4.445 ms** |
| paired fresh-capture improvement median | — | **28.102 ms** |
| post-release input admissions | 0/3 | 0/3 |
| strict final scorer agreement | 3/3 | 3/3 |

All hard gates passed. This crosses the preregistered >=10 ms paired-improvement gate and does not regress release timing. **PROMOTE as a mechanism candidate for short scheduled motor windows where intermediate visual feedback is not required.** It is not yet a general dynamic-control policy because it intentionally gives up observations during the active hold.

## Experiment C — preserve observations, suppress only the last 100 ms

The prior capture-coupled formal runs had `capture_to_artifact_ready_ms` max 79.212 ms. Before this experiment, that observed maximum was rounded up to one fixed 100 ms guard band; no sweep was permitted. The guard arm keeps periodic hold observations but starts no new snapshot when <=100 ms of input authority remains.

Three fresh matched pairs, seeds 993300..993302.

| Metric | capture-coupled hold | 100 ms guard band |
|---|---:|---:|
| n | 3 | 3 |
| pre-release observations median | 6 | 5 |
| deadline -> verified empty median | **0.534 ms** | 0.737 ms |
| verified empty -> fresh capture median | 4.206 ms | **3.290 ms** |
| paired fresh-capture improvement median | — | **0.947 ms** |
| post-release input admissions | 0/3 | 0/3 |
| strict final scorer agreement | 3/3 | 3/3 |

All hard gates passed, but the preregistered >=10 ms paired-improvement threshold failed. One capture-coupled pair had a large tail; the other two were already fast. **HOLD.** Do not tune 50/150/200 ms after seeing this block merely to find a favorable width.

## Concurrent evidence / coordination note

While this block was running, `main` advanced independently to `d492586b7704a741c0b1a7999f31369f009745b1` with `container_two_phase_observation_publish_v1`: a rendered Xvfb/Tk/XTEST micro-test in which raw capture still occurs before release but PNG persistence/reopen moves after release, reducing application-observed hold by about 20.344 ms median while preserving raw/reopened pixel equality. That result was **not** an input to the preregistered studies above and is not pooled with them. It is convergent evidence that acquisition, physical authority and durable publication should be treated as separate phases. Do not combine its publication-order change with the quiet-hold mechanism in one first integration experiment; test one changed boundary at a time.

## H / T / D / C / U

**H.** Input authority and observation lifecycle can be separated without reopening input; delayed fresh state after expiry may be dominated by synchronous observation work that is already in flight on the worker.

**T.** Three sequential finite matched studies above, each n=3 pairs after smoke validation, fresh processes per arm, fixed seeds/order, zero model calls, same saved MAP01 fixture, owner-verified physical release and independent final scorer agreement. First outcomes are retained; no formal block was extended after seeing results.

**D.** Dual lifetime: **RETAIN for semantics/boundary reduction, no latency claim**. Quiet hold: **PROMOTE_MECHANISM_CANDIDATE** at this narrow scope. 100 ms guard band: **HOLD**. No broad runtime promotion follows yet.

**C.** Capture timing is host/scheduler dependent; eliminating all in-hold observations can hide relevant environment changes; a fixed guard can miss long capture tails; the `Shift_L` fixture tests authority mechanics rather than useful gameplay; the candidate status name could encourage callers to overread `authority_ended` as task completion if the ABI is poorly specified.

**U.** n=3 pairs per study, one key/fixture/host, unpinned CPU frequency, no frontier-model waits, no planner use, no cross-domain transfer. Sub-ms deadline values are observations, not hard-real-time guarantees. The dominant open question is whether a planner-facing short motor window can use the quiet/dual-lifetime shape without losing task-relevant reactions.

## Next high-information step

Do **not** sweep guard widths. Prefer the simpler result: for a deliberately short, predeclared motor window, use owner-enforced input lifetime with no capture inside that window, then mandatory passive observation after verified release. The next new experiment should expose exactly that two-phase primitive to one existing planner/recovery path and test whether the model correctly distinguishes `authority_ended` from semantic completion. If no model endpoint is available, first run a model-free caller integration that rejects any attempt to infer task success from `authority_ended` and requires the post-release observation before the next semantic decision.
