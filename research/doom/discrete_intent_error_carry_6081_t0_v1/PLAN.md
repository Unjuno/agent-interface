# Error-carry compilation of bounded directional intents — T0

## H / T / D / C / U

**H.** For nonrepresentable rational directions inside the legal action hull, finite-horizon error carry can reduce worst-prefix or terminal displacement error versus a fixed nearest legal action, at identical slot and occupancy bounds, without violating the frozen path envelope, switch cap, or final-release gate. Outside-hull intents must refuse. No direction of real-world benefit is assumed.

**T.** Enumerate the 10 fixed cases in `FIXTURE.json`: exact 4-way vector; shallow 4-way slope; near-axis duty; explicit 8-way diagonal; zero; reversed axes; one-slot deadline; 4-way intent outside its convex hull; calibration mismatch; and a held-out nonlinear collision/acceleration transfer control. Compare four policies: horizon-wide nearest legal action (A), independent per-slot nearest action (B), cumulative-error greedy schedule (C), and release/no-continuation (D). Calculate every exact rational prefix error, terminal error, switch count, box-envelope violation, refusal and final release. Candidate once, separate raw-only independent auditor once, retries 0.

**D.** `PASS_METHOD_SCOPED` only if: C has strictly lower worst-prefix squared error than both A and B on at least two preregistered reachable nonrepresentable linear cases; no increased frozen box-envelope violation or switch/deadline/release error; exact/zero controls remain correct; outside-hull and calibration-mismatch inputs refuse; nonlinear holdout is reported HOLD_TRANSFER, not tuned; independent oracle matches all outputs and rejects all mutation controls. Otherwise `FAIL_METHOD`, with precise first failed gate.

**C.** Source anchor main `6cd70ad4bfad74e11658057bf024918bffb24add`. T0 is exact synthetic geometry; no GUI/model/container allocation is necessary. Disposable container was preferred, but the shared Docker/OrbStack ownership/lifecycle remains unresolved in #5085/#626, so this isolated CPU-only run is host-side; no container was launched. The legal action tables explicitly include only fixture-calibrated vectors. In particular, 8-way diagonal displacement is stipulated, never inferred from cardinal inputs.

**U.** Idealized constant displacement only; no game/GUI physics, collision dynamics, actual key occupancy, input latency, focus or task-effect evidence. A geometric PASS cannot establish safe live paths or MAP01 progress. The nonlinear collision/acceleration row is a held-out transfer refusal/negative control, not part of tuning or the linear win count.

## Freeze and one-shot gate

Only `candidate.py` then `audit.py` may execute, exactly once each. Both use the frozen fixture. Candidate writes the deterministic raw JSON; auditor independently reconstructs from fixture and raw only. Preserve a failure/STOP; do not rerun either process.
