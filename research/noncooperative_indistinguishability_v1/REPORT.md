# Non-cooperative GUI semantic indistinguishability v1

## Decision

**FAIL for any generic claim that screenshot/XID freshness alone can make stale semantic plans safe when the relevant application state is not observable.**

**RETAIN fail-closed dependency-unavailable as the only safety-preserving fallback tested here:** if the planned effect depends on semantic state for which the interface has no trustworthy evidence, yield rather than treating visual stability as semantic stability.

This is a deliberately non-cooperative GUI fixture. It publishes no document ID, revision, hidden world label, or semantic context property. The target pixels, child XID, focus, geometry, and TargetHandle result are intentionally unchanged while the hidden document meaning changes.

## Provenance and scope

Source base: `21fb50be01e99816eb3a555e2ae131e679723f48`.

Unchanged inherited sources:

- `scoped_target_handle_v1.py` Git blob `c4482bb7cd9c3a3e780c05bafa34073491a33ece`
- `coordinate_frame_transform_v1.py` Git blob `972daffee40a38d3effbd8155f3da133d664e445`

Private Xvfb 320x200x24, native Tk target, Pillow/XCB screen capture, native XTEST click. Hidden semantic transitions occur inside the fixture without rendering or publishing semantic metadata. No model, network, shared runtime, Doom/formal allocation, or production authority path is used.

## Rung 1 — one observation, two policies

Three worlds are created with the same visible target:

1. `stable`: A remains revision 0/value 0; the prepared action is valid.
2. `hidden_edit_A`: A becomes revision 1/value 10 without visual change; the old prepared value 1 is stale.
3. `hidden_switch_B`: active document becomes B without visual change; applying the old action targets the wrong document.

The controller input is restricted to current RGB pixels, focus XID, child surface XID, child geometry, TargetHandle status and resolved point. It does not receive absolute world/case identity or semantic document state.

30 blocks × 3 worlds × 2 policies = **180 rows**.

| Policy / world | stable | hidden edit A | hidden switch B |
|---|---:|---:|---:|
| visible-match → act | correct 30/30 | **wrong 30/30** | **wrong 30/30** |
| semantic dependency required but unavailable → yield | yield 30/30 | safe yield 30/30 | safe yield 30/30 |

For every block and policy, the normalized observation signature was byte-for-byte identical across all three worlds. Independent audit: **60/60 indistinguishable world triplets**.

The safety/progress tradeoff is therefore not caused by a weak visual detector in this fixture. The required distinction is absent from the declared observation channel.

## Rung 2 — repeated screenshot polling

Competing explanation: perhaps one screenshot is insufficient and repeated observation reveals the semantic change.

Only observation count changes. Compare one visible frame versus ten visible frames, with 5 ms requested spacing between later captures. The hidden state does not render.

20 blocks × 3 worlds × 2 observation histories = **120 rows**.

| History / world | stable | hidden edit A | hidden switch B |
|---|---:|---:|---:|
| 1-frame visible history → act | correct 20/20 | **wrong 20/20** | **wrong 20/20** |
| 10-frame visible history → act | correct 20/20 | **wrong 20/20** | **wrong 20/20** |

Independent audit found **40/40 world-history groups** observation-identical. Every frame within each ten-frame history also had the same normalized visual/XID signature.

Observed history span:

- 1-frame arm median 0.368 ms, range 0.294–2.272 ms;
- 10-frame arm median 73.003 ms, range 66.589–111.527 ms.

The longer history spent materially more wall time but gained zero semantic discrimination in this fixture. The nominal 5 ms sleep spacing is not substituted for measured history duration.

## Impossibility statement for the declared observation contract

### Claim

For two application states that require different safe actions but produce exactly the same controller observation, no deterministic policy that receives only that observation can both act in the valid state and refuse in the invalid state.

### Proof

Take the stable state and one hidden-changed state from the retained paired fixture. The audit establishes that the complete declared controller observation is identical in both states. A deterministic policy is a function of that observation, so it must return the same decision in both states. There are only two relevant decisions in this experiment: act or yield. If it acts, the stable state succeeds but the hidden-changed state produces a stale or wrong-document effect. If it yields, the hidden-changed state is safe but the stable state is unnecessarily stopped. Therefore the policy cannot simultaneously satisfy both requirements on these observation-identical states. Repeating the same observation does not change the argument when the whole history is also identical, as verified in Rung 2. QED.

