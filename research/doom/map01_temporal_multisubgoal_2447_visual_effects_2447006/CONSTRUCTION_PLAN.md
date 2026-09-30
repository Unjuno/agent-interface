# Issue #2447 — visual-effect evidence construction v2

Status: new construction-only allocation; distinct seed from the retained 2447005 case. No formal rows authorized or consumed.

## H/T/D/C/U

- **H:** If the runner saves one exact screen image at each fresh-observation-bound input handoff and another immediately after release/engine sampling, an independent audit can evaluate each Right/Left subgoal using only controller-visible pixels instead of relying on scorer yaw.
- **T:** One fresh Linux Docker/Xvfb/Openbox MAP01 episode, seed `2447006`, drop class, temporal gate, requested setup heading `110°`, followed by the inherited Right 190ms and Left 190ms bounded subgoals. Add only before-action and after-action image retention to a distinct copied runner; preserve all inherited phase detector, InputOwner, setup, capture roles and action durations. Audit both image pairs with the frozen LK feature-flow implementation and verify image hashes, action/release ordering and empty release. One invocation only.
- **D:** Construction instrumentation PASS requires all four paired images to exist; pre-action hashes equal the exact fresh handoff receipts; each pair is monotonically ordered around the corresponding action/release; independent LK recomputes for both pairs with valid track count >=80; no run/runtime/release errors; all releases empty. Any missing pair, LK UNKNOWN, ordering defect or release failure is retained as STOP/HOLD, no retry. This does not establish correct subgoal semantics or Issue #2447 efficacy.
- **C:** Docker Desktop Linux/amd64 pinned image; network none; source/evidence read-only except fresh evidence output; one no-monster temporal-arm sequence; same bounded UI route; no model. The fixed-seed single case is construction-only and is not pooled with the prior case.
- **U:** Does not compare endpoint/temporal/fail-closed gates; does not inject stale/ambiguous/missing, delayed/dropped frames, false/repeated completion, wrong-direction, focus-loss, timeout or restart; no held-out transfer, recovery-rate or cumulative completion estimate; scorer-only state remains corroborative, not controller evidence; no formal acceptance.

## Frozen case

ID `issue2447-visual-effects-construction-2447006`; seed `2447006`; class `drop`; temporal gate; requested heading `110°`; source fixture from the retained offline source bundle. The frozen command, exact copied source hashes, Docker image identity, plan hash, and schedule hash are recorded in `FROZEN.json` before the only run. If that record is incomplete, do not start the game.
