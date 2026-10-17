# A11 preregistration - exact-main owner close on isolated Xvfb

H: V4->V3->V12 admits a key to a focused Xvfb client; close generates matching KeyRelease, observer key-up, verified terminal close receipt and stopped owner thread.

T: One `a` key on display :133, then wrapper close; retain X events, keymap, owner records and thread state.

D: PASS_METHOD_SCOPED if exact-source freeze and raw-only audit pass. Setup/incomplete trace STOP; complete mismatch FAIL. One candidate; one auditor if RAW exists.

C/U: Synthetic X server only. No physical key state, app consumption, useful feedback, task effect, threat response, recovery or MAP01 completion.

Base main `f185a9059d485a4f8d5a65e9e7f6782897f67eae`; A10 remains unchanged.
