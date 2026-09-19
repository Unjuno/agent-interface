# Lifecycle source-generation autoresearch v1

Decision: **RETAIN scoped source-generation admission candidate; do not promote to general liveness/authentication.**

Issue #199. Publication base `4e65e2ac3b6f0ff7cf4701d5986a479a990e90a0`; immutable executed runtime `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`. The measured source/threshold plan was frozen on GitHub before all 12 measured sessions. Shared runtime and historical evidence remain unchanged.

## Question

Can a provider defeat timestamp freshness by continuously delivering fresh but false `running` receipts after its underlying dynamic source has stopped, and can a source-generation freshness condition refuse **new** authority without guessing that stall means terminal?

The candidate changes one contract: lifecycle receipts bind to a provider source generation. In this ViZDoom provider the generation is the episode tic acquired by the evaluator. Delivery freshness remains 300 ms in every arm; the candidate additionally requires the last source-generation advance to be within 300 ms. Stalled generation never cancels active input. The unchanged 3075 ms owner deadline remains the backstop unless a trusted terminal receipt arrives.

## Frozen real-container result

| Condition | Complete | Primary | Late authority | Receipt delivery age at late submit, median [range] | Source-progress age, median [range] |
|---|---:|---|---:|---:|---:|
| Fresh false-running, timestamp freshness only | 3/3 | expired 3/3 | **admitted 3/3** | 56.013 [55.991, 56.131] ms | 2529.231 [2525.260, 2530.794] ms |
| Fresh false-running + source-generation gate | 3/3 | expired 3/3 | **rejected 3/3** | 55.959 [55.922, 56.043] ms | 2533.998 [2433.626, 2544.542] ms |
| Truly running + source-generation gate | 3/3 | expired 3/3 | **admitted 3/3** | 41.099 [38.659, 41.482] ms | 41.099 [38.659, 41.482] ms |
| True terminal + source-generation gate | 3/3 | cancelled 3/3 | **rejected 3/3** | 56.372 [56.156, 56.658] ms | n/a for authority decision; terminal latch dominates |

The false-running fault emits a new receipt at each 10 Hz evaluator acquisition but flips the delivered terminal bit to `running`; the off-policy evaluator still retains the actual `episode_finished=true`. Across those six sessions, the last delivery remains about 56 ms old at late submit while the engine episode tic has not advanced for roughly 2.4–2.5 seconds. Timestamp freshness therefore passes precisely when the underlying evidence is stale.

The source-generation arm rejects the same late submit 3/3 with `provider source generation stale`, while the active primary action still expires at its original owner deadline 3/3. It does **not** infer terminal from stalled progress. The false-running timestamp baseline admits late authority 3/3.

The true-running control advances source generation and admits late authority 3/3. Its source-progress age at late submit is only 41.099 ms median. The true-terminal control cancels primary input and refuses late authority 3/3; end-observed to verified empty is 1.148 ms median, range 0.644–1.153 ms. These are observed values, not hard-real-time guarantees.

## Integrity and negative evidence

- 12/12 case audits pass; every primary release independently verifies empty.
- Scorer missed periods total: 0.
- False-running sessions retain 164 injected false-running receipts in their acquisition logs; no real terminal receipt is delivered to the gate in those arms.
- Historical timeout `score.json` still falsely reports `map_exit=true` in all nine timeout cases; the independent final sample disagrees on `map_exit`. This separate scorer bug remains visible and uncorrected.
- No same-ID reruns. Preflight is excluded from the 12 measured cases.
- The gate never uses kill, health, ammo, or success classification to choose/cancel input.

## Environment

CPU: AMD EPYC 9V74 80-Core Processor; affinity [0, 1, 2, 3, 4]; clock frequency not pinned and shared-host contention unobserved. CPython 3.13.5, Linux 6.18.44 x86_64. ViZDoom 1.3.0/Freedoom MAP01, skill 1, ASYNC_SPECTATOR, private Xvfb/Openbox, visible 640x480 game. One fresh restored session per case; three restores/cell; zero model calls.

## H / T / D / C / U

**H.** Delivery freshness and source freshness are distinct. A meaningful source generation can fail closed on new authority when fresh receipts merely repeat stale state.

**T.** Fifteen deterministic gate tests, one excluded true-running preflight, then 12 source-frozen real X11 sessions (four conditions x three restores) with identical `[a,d]`, 5000 ms requested hold and 3075 ms owner deadline.

**D.** Scoped mechanism PASS: false-running timestamp-only counterexample 3/3; source-generation refusal 3/3; true-running availability 3/3; true-terminal cancellation/refusal 3/3. Retain as an optional dynamic-provider admission capability, not a shared-runtime/general GUI rule.

**C.** A source may legitimately be static while still usable. A faulty or malicious provider can forge monotonically increasing generations. Episode tic is provider-specific and evaluator refresh is an intervention. Availability depends on the 300 ms threshold.

**U.** One saved MAP01 neighborhood, one host, n=3/cell, provider-local source generation, no model/planner. This is not authentication, semantic termination, arbitrary-GUI liveness, gameplay efficacy, exactly-once behavior, or hard-real-time evidence.

## Generalization boundary / next question

This result strengthens a general interface rule: **acquisition time, delivery time, and source generation must be separate evidence fields.** But source-generation freshness is only valid for providers that expose a meaningful advancing generation. Static documents cannot be declared dead merely because their version does not change.

The next discriminator is adversarial/faulty provenance: if a provider can emit a fresh, increasing but fabricated generation, freshness and generation checks both fail. The next mechanism should therefore test an independently sourced or cryptographically/source-pinned provenance relation rather than tightening the 300 ms threshold.
