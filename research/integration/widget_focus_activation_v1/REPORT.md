# #4036 — Existing X11 target-activation recipes for keyboard recovery

## Decision

**PASS_FOCUS_ACTIVATION_RECIPE_BOUNDARY_SCOPED**. One prospectively hash-frozen 30-case allocation completed in three immutable ten-case batches. No formal retry, replacement, pooling or post-freeze source change. The PASS supports a bounded integration finding; it does not qualify every tested recipe or the production runtime.

| Actual route | Stable A | B before activation | B after activation |
|---|---|---|---|
| Top-level focus | A receives 7: 3/3 | B receives 7: 3/3 | B receives 7: 3/3 |
| Native A child focus | A receives 7: 3/3 | B receives 7: 3/3 | B receives 7: 3/3 |
| Ordinary click on A | A receives 7: 3/3 | A receives 7: 3/3 | B receives 7: 3/3 |

Three no-input controls remain blank. Total: **12 correct A effects, 15 wrong B effects, 3 no-input controls**. These deliberately selected finite counts are not failure-rate estimates.

All nine native-child activations successfully returned and the independent X connection immediately observed the exact native A XID. Nonetheless, six of those sessions later entered text into B. In the three BEFORE cases, internal focus was B immediately after native activation and remained B. Therefore native-window focus success is not a reliable Tk-recipient repair certificate in this fixture.

All nine clicks were observed as one ordinary left press/release on A and restored Tk internal focus A at the post-activation snapshot. Six stable/before-change sessions then entered the intended text. A subsequent explicit application focus change invalidated all three after-activation sessions, which entered B. **RETAIN only the current-geometry/no-later-change click recipe as a scoped candidate; REJECT top-level or native-child focus alone as repair for this Tk state.** Do not install a production default from this evidence.

## Why this question

#55 separates in-window target validity from top-level surface/focus. #57/#2789 require useful bounded recovery, not an always-refuse checker or an endless wrapper-repair chain. The preceding conversation-local focus study established check limitations but did not try activation recipes. This study tests a different integration choice using existing backend primitives. It does not repeat the old 21 cases.

Old ZIP SHA256 b43733124b805ddb94e5fa77be1fe64190dd13531723a23cc901d8a8dca270f0 remains unchanged and conversation-hosted. Its full 266-file evidence is NOT claimed uploaded by this PR. No old result is altered or retroactively publicly preregistered.

## Executed path and assumptions

Provided Linux x86_64 execution container; CPython3.13.5; Tcl/Tk8.6.16; Python-Xlib0.15; private authenticated Xvfb,640x360x24,TCP disabled. No Docker/OrbStack CLI/image identity or image-attested replication. No model/provider, external-network experiment, installation, host display, user document or clipboard. XQueryKeymap is X-server logical state, not physical HID telemetry.

The full backend.py is the exact 15074-byte current-main Git blob 9cae101a219348077668c8fc086acf8e13154afe, SHA256 3429a422e61ecb8b1f1f278540d0696842d8197d7967803e01bc8d9453bcb4a8. The inherited loader removes only an unused core-manifest import. All executed backend methods are unchanged. The test uses its execute/preflight/focus/pointer/text/release paths, but NOT public CLI/MCP, core admission, a model or a production target guard. Backend code explicitly does not decide admission; this is not an allegation about an undocumented production guarantee.

Fresh ordinary Tk Entry A/B widgets start empty. Current A native identity/geometry is supplied by the cooperative app and checked through X11, not found by a general semantic locator. Fixture IPC can observe, focus B or close; it never inserts/deletes text or invokes widget bindings directly. Native digit7 events alone change content. Click uses exact current A-center geometry and ordinary stock Entry bindings. All routes use the same observation separation between activation and text, so this is not an atomic macro or a measured model-wait interval.

## H / T / D / C / U

H: native X focus and remembered toolkit recipient are distinct; ordinary click activation can repair an earlier internal focus change but cannot guarantee validity after another change.

