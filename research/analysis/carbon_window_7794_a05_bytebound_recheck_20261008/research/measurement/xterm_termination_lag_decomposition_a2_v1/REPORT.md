# #1563 XTerm termination-tail A2 retained stop

Decision: **STOP_FORMAL_ENVIRONMENT_INTERPRETER_MISSING_XLIB**. Scientific disposition: **NONE**.

The excluded four-session construction was eligible: correctness/marker/ROI integrity passed, effect-to-child-ready p95 was 19.687084 ms, and child-ready-to-native-XTerm-exit p50 was 264.240491 ms. These four sessions are construction only and are not a scientific result.

Source-first freeze and remote Git-blob readback passed. Parent #1346 source reconstructed byte-exact; the fresh A2 source archive is SHA-256 `87d56230057cde50b8a6bee9741ca7ed042d1a0c6e1bb084170d600c58521329`.

The single formal invocation then stopped before any GUI session or scientific row. The orchestration command selected `/usr/bin/python3`, where `python-xlib` is absent, while construction had used `/opt/pyvenv/bin/python3`, where Xlib is installed. Import failed at `from Xlib import ...`; case directories=0, scientific rows=0, residual Xvfb/Openbox/XTerm/planner processes=0. Formal invocation1 / reruns0.

No scientific threshold, source member or prior result was changed. Post-stop source rehash is8/8 exact. This TASK must not rerun. A legal successor changes only orchestration interpreter identity and uses a fresh TASK/seed; #1563 rows pooled0.
