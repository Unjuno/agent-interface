# Effect-side dependency commit discovery v1

## Decision

**RETAIN as a cooperative mechanism candidate, not as a generic GUI capability:** a planned effect can be guarded against semantic state races when the **effect owner** performs a dependency-scoped compare-and-apply under the same indivisible state boundary as the mutation.

Four bounded rungs isolate what is required:

1. moving document/revision checking from the client to the effect owner closes the previously demonstrated check-to-input race in this cooperative fixture;
2. guarding only the relevant document revision preserves unrelated progress better than a coarse global revision;
3. the dependency check and effect mutation must actually be atomic — colocating them without one state boundary is insufficient;
4. the dependency token must remain bound to the observation that produced the plan — silently refreshing only the token launders a stale plan and recreates wrong effects.

This is **not** a claim that arbitrary GUIs expose a transactional effect API. The fixture deliberately supplies an extra application contract over X11 properties. The next generality question is therefore whether useful real applications expose an equivalent compare-and-apply boundary, and what safe fallback remains when they do not.

## Provenance and scope

Repository source base used for the inherited `TargetHandleStore` sources: `21fb50be01e99816eb3a555e2ae131e679723f48`.

Imported source blobs were checked before every run:

- `scoped_target_handle_v1.py`: Git blob `c4482bb7cd9c3a3e780c05bafa34073491a33ece`
- `coordinate_frame_transform_v1.py`: Git blob `972daffee40a38d3effbd8155f3da133d664e445`

All new work is isolated under `research/context_effect_commit_discovery_v1/**` when retained. No shared runtime, Doom formal allocation, existing preregistration, or retained historical result is modified.

The environment is a private 320x200x24 Xvfb display, one native Tk button, full RGB X11 observations through Pillow/XCB, and native XTEST ButtonPress/ButtonRelease. The normal button callback owns the application mutation. The experimental application additionally publishes semantic document context and, for the candidate arm, accepts an expected dependency token. That is an explicit cooperative backend contract, not ordinary screenshot-only information.

Across the four completed allocations: **840 scored decision rows**. Rungs 1–2 use 20 repetitions per named condition; rungs 3–4 use 30 repetitions per named condition. Repetitions reuse fixed deterministic scenes and are not independent applications.

## Rung 1 — effect-owner CAS versus client precheck

Question: can effect-owner compare-and-apply remove the final race already shown to survive repeated client prechecks?

The planned action is fixed: write value `1`, derived from document A revision 0/value 0. Both arms first pass the same pixel/child-XID/document/revision precheck. The intervention is whether the application callback rechecks the plan-bound dependency before mutation.

| Change after client precheck | client precheck only | effect-owner CAS |
|---|---:|---:|
| stable | correct effect 20/20 | correct effect 20/20 |
| switch to B | **wrong effect 20/20** | reject 20/20 |
| edit A | **wrong effect 20/20** | reject 20/20 |
| edit unrelated B | correct effect 20/20 | correct effect 20/20 |
| A→B→A unchanged | correct effect 20/20 | correct effect 20/20 |
| A→B, edit A, →A | **wrong effect 20/20** | reject 20/20 |

**Disposition:** PASS at the cooperative mechanism level. The candidate eliminated all 60 seeded relevant post-check races while preserving all 60 known-valid cases in this allocation.

The effect-side dependency comparison itself was small relative to GUI transport: client-precheck callback check median 0.244 µs versus effect-CAS check median 2.086 µs. Input-start to effect/rejection terminal median was 0.602 ms and 0.744 ms respectively. These are mechanism timings in one synthetic fixture, not end-to-end product speedups.

## Rung 2 — relevant dependency versus global revision

Question: is a single global epoch a simpler equivalent guard?

Both arms use atomic effect-side CAS. Only the dependency set changes.

| Condition | relevant document+revision | global revision also required |
|---|---:|---:|
| stable | correct 20/20 | correct 20/20 |
| switch B | reject 20/20 | reject 20/20 |
| edit A | reject 20/20 | reject 20/20 |
| A→B→A with edited A | reject 20/20 | reject 20/20 |
| unrelated B edit | **correct 20/20** | **reject 20/20** |
| A→B→A unchanged | **correct 20/20** | **reject 20/20** |

The coarse global guard was safe in these seeded cases but rejected 40/40 semantically valid cases that changed only irrelevant/global state. The relevant guard retained them.

Median comparison cost: relevant dependency 2.330 µs; global tuple 2.748 µs. The important result is semantic selectivity, not the sub-microsecond difference.

**Disposition:** RETAIN dependency-scoped invalidation; REJECT “any global change invalidates every planned effect” as the default mechanism in this fixture.

## Rung 3 — atomicity is required

Question: is it enough to perform the check inside the application, even if the check and write are separated?

A deterministic competitor is released immediately after the effect-side check. The non-atomic arm releases the state lock and deliberately leaves a 2 ms gap before mutation. The atomic arm holds the same state lock across check and mutation; the competitor can run only after that linearization point.

| Case | non-atomic effect-side check | atomic compare-and-apply |
|---|---:|---:|
| stable | correct 30/30 | correct 30/30 |
| concurrent edit A | **wrong 30/30** | correct-at-linearization 30/30 |
| concurrent switch B | **wrong 30/30** | correct-at-linearization 30/30 |

Independent timestamp audit confirmed the competitor occurred before the effect in 60/60 non-atomic race cases and after the effect linearization in 60/60 atomic cases.

The 2 ms gap is an intentional deterministic discriminator; it is not an estimate of a natural race frequency.

**Disposition:** PASS for the narrow claim that compare and mutation must share an indivisible application-state boundary. Merely moving the check closer to the effect does not establish the same property.

## Rung 4 — dependency tokens must remain plan-bound

