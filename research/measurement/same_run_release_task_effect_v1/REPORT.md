# Same-run release + TASK_EFFECT endpoint — Issue #4134

Disposition: **PASS_SAME_RUN_RELEASE_TASK_EFFECT_ENDPOINT_SCOPED**.

The prospectively frozen formal command ran exactly once after GitHub readback of the source capsule and all eight source hashes. It completed 12/12 fresh sessions with process exit 0: PRESS_EFFECT, RELEASE_EFFECT, STATE_ONLY and BACKGROUND_EFFECT each had 3 cases.

Every case retained exactly one plan/actuation/key-bound `key_released` receipt after XTEST KeyRelease + XSync, and every terminal X-server key observation was neutral. PRESS_EFFECT 3/3 and RELEASE_EFFECT 3/3 produced one independently journal-bound TASK_EFFECT each. STATE_ONLY 3/3 and BACKGROUND_EFFECT 3/3 remained `UNRESOLVED_NO_TASK_EFFECT`. Authority remained `none`.

Independent raw-only audit: 12 cases, errors=[]; 10/10 coherent semantic/provenance corruptions rejected. Formal reruns/replacements/tuning: 0/0/0.

Construction remains excluded and unchanged: construction-01 STOP_SETUP_XAUTHORITY; construction-02 missing Tk internal focus callbacks; construction-03 eligible after fixture `focus_force()` before ready.

Scope: one cooperative private Xvfb/Tk single-actuation fixture on one host monotonic clock. This closes the same-run measurement endpoint required by #1866 at this fixture scope only; it does not itself authorize MAP01 recovery efficacy, establish physical HID timing, model-visible useful feedback, token/latency benefit, human tempo, cross-platform behavior or production promotion.
