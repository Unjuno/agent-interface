# MotorState Inkscape pointer-effect transfer — Issue #4219

Decision: **PASS_MOTOR_STATE_POINTER_EFFECT_GUARD_SCOPED**.

Three prospectively frozen six-case formal batches ran once each; reruns/replacements/tuning 0. Across 18 fresh private Xvfb/Openbox/Inkscape lifetimes, stable naive/guard produced the intended saved-SVG rectangle move 6/6. Directed external pointer displacement made the command-only comparator observe MISMATCH but still dispatch Button1 and fail the intended SVG effect 3/3. The observed guard refused those MISMATCH cases 3/3 before button-down. Observer-unavailable guard returned UNKNOWN and refused 3/3. Candidate wrong effects: 0.

All 12 dispatched cases observed Button1 held and all 18 cases ended neutral. Inkscape teardown is expected SIGTERM (-15) after final observations; Openbox and Xvfb exits are 0 in 18/18. Saved SVG bytes/geometry are scorer-only and never authorize input. Authority remains none.

Independent raw audit reconstructs 18/18 with errors=[]; 10/10 coherent evidence corruptions reject. Formal RAW SHA256: rep0 106a59c3f89242bd3d8b1825337cde48d317eee5ab6248e5ba16ef8d0b969625; rep1 16c1a5e415f588883eafad335609b9f1cd933a8ccd89abcd93927aa69a9170b3; rep2 6901b4733effa61db0e150fb9814969db51f2e078c4a7bf28f24a5cd03bd2557.

Scope: one fixed red-rectangle Inkscape/X11 fixture. X-server state is not physical HID telemetry. No model/planner usefulness, screenshot/token/latency benefit, natural displacement rate, arbitrary document, second pointer app, cross-platform/runtime/product claim.
