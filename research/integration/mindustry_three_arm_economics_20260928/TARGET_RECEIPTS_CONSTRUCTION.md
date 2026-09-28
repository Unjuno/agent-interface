# Target-specific receipt construction — local synthetic boundary experiment

Date: 2026-09-28 JST. Issue: [#5130](https://github.com/Unjuno/agent-interface/issues/5130).

## H / T / D / C / U

- **H:** Given a source-bound two-point locator and retained pixel evidence, the palette and world builders produce specs accepted by the unchanged receipt admission evaluator. A changed dependency, missing frame, authority-bearing locator, or evidence after the decision boundary must fail closed with no point authority. Building these specs makes no additional model call.
- **T:** Freeze the builder and test fixtures in this additive package. Use two deterministic 128×96 RGB frames: source frame SHA-256 `794071134358dff4c521137710f6555e2e3679b423be59e70ce7db0d6e26053f`; post-selection frame SHA-256 `0cf3d9747eb03f85e147dd09d9a9d018dc569ad340c4d44eb9c6a0a7181ed647`. Sequences are source 1, post-selection 2, fresh decision 3, and post-decision admission 4. Run the eight-case unittest construction suite and the existing no-GUI evaluator probe on the Windows host. No container, game, model, socket, or task input is part of this construction rung.
- **D:** PASS this construction rung only if both positive specs revalidate to their exact source points, all four negative evidence/authority controls return `NO_TARGET_AUTHORITY` and null point, the existing click compiler accepts the generated receipt at the same fresh sequence, and all tests pass. Any live/economic disposition remains unscored.
- **C:** Source/selection images, focus/surface/geometry, dependency boxes, model source sequence, decision sequence, and evaluator are fixed; controls change one dependency or evidence-availability/authority condition at a time.
- **U:** Synthetic RGB patches establish receipt shape and fail-closed integration with the existing evaluator only. They do not establish that a Mindustry palette icon, selected-tool marker, or world cue is semantically adequate; do not claim live click admission, task correctness, three-arm economics, or formal #5130 success.

## Executed result

Local command, from the repository root:

```powershell
python -m unittest discover -s research/integration/mindustry_three_arm_economics_20260928 -p test_target_receipts.py -v
python -m unittest discover -s research/integration/mindustry_three_arm_economics_20260928 -p 'test_*.py'
python research/live_control/probe_integrated_efficiency_protocol_v1.py
python research/live_control/probe_receipt_target_admission_v1.py
git diff --check
```

Final outcome: target-receipt construction **8/8 PASS**; full package **60/60 PASS**; inherited efficiency probe `passed=true`, positive `RETAIN`, 10 controls; existing no-GUI receipt probe passed; whitespace check clean. Cases include positive palette/world revalidation and click-envelope compilation, changed world context, changed selected-state mask, missing history, authority/sequence mismatch, required world dependencies, and strict changed-pixel typing. The receipt evaluator and its no-GUI probe are upstream Issue #55 code and were not modified.

The first target-suite invocation produced 6/7: only the test's regex expected `pre-decision`, while the builder correctly raised `exact dependency must predate the decision boundary`. The assertion text was corrected; the complete target suite then passed 8/8. This was a construction-test expectation defect, not an evaluator refusal or research failure; it is retained here rather than erased.

Source refresh: current `origin/main` is `5ad5a9ab465e2b0052aa301b1909b92816e70025`. A path-scoped `git diff --name-status 15bab5980e2bb0e48472e29144e21d25dbd337c1 origin/main -- <eight frozen/reused dependencies>` returned no changes. The exact blob IDs remain in [SOURCE_IDENTITY_AUDIT.md](SOURCE_IDENTITY_AUDIT.md). The branch was merged with current main before this construction edit.

Independent check: each generated spec passes the pre-existing `receipt_target_admission_v1.validate`, then the unchanged `evaluate` processes retained `PIL.Image` frames and returns either the expected source point or an explicit no-authority refusal. The separate no-GUI probe rechecks positive, pixel-change, freshness, binding, and missing-history controls. This is an independent evaluator-level check, not a standalone raw-run auditor; that broader #5130 gap remains open.

No Docker command was run in this rung. Although Docker Desktop reports Engine 29.8.0, #5130 explicitly bars start/build/pull/inspect/alter until a named coordinator assignment and sibling-container release are recorded. The current #5085 arbitration is still unresolved, so this local host construction does not bypass that gate. No GitHub Actions/workflow result was used.
