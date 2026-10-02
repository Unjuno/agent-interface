# Ideas and outcomes

This is a concise, Issue-centered index of ideas proposed in `Unjuno/agent-interface` and what happened to them. Issues remain the place to submit and discuss new ideas; this page does not replace or close them. Closed issues are included where useful. An Issue's closed state alone does not mean its hypothesis passed or failed.

This index complements, rather than duplicates, the [durable design-theses ledger](design-theses.md) and the detailed [research evidence ledger](../RESEARCH.md). The linked Issue, PR, and retained report remain authoritative for full scope and evidence.

## Status key

- **Proposed / open:** no result is implied.
- **Scoped result:** evidence supports only the stated fixture, method, and assumptions.
- **HOLD / STOP / FAIL:** preserve the recorded outcome; do not reinterpret it as a pass.
- **Closed, unresolved:** workflow is closed, but the question was unanswered or continued elsewhere.

## Durable idea clusters

| Idea | Proposal | Current understanding |
|---|---|---|
| Interface bottleneck | With the planner held fixed, reduce redundant observations, model boundaries, serialization, waiting, recovery, and relearning without weakening correctness. | Core thesis. Issue [#57](https://github.com/Unjuno/agent-interface/issues/57) retains integrated efficiency questions. The [public six-task comparison](../runtime/results/public-six-task-comparison-04/README.md) preserves exact task outcomes, but overall efficiency and useful-feedback claims remain HOLD. |
| Rich planner + bounded local refinement | Keep intent and strategy with the rich model; local deterministic loops handle frequent refinement, verification, invalidation, and recovery, yielding on stale, ambiguous, or novel evidence. | Reflected in current architecture and several component studies. End-to-end useful outcomes and human-tempo generality remain unproven; see the [current handoff](LOCAL_RESEARCH_HANDOFF.md). |
| Universal fallback | Keep generic observation and input available; specialized application routes are optimizers, not prerequisites. | Durable architecture principle; broad cross-application promotion remains unproven. |
| Compact control with semantic equivalence | Compress model-boundary control while resolving it to the same validated semantics and preserving capability, freshness, lease, release, and verification guards. | Portable C1 has scoped evidence. Broader C0–C5 claims remain a separate research ladder; see [control codec](control-codec.md). |
| Observation gating + control codec | Reduce unnecessary observations and compact action representation as complementary optimizations, evaluated at equal correctness. | Both are retained design directions; no universal efficiency claim follows from design alone. |
| Local deterministic control | Keep frequent input delivery, update detection, verification, release, bounded recovery, and fine motor correction local when semantic reasoning is unnecessary. | Component/method results exist; integrated real-time control and useful task outcomes remain bounded by current handoff evidence. |
| Layered invalidation | Meanings, bindings, preconditions, routes, caches, and motor calibration go stale at different rates; invalidate only the narrowest stale layer. | Durable thesis with scoped evidence; broad live-app validity remains unresolved. |
| Pending effects + bounded authority | Treat unresolved effects as dependencies; allow independent work only with complete nonconflicting footprints. Bound physical authority with finite leases and fresh observable guards. | Issue [#6156](https://github.com/Unjuno/agent-interface/issues/6156) exhaustively passed within its finite escrow model; skew/crash stranded rights and a heartbeat-only reclaim counterexample violated the budget. Not a live distributed-system claim. |
| Scoped, renewable visual invalidation | Ignore irrelevant whole-frame motion while periodically revalidating ROI identity. | Only bounded fixture evidence; no general GUI guarantee. |
| Evidence and benchmark integrity | Preserve first outcomes and counterexamples; distinguish proxies from measured token/byte/performance claims; avoid tuning on hidden outcomes then calling them preregistered. | Embedded in the research method and evidence ledger. Issue [#6081](https://github.com/Unjuno/agent-interface/issues/6081) has a method-scoped exact-rational result, not live GUI/game evidence. |

## Recent open ideas

| Issue | Idea | Status / boundary |
|---|---|---|
| [#6358](https://github.com/Unjuno/agent-interface/issues/6358) | Shared recovery advice may become invalid when many recipients adopt it; retry/backoff interactions are related. | Open, explicitly unverified transfer question. No harmful advice or overload finding in this runtime. |
| [#6354](https://github.com/Unjuno/agent-interface/issues/6354) | Whether explicit role identity lets an online low-rank adapter learn a conflicting second role while preserving the first. | Open successor after earlier allocation/provenance STOPs. A three-seed synthetic RTX 3080/WSLc test is proposed; this entry records no GPU result. |
| [#6347](https://github.com/Unjuno/agent-interface/issues/6347) | Whether shared GUI arbitration creates an infrastructure-speed race between equally authorized conflicting intents. | Open, unverified analogy; no live scheduler finding or literal auction proposal. |
| [#6351](https://github.com/Unjuno/agent-interface/issues/6351) | Whether different roles attach different meanings to shared interface evidence about the same artifact. | Open, unverified transfer idea; no existing defect asserted. |
| [#6331](https://github.com/Unjuno/agent-interface/issues/6331) | Whether host suspend can let leases outlive intended deadlines across clock semantics. | Open successor; no suspend/resume trial or production defect claimed. |
| [#6350](https://github.com/Unjuno/agent-interface/issues/6350) | Distinguish verified non-application, unknown effect, and terminal task completion truthfully. | Open successor to a retained STOP; finite audit repair only, not a model/GUI experiment. |
| [#6342](https://github.com/Unjuno/agent-interface/issues/6342) | Whether presentation of a mandatory safety stop affects reactance or safe recovery choices. | Open, unverified HCI transfer idea; no proposal to weaken the stop and no participant study claimed. |
| [#6338](https://github.com/Unjuno/agent-interface/issues/6338) | Whether agent-request interruptions can amplify into self-exciting notification chains. | Open, unverified transfer idea; no current cascade or human-attention benefit claimed. |
| [#6327](https://github.com/Unjuno/agent-interface/issues/6327) | Evaluate an agent against a counterparty UI that changes its responses to observed interaction prefixes. | Open evaluation proposal; no live vulnerability or defense result claimed. |
| [#6310](https://github.com/Unjuno/agent-interface/issues/6310) | Define when silence supports a no-change GUI claim relative to a predicate and in-flight events. | Open contract/evaluation idea; no current event-loss defect or quiescence proof claimed. |
| [#5156](https://github.com/Unjuno/agent-interface/issues/5156) | Measure an owner-thread key-release/XSync interval inside the caller bracket without changing input authority or behavior. | Open; this is server-processing evidence, not physical or application-consumption time. Coordination Issue [#6360](https://github.com/Unjuno/agent-interface/issues/6360) reports successor-package/source mismatches and requests a fresh isolated window; it authorizes no run. |

## Closed ideas and successor lineage

Closure does not erase evidence. [#6353](https://github.com/Unjuno/agent-interface/issues/6353) closed as a duplicate of [#2031](https://github.com/Unjuno/agent-interface/issues/2031): its final collision audit found no distinct falsifiable remainder beyond #2031's truth-independent proposer, serialization, and localization work. No separate #6353 experiment ran. Preserve [#1968](https://github.com/Unjuno/agent-interface/issues/1968)'s `HOLD_NO_FORMAL_CONTAINER`; a separate [later scoped report](../research/analysis/serialized_attention_duplicate_label_successor_1968_v1/REPORT.md) found exact reconstruction and smaller serialized packages on a tiny fixture, but used truth-derived crops and makes no automatic-attention, model, or GUI claim.

- [#6319](https://github.com/Unjuno/agent-interface/issues/6319) closed after an allocation/seed collision before candidate execution: terminal pre-candidate STOP (candidate 0, auditor 0, retries 0), not a scientific pass or a falsification of six-worker memory sharing. Successor [#6329](https://github.com/Unjuno/agent-interface/issues/6329) also records a pre-candidate STOP after runtime/source admission mismatch. Neither is GPU experiment evidence.
- [#6324](https://github.com/Unjuno/agent-interface/issues/6324) closed as not planned: repeating #6296 with the same seeds/protocol would add no independent result. WSLc CPU construction prep passed 5/5 as environment preflight only; no CUDA/scientific experiment ran under #6324.

| Issue / evidence | Idea and outcome |
|---|---|
| [#6284](https://github.com/Unjuno/agent-interface/issues/6284) / [PR #6295](https://github.com/Unjuno/agent-interface/pull/6295) | Test cross-handoff duplicate correction demand under pending GUI effects. On seven synthetic histories, #24 retry identity + #5817 obligation/footprint accounting subsumed the extra mechanism: `H_FAIL_SCOPED / SUBSUMED_BY_24_5817`. No real-world or production-safety claim. |
| [#4155](https://github.com/Unjuno/agent-interface/issues/4155) / [PR #4169](https://github.com/Unjuno/agent-interface/pull/4169) | Test typed diagnosis before bounded recovery. `FAIL_DIAGNOSIS_LAYER_UNNECESSARY` on 324 cases: equal final dispositions and zero errors in both deterministic arms. Other learned, partial-observation, and transfer settings remain open. |
| [#4217](https://github.com/Unjuno/agent-interface/issues/4217) / [PR #4225](https://github.com/Unjuno/agent-interface/pull/4225) | Reuse semantic predicates only while declared evidence dependencies/generations remain valid. `PASS_DEPENDENCY_SCOPED_PREDICATE_CACHE_SCOPED` on 13 states × 4 predicates: evaluator calls 52→26, zero predicate/graph mismatches, independent audit passed. Authored deterministic trace only. |
| [#5521](https://github.com/Unjuno/agent-interface/issues/5521) / [PR #5762](https://github.com/Unjuno/agent-interface/pull/5762) | Reversible suppression of novel action proposals until qualifying fresh evidence. Finite-FSM test passed 35 rows across restart/state hashes; clear-on-expiry used 6 checks/4 effects vs tombstone 5/3, with both corruption controls rejected. No semantic-fingerprint or production-safety claim. |
| [#1871](https://github.com/Unjuno/agent-interface/issues/1871) → [#1884](https://github.com/Unjuno/agent-interface/issues/1884) / [PR #1896](https://github.com/Unjuno/agent-interface/pull/1896) | Preserve strict order while batching planner-visible interrupts after arbitration. #1871/#1876 initial allocations remain immutable STOPs; successor #1884 earned `PASS_ORDERED_INTERRUPT_BATCHING_A3_SCOPED` on 299,593 finite sequences, with zero sequence/identity/session-projection errors and 5/5 malformed controls rejected. Representation only; no model/token/latency/task-success claim. |

## Recent validation proposals (not results)

- [#6355](https://github.com/Unjuno/agent-interface/issues/6355) proposes an independent audit of the retained WSLc memory-cap failure from #6309. The predecessor's scoped failure remains unchanged. A multi-mount preflight failed and a no-mount smoke passed; a fresh mount-only preflight is the next gate. No formal audit outcome is recorded here. A pass would audit receipts, not actual cgroup enforcement or memory relief.

## Sources of truth

- [Design Theses and Idea Ledger](design-theses.md) — durable idea/thesis summaries.
- [RESEARCH.md](../RESEARCH.md) — evidence ledger and detailed results.
- [CURRENT_GOAL.md](CURRENT_GOAL.md) and [ROADMAP.md](../ROADMAP.md) — current direction and roadmap, not result ledgers.

This is an initial high-level index, not an exhaustive retrospective of every issue. Add or revise concise idea/outcome entries as they become relevant; keep full raw logs and detailed claims in the linked Issues, PRs, and reports.