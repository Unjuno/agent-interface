# Stop optional observation after cancellation

Executor v8 and post_release_observation_v2 preserve the original focus/surface interruption while checking the lease's explicit cancellation Event before each optional sample. The 80ms pre-capture wait is interruptible. The existing interruption-aware lease.wait is intentionally not used: it would immediately throw the already-recorded focus cause and prevent all passive observation. No input permission or lease is created. Cancellation affects optional collection and is reported as post_release_observation.stopped; it does not rewrite the original terminal cause.

## Controlled stalls

results/post-release-stop-01 contains a pinned plan and ten synthetic live-thread runs: frozen v7 and candidate v8 across blocked capture/cancel, blocked output/cancel, stopped-notification/cancel, blocked capture/close and blocked output/close. Gates are released explicitly by the probe and have a three-second fail-safe. This models blocking boundaries, not actual X11 capture hangs or saturated OS pipes.

Both versions still have no terminal while the current synchronous operation is blocked. Close also remains pending at that point. V7 completes two captures even after explicit cancel/close. V8 completes only the already-started capture (one), or zero if cancellation preceded collection. After the test gate opens, v7 spends another roughly 80ms, or 160ms before collection, whereas v8 reaches terminal in 0.087–0.221ms in these synthetic cases. These are controlled worker timings, not model speed measurements. All cases retain needs_decision/focus_changed, release verification and zero completed steps without executing the tail.

This is a cooperative improvement, not preemption or a hard wall-clock bound. It does not fix blocked capture/output. Returning terminal early without controlling the lingering worker would create concurrency and resource-ownership questions; detached threads are not a solution by themselves.

## Persistent unrelated focus on actual X11

probe_bundle_focus_v4 runs the registered nine-step Inkscape bundle on seed 224, blocks output after Control_L admission, then moves focus to an unrelated private X11 window. Unlike the earlier probe, it keeps that foreign focus through passive collection and a fresh observation using the original deadline.

results/bundle-focus-04 passes: physical key down verified, physical release while output remained blocked, prefix three completed steps, no later input, needs_decision/focus_changed retained, two passive captures with no owned keys/buttons or active owner lease, foreign focus unchanged, fresh same-deadline observation completed without old cause. All four close calls returned. Release-record to terminal was 318.999ms including passive collection. audit_bundle_focus_v3 independently verifies source/step hashes, owner cause/admission order, the passive-only interval, foreign focus, and eleven exact PNG/AIT frames. No input was issued into the unrelated window.

This tests the shared backend with controlled X11 focus, not socket delivery, model decision quality, rollback or every focus transition. Existing defaults and measured sources/results remain unchanged.

## Next architecture decision

The live Calc benefit (fewer explicit observation programs) remains evidence for passive followup, but a capture must not become a prerequisite for learning that input stopped. Next compare immediate interruption delivery plus a separately bounded passive observation lifecycle against the current terminal-delayed path. Explicitly represent capture still running, finalization pending and cancellation; do not declare resource reuse safe until the active capture has ended. Validate transport backpressure separately. Model tokens/cost and human-speed comparisons remain open.
