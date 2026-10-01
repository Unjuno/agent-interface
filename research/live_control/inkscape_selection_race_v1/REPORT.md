# Real Inkscape selection race after fresh revalidation

Decision: **FAIL_PREREG_FULL_GATE; RETAIN_CONDITIONAL_WRONG_TARGET_BOUNDARY.** Four of twenty first measured cases failed the frozen visible-selection revalidation and correctly emitted no effect input. Among the sixteen cases whose frozen revalidation precondition did hold, stable cases moved the intended object A in 8/8 and selection-switch cases misapplied the identical Right-key intent to object B in 8/8. This is negative/conditional boundary evidence, not a promoted runtime mechanism.

Scientific task identity is the immutable preregistration value `INKSCAPE-SELECTION-RACE-20260916-014` (SHA-256 `66dc4ce13ae4d2f6aafdf3eaf732720e8d95bd1b910b59cf751b425a30473fc5`). Issue #288 and the branch name mistakenly used suffix `015`; this report preserves that provenance mismatch instead of editing the preregistration after measurement.

Publication base: `b3465ae3c042ad4ff5c91155f991f3998c8d2557`. Scope: additive `research/live_control/inkscape_selection_race_v1/**`. No model/game calls.

## Question

After a fresh rendered observation verifies that red object A is current and visibly selected, does ordinary Inkscape reject a stale Right-key intent if selection changes to object B before the same OS input, or does it reinterpret the input in the new selection context?