Question: after state changes, may an executor simply replace stale dependency metadata with the newest context while keeping the old planned action?

Both arms use the same atomic effect-side CAS. The only difference is the source of the expected dependency token.

| State before arm | original plan-bound token | refreshed current token with old action |
|---|---:|---:|
| stable | correct 30/30 | correct 30/30 |
| A externally edited | reject 30/30 | **stale overwrite 30/30** |
| switched to B | reject 30/30 | **wrong-document effect 30/30** |

Thus a fresh token does not make a stale plan fresh. It can instead certify the current state while silently detaching the action from the evidence that produced it.

**Disposition:** FAIL for independent token refresh. A dependency token must be causally bound to the planner evidence/action (or the action must be replanned/semantically revalidated), not rewritten just to satisfy admission.

## Measurements

Common environment for the completed allocations:

- Linux 6.18.44 x86_64
- CPython 3.13.5
- Pillow 12.3.0/XCB
- Tk 8.6.16
- reported CPU: Intel Xeon Platinum 8573C
- 5 visible CPUs, affinity 0–4
- sampled CPU frequency: 2300 MHz; not pinned
- batch: 1
- GPU: none
- X server CPU is not included in Python process timing
- `perf_counter_ns` uses `CLOCK_MONOTONIC`; 1 ns reported resolution is not claimed accuracy

Capture medians by allocation were 0.337–0.408 ms. One Rung-1 capture outlier reached 72.535 ms; scheduler/host contention was not independently instrumented, so no distributional performance claim is made from it.

### Variable / parameter table

| Name | Meaning | SI unit | Definition | Domain / assumption | Type |
|---|---|---|---|---|---|
| `document` | semantic target document identifier | 1 | fixture-published A/B identity | unique within fixture instance | string identifier |
| `revision` | relevant document version | 1 | incremented on each content mutation | monotone in fixture; no hidden update | integer scalar |
| `global_revision` | all-state change version | 1 | incremented for relevant and irrelevant fixture transitions | monotone in fixture | integer scalar |
| expected token | plan dependency passed to effect owner | 1 | instance/document/revision, optionally global revision | trusted cooperative contract | record |
| `value` | synthetic document value | 1 | A starts 0, B starts 100, planned write is 1 | dimensionless fixture state | integer scalar |
| XID | observed X11 child identity | 1 | native X resource ID | stable in these allocations | integer identifier |
| `box` | target image box | 1 (pixel count) | 32x24 px at (96,80) | physical size unknown | integer 4-vector |
| `offset` | click point within box | 1 (pixel count) | (16,12) | inside target box | integer 2-vector |
| `t` timestamps | monotonic event endpoints | s, stored as integer ns | `perf_counter_ns` | same local clock domain | integer scalar |
| repetitions | repeated trials per named case | 1 | 20 or 30 depending on rung | deterministic fixture, not population samples | integer scalar |

Unit check: elapsed milliseconds equal same-clock nanosecond endpoint differences divided by 1,000,000; microseconds divide by 1,000. Pixel coordinates are counts and are not converted to physical length.

## H / T / D / C / U

**H:** correctness-preserving continuation across planner delay requires effect admission to carry the exact semantic dependencies of the plan into an atomic effect-owner compare-and-apply boundary; unrelated state should not invalidate the effect, and dependency evidence must not be refreshed independently of the plan.

**T:** four finite, source-frozen local allocations above. Same native target and XTEST delivery; one causal factor changed at each rung. No formal Doom/model allocation consumed. First completed outcome retained for every allocation ID.

**D:** RETAIN the cooperative effect-CAS mechanism candidate: Rung 1 removes all seeded post-check relevant races; Rung 2 preserves irrelevant progress; Rung 3 establishes the need for atomicity; Rung 4 rejects token laundering. General GUI promotion remains HOLD because ordinary applications may not expose such a semantic commit boundary.

**C:** the improvement is explained by stronger application cooperation, not by better pixels, more frequent observation, or faster model reasoning. A transactional app API may simply move complexity into an unavailable backend. Hidden dependencies, incorrect revision maintenance, forged context, or same-token semantic changes could invalidate the result.

**U:** one synthetic application, fixed scenes, deterministic interventions, trusted context publication, no authentication/adversarial app, no model/network, no physical compositor/GPU, no arbitrary browser/canvas semantics, no Doom efficacy, no production authority/lease stack. Repetitions test mechanism consistency, not population reliability. Combined standard uncertainty `u_c` and coverage factor `k` are not estimated; empirical ranges are retained instead.

## ERROR CHECK

A second-generation independent auditor (`audit_all_v2.py`) imports none of the experiment runners or `TargetHandleStore`. It reclassifies every effect from retained pre-effect state and checks run manifests, paired input equivalence, event ordering, mode/case expectations, and atomic linearization ordering. Result: **840/840 rows passed**.

Two semantic corruption tests then recomputed file manifests after tampering, so hash checking alone could not catch them:

1. disguise one refreshed-token stale overwrite as if it began from A revision 0;
2. invert one atomic trial's competitor/effect ordering.

The v2 audit rejected both corrupt copies for semantic inconsistency. The earlier per-rung audits remain retained; v2 supersedes them for cross-run semantic validation.

## Smallest successor

Do **not** immediately add fuzzy vision, another client precheck, or silently promote an application transaction API to a universal GUI feature.

The next discriminating question is **generality of the commit boundary**:

- identify one real application/domain where an independently observable versioned effect boundary exists and test the same plan-bound CAS invariant; or
- in a deliberately non-cooperative GUI, demonstrate exactly what guarantee remains impossible and what fail-closed/yield policy is required.

A second-domain result should keep the same distinction between target identity, semantic dependency validity, effect atomicity, and planner-evidence provenance.
