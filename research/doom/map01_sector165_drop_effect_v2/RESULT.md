# MAP01 sector165 pixel-only drop-effect predicate v2

Decision: **PASS_PIXEL_DROP_EFFECT_SCOPED / PASS_AUDIT**.

V1 retained its first formal case and stopped as `HARNESS_FAIL_STALE_SCORER_READBACK`: the separately launched X11 controller observed the expected pixel effect, but the parent ViZDoom evaluator was read without a refresh and therefore returned stale hidden pose. V1 case-00 was not retried and the remaining seven cases were not run.

V2 changes only scorer-side evaluator refresh after the controller returns. The X11 pixel controller, LK relation, threshold, action program, setup boundary definitions, and PASS/HOLD/FAIL gates are unchanged. Fresh seeds 993200..993203 were used.

Formal V2: 8 first sessions, four lower-floor drop fixtures and four matched one-sided-wall controls. Every controller receives only current X11 pixels plus focus/surface/geometry and executes the identical `use 80 ms -> forward 450 ms -> settle 350 ms` program. Hidden pose/topology are setup/evaluator-only.

Independent audit result:
- drop fixtures: 4/4 hidden sector165/Z-64 -> sector38/Z-128 and 4/4 pixel `DROP_COMPLETED`;
- wall controls: 4/4 remain sector165/Z-64 and 0/4 pixel false positives;
- valid LK tracks: min 118, max 352, all above frozen minimum 80;
- drop median vertical flow: -50.932 to -55.283 px;
- wall median vertical flow: -0.849 to -0.877 px;
- controller release failures: 0/8; setup release failures: 0/8;
- model calls: 0.

The frozen pixel predicate is `DROP_COMPLETED` iff median vertical LK displacement <= -20 px with >=80 valid tracks in ROI `[x=20:620,y=20:300]`. The auditor recomputes this from retained PNG bytes without importing the controller.

Interpretation is deliberately narrow. This establishes a public-screen effect sensor for one MAP01 lower-level transition against a matched blocked-forward control. It does not expose sector IDs to the controller, prove general drop detection, solve navigation, justify a generic optical-flow threshold, show combat benefit, or establish MAP01 clear/model benefit. The next rung may use this pixel effect as a subgoal/termination condition while keeping hidden topology evaluator-only.