The prior synthetic X11 experiment (#273 / merged PR #277) established that generic XTEST has no expected-version field. This block transfers that boundary to Inkscape 1.4 using an independently scored SVG effect.

## Frozen design

One SVG contains red rectangle A at x=50 and blue rectangle B at x=220. Each case starts a fresh private Xvfb/Openbox/Inkscape process. The controller uses only screenshots and XTEST. The independent scorer parses the saved SVG only after the action.

Both arms:

1. focus `two.svg`;
2. explicitly enter the Inkscape Select tool with F1;
3. click A;
4. capture a fresh screenshot;
5. require A's scoped pure-red target center to remain within ±5 px, B unchanged, and at least 20 dark pixels in each of four selection-handle zones;
6. wait approximately the same 120 ms revalidation-to-effect window;
7. emit five XTEST Right press/release pairs, then Ctrl+S;
8. verify empty physical keymap and independently parse A/B x positions from the saved SVG.

Only the window content differs:

- `stable`: no context change; a 120 ms sleep matches the other arm.
- `switch`: click B after successful revalidation; the click helper contains the same ~120 ms settle, then the identical Right-key effect is emitted.

Frozen schedule: ten repetitions per arm, shuffled once with `random.Random(27420260916)`, 20 first cases total. No measured case was retried or replaced.

Measured source SHA-256:

- `run_case.py`: `c4ebfb09165d111fd9c74c1e606b56a3728ec0e0ca4b5b002552a021271cb24d`
- `audit.py`: `a16f90d10a4aa389e0dc0010d6583f071fb8d1125c0a35b8ba40f4238fb8ba29`
- `prereg.json`: `66dc4ce13ae4d2f6aafdf3eaf732720e8d95bd1b910b59cf751b425a30473fc5`
- `environment.json`: `669cf9ab21705474bb1f4a771c498f4dbe7d62ede8dfdb6e12e0c7c98265651b`

Construction-only failures before freeze were retained locally: global color scanning included unrelated UI red after selection; one construction did not explicitly choose the Select tool; selection overlay expanded the apparent target bbox. Final construction switched to F1, scoped ROIs, visible-handle scoring, and matched delays and produced the expected A movement / B misapplication pair.

## First measured outcomes

| outcome | stable | switch |
|---|---:|---:|
| fresh visible-selection revalidation passed | 8/10 | 8/10 |
| revalidation failed; effect not started | 2/10 | 2/10 |
| among valid cases: intended A moved x=50→60 | **8/8** | 0/8 |
| among valid cases: B moved x=220→230 | 0/8 | **8/8** |
| application rejection after successful revalidation | 0/8 | **0/8** |
| final physical keymap empty in executed cases | 8/8 | 8/8 |

The four failed-precondition cases (`00-stable`, `06-stable`, `05-switch`, `06-switch`) retained the same A/B target geometry but had zero dark pixels in all four selection-handle zones. `run_case.py` raised before `effect_start_ns`, before save, and before any Right-key effect. These are fail-closed outcomes, not silently discarded trials.

The preregistered 20/20 revalidation gate therefore **fails**. The original frozen audit returns nonzero and is retained. A separate posthoc retention audit does not change that decision; it only verifies that all twenty first outcomes are internally reconstructible. It reports: 4 failed preconditions / 4 fail-closed; 16 valid cases; stable correct 8/8; switch wrong-target 8/8.

For valid cases only, revalidation-to-effect-start elapsed time was 120.135 ms median (120.113–120.155) stable and 120.524 ms median (120.464–120.597) switch. This matching is a causal control, not a performance comparison.

## Interpretation

**Fact:** when the visible-selection precondition was satisfied, changing Inkscape selection from A to B after revalidation caused the subsequent correctly delivered Right-key input to move B in every measured switch case. Inkscape did not reject stale semantic intent.

**Fact:** when the selection predicate was not visibly established, the frozen harness stopped before task input in all four cases.

**Inference:** a fresh screenshot/selection check narrows the race but cannot bind a subsequent generic key event to the object identity that was verified. The application interprets the event using its current selection at consumption time.

**Boundary:** this does not mean all ordinary GUI input is unsafe or all applications misapply stale intent. Some applications disable actions or naturally no-op after context changes. It does show that the universal OS-input path cannot assume application-level stale-intent rejection even in a mature desktop app.

## ERROR CHECK

The frozen prereg audit correctly fails because revalidation did not pass 20/20. The posthoc retention audit independently parses every saved SVG, checks all artifact SHA-256 values, verifies empty keymaps for executed effects, verifies that failed-precondition cases contain no effect start or saved result, and binds all 20 schedule identities. It returns `retention_pass=true` without changing `preregistered_full_gate_pass=false`.

Five post-measurement corruption controls are rejected: altered wrong-target SVG, fabricated effect start in a failed-precondition case, nonempty keymap, missing result, and corrupted artifact digest.

A compact retained evidence package contains all result JSONs, all independently scored saved SVGs, source/prereg/audit files, and the two distinct scoped revalidation crops needed to independently distinguish visible handles from missing handles. Full 1280x800 screenshots remain local-only; their SHA-256 values remain in the case records. The retained crop is the exact scope used by the selection/target predicates, so the declared local visual checks can be reproduced without claiming full-screen retention.

## H / T / D / C / U

**H:** Inkscape will reinterpret generic OS input against a new selection after final revalidation rather than preserving the planner's prior target identity.

**T:** 20 frozen fresh-process X11 cases, stable vs one post-revalidation selection switch; same action and matched wait. Zero model/game calls.

**D:** full prereg gate **FAILS** due 4/20 revalidation failures. Retain the conditional boundary: 8/8 valid switch cases wrong-target, 8/8 valid stable cases correct, four invalid-selection cases fail closed. No production promotion.

**C:** the four false/absent selection-handle observations may reflect asynchronous selection paint or click admission rather than actual selection failure. A bounded wait-for-visible-selection predicate could reduce these false stops without changing the stale-input boundary.

**U:** one Inkscape version (1.4), one synthetic SVG layout, one Linux/X11 host, explicit injected selection change, no planner/model, no Windows/macOS/accessibility path, no calibrated hard-real-time timing claim.

## Next single question

Hold the action, target, scorer and race unchanged. Change only the pre-effect readiness rule: fixed-time single selection snapshot versus a bounded temporal contract that waits for the same four-sided selection predicate. Measure false-stop reduction and added local observation cost. Do not combine that first follow-up with another stale-input guard.

## GitHub coordination incident

Before this measured branch was created, a `.placeholder` was mistakenly written to `main` in commit `3de4a4c6...` and immediately removed in `b3465ae3...`; the path is absent from the resulting main tree. Several subsequent create-file attempts against the nonexistent branch returned 404 and wrote nothing. This operational error is retained here rather than hidden.
