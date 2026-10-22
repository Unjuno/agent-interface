# Post-sample cancellation publication composition v1

This package verifies whether the current owner repair preserves cancellation cause through the current executor event publisher for one forced interleaving.

H: cancellation is made visible immediately after the owner samples cancel=false and before it begins release I/O. The repaired owner should recheck after release I/O and record a cancelled release; ExecutorV12 should publish the receipt before terminal.

T: compose the real executor worker/cancel/publication path from PR #7429 at e22e59732033438916415f71b53f86695b1c448a with owner v12 / transition-owner v4 from PR #7440 at 99b7d130742b4e884709a862bc074d15e6b42ac9. Current main dependencies are vendored under dependencies/main. Use the line event at the first statement after the false cause sample to set executor cancellation. Compare with an uncancelled release control. Xlib and XTest are replaced with a deterministic fake keymap.

D: the forced cancellation passes only if owner release is verified empty and marked cancelled, exactly one lease-bound input_released is emitted before terminal(cancelled), and the event carries the same intent token and release record. The ordinary control must remain release/completed with no interruption/event. The raw-only audit must reject all three corruption controls.

C: the older PR #7440/#7429 heads reproduced lost cancellation cause and missing input_released. That prior raw pair remains preserved in the workspace history but is not the result packaged here. The current result tests the later owner recheck and executor barrier together.

U: deterministic forced schedule only; no natural race-frequency estimate. Fake Xlib is not physical input. No live game, application effect, useful feedback, bounded recovery, survival benefit, or MAP01 result is established. This package is not a full merge-tree check.

## Current-head result

The cancellation case passed 1/1: one fake key press and release; owner_release(reason=cancelled, verified=true, keys_down=[], buttons_down=[]); exactly one input_released event before terminal(status=cancelled); matching intent token and owner receipt. The ordinary release control passed 1/1: owner_release(reason=release, verified=true); terminal completed; no interruption or input_released. The independent raw audit reports PASS_SCOPED_REPRODUCTION with no errors and rejects all three mutated controls.

## Run

From repository root:

    python -B research/live_control/cancel_release_publication_59/late_cancel_composition_v1/test_postsample_composition.py
    python -B research/live_control/cancel_release_publication_59/late_cancel_composition_v1/test_ordinary_release_control.py
    python -B research/live_control/cancel_release_publication_59/late_cancel_composition_v1/audit_pair.py

All imported code sources are included under dependencies/ and pinned in SOURCE_MANIFEST.json.