T: three routes x three controlled schedules x three repetitions, plus three no-input controls; 30 fresh apps in three fixed ten-case batches with rotated route order.12s startup bound,3s RPC bound,38s supervised batch bound,42s enclosing tool request. Stop bounds, not performance claims. Excluded construction uses digit3. Actual external batch runner exits were0/0/0.

D: exact table above plus full source/event/effect/request/response/process/batch/hash closure. Formal raw-only audit reports30 cases and zero errors. Thirteen preformal tests pass, including12 semantic corruption variants; all12 variants also reject copied formal evidence. Ten frozen files remain exact. All30 app actual exits and three Xvfb actual exits are0, all final keymaps/buttons neutral, owned process/socket/auth cleanup verified. No safety claim inferred merely from release.

C: another toolkit/window manager may interpret native-child focus differently. Click geometry could become stale or occluded, change caret/selection or trigger collateral effects. Populated fields, disabled widgets, window reincarnation, layout/IME/lock changes are not tested. This study does not solve target acquisition or atomically bind activation to future input.

U: deterministic directed conditions and one toolkit/backend configuration. No natural race probability, model utility, actual token saving, latency benefit, hard real-time bound, cross-platform/general reliability or product claim. Same-author separately implemented auditor is not external review. No calibrated combined timing uncertainty or coverage factor is manufactured.

## Analytical consequence and unit check

The native-child BEFORE case has successful native activation and exact A XID readback, yet its ordinary text effect is in B. This is a concrete counterexample to the implication that native focus success alone establishes the desired Tk recipient. The click AFTER case has verified A activation followed by a later B change and B text, so activation-at-one-time is not a persistent authority claim. Both are existence statements within the measured setup, not population claims.

The PLAN includes the variable table. Counts and XIDs are dimensionless integers; coordinates retain pixel units with no metre interpretation. Timestamps are same-container monotonic integer nanoseconds; time differences retain time units. No cross-domain clocks or model-visible timing are compared. Integer text equality and event order, not a calibrated timing benchmark, decide the gates.

## Retained construction and publication chronology

- Construction01: startup response exceeded3s before input. The first constructor did not retain a direct app wait; XIO after server teardown is retained and missing exit is not inferred. Subsequent process inspection found no live owned actor.
- Construction02: incorrect equality between Tk frame() and the client's wrapper parent caused a pre-input STOP. Actual app exit0 retained. Corrected to client-parent-root ancestry plus observed initial native focus.
- Construction03: three excluded before-activation comparisons completed.
- Construction04: all nine excluded route/schedule conditions completed; separate raw-row audit had zero errors.
- Environment metadata lookup failed once because installed Xlib lacked package-distribution metadata; actual Xlib.__version__ was recorded before freeze.
- Source/gate hash commitment: FREEZE at commit dfd747fdeed3bcd41df65520f649761e878a6a74, readback blob b42dc6bd7e79a7a4305608f80f377b91f1b21976; exact decision table at0c087089e0a275cd59a667cc75b181ff289786c6, both before formal input. Full code/raw publication follows execution, explicitly not claimed earlier.
- Original frozen auditor passed on its first formal invocation. A tool-level TERM diagnostic appeared outside its JSON output; it is not an experiment failure or invented study stderr.

Freeze SHA256:3468b572d0210edd2dff512473c592dc4ac68bc4a57b07299ec77c88b64953e8.
Audit SHA256:fec7c91b44d7b47b70288da672eae588b21dbb6c82f59d4c1b3ca4eebd2395d8.

## Integration handoff / non-goals

Retain separate fields for OS-window activation, toolkit recipient evidence, actual input delivery, input release and final application effect. A current bounded click-to-focus recipe may be useful where exact target geometry and the no-later-change assumption are satisfied; bind and verify those conditions rather than silently equating a focus return with semantic input targeting. HCI, concurrency and API contract design are the relevant transfer domains. No new learned intermediary is needed for this measured mechanism.

Local roadmap through experiment/audit is complete. Evidence publication, exact-head CI/review, merge and main readback are separate delivery gates recorded in the PR. No repository-wide test PASS is asserted. #55's historical result, #57/#2789 and the global roadmap are not closed by this finite result. Construction/publication incidents remain in #4036, not new wrapper research tasks.
