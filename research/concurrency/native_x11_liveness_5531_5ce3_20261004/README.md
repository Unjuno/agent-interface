# Native liveness boundary — Issue #5531 N01

This additive package extends existing synthetic #5531 evidence to a private native Xvfb read. It is not a new failure detector or deployment qualification. PLAN.json and prospective Issue comment 5971454566 define H/T/D/C/U and 12 formal cells.

All operations target fresh owned fixture servers. READY precedes GO; a controller-confirmed GrabServer blocks another connection's GetInputFocus. Delayed healthy and killed workers have distinct complete transcripts (pipe EOF / waitpid may distinguish them). The claim concerns timeout alone, not indistinguishability of all available OS signals. The invalid-response cohort deliberately corrupts only the emitted focus field after a genuine native read; it is not a native API defect.

Construction policy RED: six assertions failed against UNIMPLEMENTED before implementation; construction.json preserves that receipt. Synthetic test_auditor fixtures only test saved schema predicates; they are never experimental rows. Preflight is excluded from formal evidence. The observed scheduled 30ms checkpoint can overshoot because this VM shares the host; actual monotonic checkpoints are retained. Fast/invalid native query finishing after nominal GO+30ms yields HOLD_CLOCK_BOUNDARY even if stdout is available at a later actual checkpoint. No hard clock guarantee.

Source/image freeze precedes one candidate and one saved-raw auditor. run_stage.py x-creates stage outputs and checks hashes; do not remove outputs or rerun stages. A formal failure must remain first failure, with any saved audit correction separately labeled. Worker stdout identity joins parent PID/start ticks/nonce, but this trace is owned instrumentation, not independent adversarial source authentication. Candidate never emits keyboard/pointer actions or dispatch authority. Initial fixture focus setup and cleanup are explicit.

Local tests: `python3 -B -m unittest test_policy test_auditor`. Native stages require the already-owned OrbStack VM/image from PLAN.json: `python3 -B run_stage.py preflight`, `tests`, then frozen `candidate`, `auditor`. These are destructive to no user/server state beyond newly owned fixture processes. Never run them against shared desktop/server resources.

Cleanup observes the full keymap and Button1–3 masks only; it does not claim Button4+ neutrality. Report metrics apply to the saved cohort only, not model usefulness, input admission, recovery task effects, production health, or the complete roadmap.
