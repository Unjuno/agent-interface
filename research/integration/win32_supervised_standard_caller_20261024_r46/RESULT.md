# R46 result

Disposition: `FAIL_OR_UNKNOWN` for the paired sequence. Phase 1 achieved `STRICT_RELEASE_PASS`; phase 2 did not reach fixture startup, so no fresh-generation task effect was tested and `task_success` remains null.

The repaired single-clock deadline ran as specified. The callback remained held for 1406.7954 ms after the public cancel response against the preregistered 1400 ms duration. There were 89 same-call polls (minimum 21), and same-generation Q-up was independently observed while the callback remained held. The phase-1 strict release audit passed 11/11 checks, and cleanup reported the producer, hook, fixture, and session closed with foreground restoration.

Phase 2 exited before opening a fixture. Its command passed a `.py` file path to `python -m`; CPython treated that path as a module name and exited with `ModuleNotFoundError`. The captured stderr identifies this as the startup failure. No phase-2 foreground marker or task inputs were created. This is a harness invocation defect, not evidence about phase-2 computer-control behavior.

The combined audit is 3/13 because the ten phase-2-dependent checks cannot pass without phase-2 evidence. Do not reinterpret this as a partial task success. R46 is one native Windows fixture trial and makes no WSLc, MAP01, efficiency, transfer, or reliability claim. Preserve its original raw and audit outputs without replay.
