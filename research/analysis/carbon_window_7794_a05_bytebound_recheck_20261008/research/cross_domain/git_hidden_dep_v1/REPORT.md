# Hidden dependency completeness boundary for delayed Git effects

Decision: **RETAIN the dependency-completeness requirement** and retain the complete two-path guard only at this authored fixture.

## Question
The preceding rung showed that a declared dependency path avoids whole-tree false rejects. This rung deliberately omits one dependency to test whether a narrow validity predicate fails closed or becomes unsound.

## Frozen design
Real local Git 2.47.3, forty fresh repositories: `declared_only` versus `complete_two_path` across stable, declared-dependency change, omitted-hidden-dependency change, and unrelated change; five first outcomes per cell. Freeze commit `1c3486605e21c77bd5aa759dcf7b88ab84cb7962` precedes measurement. Both policies finish with current-OID Git CAS; only dependency coverage differs.

## Results
- declared-only / stable: 5/5 correct accept.
- declared-only / declared dependency changed: 5/5 correct reject.
- declared-only / unrelated changed: 5/5 correct accept.
- declared-only / **hidden dependency changed: 0/5 correct; stale B accepted 5/5**.
- complete two-path / stable: 5/5 accept.
- complete two-path / unrelated: 5/5 accept.
- complete two-path / declared changed: 5/5 reject.
- complete two-path / hidden changed: 5/5 reject.

Complete candidate: **20/20 ground-truth correct**. All40 cases pass independent integrity audit. No measured ID was rerun.

## Interpretation
Dependency-scoped revalidation is not intrinsically safe. Its soundness depends on the declared dependency set being complete for the consequential effect. Omitting a real dependency can transform a useful availability optimization into a stale write. Current-OID CAS still protects only the identity checked; it cannot compensate for a predicate that omitted relevant state.

This suggests a fail-closed interface rule: dependency-scoped continuation/promotion is eligible only when dependency provenance is explicit and complete enough for the effect owner; otherwise use a broader predicate or yield. This experiment does not discover dependencies automatically.

## H/T/D/C/U
H: incomplete dependency declarations are unsound; complete declared coverage restores correctness in the fixture. T: frozen40-case Git matrix plus postcheck race regression. D: complete20/20 correct; declared-only hidden-change stale accepts5/5. C: hidden dependency is authored, so the result proves the completeness requirement but not practical discovery. U: one Git build/host/ref and two paths; no GUI/model/network/power-loss, automatic dependency inference or hidden-state coverage claim.