This is a statement about the explicitly restricted observation contract, not about all possible sensors or application APIs. Adding a trustworthy semantic version signal changes the information available and escapes the premise, as the preceding cooperative CAS experiment demonstrated.

## Measurements

Common environment:

- Linux 6.18.44 x86_64
- CPython 3.13.5
- Pillow 12.3.0/XCB
- Tk 8.6.16
- reported CPU: Intel Xeon Platinum 8573C
- 5 visible CPUs, affinity 0–4
- sampled frequency near 2300 MHz, not pinned
- batch 1, no GPU

Capture median: 0.398 ms in Rung 1 and 0.388 ms in Rung 2. Observed capture ranges were 0.287–3.744 ms and 0.288–5.820 ms respectively.

### Variable / parameter table

| Name | Meaning | SI unit | Definition | Domain / assumption | Type |
|---|---|---|---|---|---|
| world | hidden application state class | 1 | stable / hidden edit / hidden switch | withheld from controller | categorical |
| observation signature | controller-visible evidence | 1 | RGB hash + focus/surface XID + geometry + handle status/point | excludes hidden semantic state | record |
| document revision | hidden relevant content version | 1 | 0 or 1 in this fixture | not observable in this experiment | integer scalar |
| value | synthetic document value | 1 | A starts 0; hidden edit makes 10; planned write is 1 | dimensionless fixture state | integer scalar |
| frame count | number of current observations | 1 | 1 or 10 | fixed per arm | integer scalar |
| history span | first current-capture start to last current-capture end | s | monotonic timestamp difference | same local clock domain | nonnegative scalar |
| XID | native X resource identity | 1 | observed child/focus IDs | unchanged across paired worlds | integer identifier |
| pixel box | target image region | 1 (pixel count) | 32x24 at fixed location | physical size unknown | integer vector |

Unit check: history/capture milliseconds are same-clock nanosecond differences divided by 1,000,000. Pixel counts are not physical lengths.

## H / T / D / C / U

**H:** if a semantic dependency changes without affecting any observation available to the controller, more screenshot/XID observation cannot restore the missing distinction; safe continuation must either obtain a new trustworthy semantic channel or fail closed.

**T:** two finite frozen local allocations. Rung 1 compares visible-act versus dependency-unavailable yield on 180 rows. Rung 2 changes only history length, one versus ten frames, on 120 rows. Actual XTEST effects are independently scored from hidden pre-effect state.

**D:** FAIL the screenshot/XID-only safety claim: visible-act produced 100/100 wrong effects across hidden-changed rows over both rungs. PASS the indistinguishability mechanics: 60/60 one-frame triplets and 40/40 history groups were observation-identical. RETAIN dependency-unavailable yield as a safe fallback, with explicit completeness cost.

**C:** this is an adversarially constructed information gap. Real applications may render semantic state or expose accessibility/API/version evidence, in which case the states are no longer indistinguishable. Conversely, a system that labels unobservable dependencies as if they were stable would recreate the failure.

**U:** one synthetic GUI, fixed target, deterministic hidden transitions, no adversarial timing distribution, no model, no real office/browser/game domain, no accessibility tree, no production compositor. Repetitions verify mechanism consistency rather than population reliability. No combined standard uncertainty `u_c` or coverage factor `k` is estimated.

## ERROR CHECK

Rung-1 independent audit: **180/180 rows**, **60/60 observation-identical world triplets**.

Rung-2 independent audit: **120/120 rows**, **40/40 observation-identical world-history groups**.

Both audits recompute file hashes from retained manifests and classify actual application effects from hidden pre-effect state rather than trusting the controller decision.

## Smallest successor

The next experiment should no longer ask whether to poll faster. The result says to ask **which real domains expose enough semantic dependency evidence to escape this impossibility, and which do not**.

The highest-information next pair is one cooperative real application with a versioned/transactional effect boundary versus one non-cooperative real GUI where only observable UI state is available. Keep task/effect semantics matched as far as possible; do not treat accessibility or API metadata as equivalent to screenshot-only evidence without declaring it.
