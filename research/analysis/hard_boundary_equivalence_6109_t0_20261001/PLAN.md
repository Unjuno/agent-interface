# Issue #6109 T0 — hard-boundary-preserving approximate route equivalence

## Scope

Finite authored path sets only. We compare exact whole-path set equivalence (hiding declared acyclic `tau` edges) with approximate whole-path matching under per-field, same-unit bounds and task-predicate margin guards. This implementation is not a general weak-bisimulation model checker. Possible divergence is a marked visible branch and cannot be hidden as `tau`.

The cited Girard–Pappas work defines approximate relations using bounded observation distance for specified metric transition systems/continuous-system classes; its assumptions do not establish GUI semantics. The T0 keeps target identity, authority generation, semantic outcome, effect lineage, release state and UNKNOWN as exact categorical labels. Coordinate (`px`), timing (`ms`) and feature-score bounds are independent; they are never summed across units. A task predicate `x < threshold` is robustly comparable only when the full declared per-route epsilon margin stays on the same side for every matched continuation.

## H / T / D / C / U

- **H:** On the frozen finite corpus, approximate matching accepts a benign coordinate/timing perturbation rejected by exact equivalence, while preserving hard labels, every possible branch, and task-predicate margins. Missing referent evidence, bounds, or compatible units yields HOLD.
- **T:** Fifteen authored cases include exact match; hidden tau refactoring; benign redraw/timing; independent-map alpha-renaming; extra possible-divergence branch; same pixels with a distinct incarnation; non-injective receipt alias; stale generation; effect-lineage, release, and UNKNOWN mutations; threshold crossing; unmapped identity; incomparable units; and missing soft bound. Candidate checks whole path sets; the independent auditor recursively checks continuations. Final candidate once and auditor once; no model/GUI/runtime.
- **D:** `METHOD_PASS_SCOPED` iff all expected case dispositions are independently reconstructed, the benign perturbation is the only accepted non-exact metric case, all hard and branch mutations reject, threshold-crossing uncertainty rejects, and unit/bound defects HOLD. Any false hard acceptance or missed possible branch is FAIL. This cannot certify a GUI route or live safety.
- **C:** Exact tau-hidden bisimulation with typed normalization plus separately reported numeric robustness may be simpler; route-level approximate metric may add no useful decisions beyond interval margins.
- **U:** Authored units, tolerances, referent maps, observation coverage, task predicate, event alphabet, tau abstraction and branch set are stipulated. No empirical calibration, actual app effect, action authority, live safety, timing benefit or human equivalence is tested. No arbitrary graph cycles, probabilities, or unmarked divergence semantics are modeled.

## Primary-source boundary

Girard & Pappas (2007), [“Approximation Metrics for Discrete and Continuous Systems”](https://doi.org/10.1109/TAC.2007.895849), develops approximate language inclusion/simulation/bisimulation and a hierarchy of approximation pseudometrics for specified metric transition systems; the paper's compositional result has operator assumptions. Girard & Pappas (2007), [“Approximate bisimulation relations for constrained linear systems”](https://doi.org/10.1016/j.automatica.2007.01.019), defines bounded observation precision for a stated class of constrained continuous linear systems. Neither supplies a GUI observation metric or task/effect oracle.

## Freeze and execution

Source base: `f590fde44595a70eb1752a4940fbc3f119b80a66`. Additive path only. Construction checks precede freeze. Docker Desktop UI processes were running but `com.docker.service` was Stopped/Manual, the `desktop-linux` Engine did not answer bounded queries, and the `docker-desktop` WSL distribution was Stopped; active-container inventory/ownership could not be confirmed. No shared backend restart. The finite fallback is host CPython with no container-isolation claim. No network/model/GUI/app/game/GPU/physical-input operations in candidate or auditor.
