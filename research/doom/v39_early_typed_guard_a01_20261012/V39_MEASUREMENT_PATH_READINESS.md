# V39 measurement-path readiness checkpoint

Date: 2026-10-12. Scope: local composition readiness for the next separately authorized V39 threat-exposure run. This does not count as live game evidence.

## Decision
Current-main V39 already has an opt-in measurement path for the missing telemetry. A run using `--measurement-session` selects `session_map01_v15.py`; default remains v12. No additional scorer or release-timing mechanism is needed before the prospective live experiment. The pair-watermark repair on this research branch still needs integration before that experiment can use it.

The v15 composition selects Executor v13 and the release-batch backend. Per-key `input_release_transition` rows join caller-side release brackets to owner-thread XTest KeyRelease/XSync timestamps and X11 keymap samples. The independent progress scorer samples the same game process/main thread at 35 Hz, writes `scorer-samples.jsonl` and `scorer-events.jsonl`, and marks those rows `controller_visible=false`. These event clocks support a prospective onset interval for independently observed kill/exit progress; a scorer event does not establish physical keyboard state or complete task success by itself.

## Frozen source identities (SHA-256)

- `research/doom/map01_overlap_controller_v39.py`: `704c8c8a35f88765f207e4be18b4e32979fdcb6960aaeafcb867dcee4cb8eed0`
- `research/doom/session_map01_v15.py`: `661b3ac311f72517670a8fe37bc2901e9479963afc9db0a219ed83ea48601724`
- `research/doom/doom_owner_thread_release_batch_backend_v1.py`: `2df84b632456388a488f2595347b6b37def29f66b47f97a44d89ed5c11b8d418`
- `research/doom/doom_typed_release_backend_v2.py`: `7192d1a47b1677ce22584eebbec51b19c7aa55c67122d2a9c85e528ff095adf4`
- `research/live_control/input_transition_owner_v4.py`: `ea5fb38f0b00da1745c9ede0d256918a1dfdf2a473a794fa22cd28de13790598`
- `research/live_control/executor_v13.py`: `d12934e7ddfa4888acaef93c37dc54773369c3c3a72a3a2dfcc8fe2714d0688b`
- `research/doom/map01_scorer_stdio_adapter_v1.py`: `626abae869c3c77fa76333347ee247eb9ce6ef25baf6d7e692fc59ff131180ab`
- `research/doom/main_thread_scorer_polling_v1.py`: `32a1a4add2949c2dc65933bef0edb1903452851b44f2ee6da4a74c18dd4ade84`

## Local verification

77 tests passed across isolated processes/platforms:

- WSL Python 3.12.3: v15 session composition 8; scorer adapter 5; scorer polling 12; release race 1; cancelled-lease release 3; watermark replay 1; owner V4 join / V12 explicit-up cancellation 9.
- Windows Python 3.11: V39 controller selection and policy 16; pending observation drain and coherent recovery 22.

A combined Windows invocation was not a valid gate: `test_session_map01_v15.py` installs temporary module stubs at import time, contaminating later adapter tests when deliberately run first, and the polling test uses a POSIX-select pipe path unsupported on Windows. The modules above passed in fresh WSL processes, while controller-dependent modules passed on Windows with the correct `PYTHONPATH`. WSL lacked Pillow for the controller modules; no dependency was installed.

## Limits and next gate

No game, GUI, executor process, model call, physical input, or shared allocation was used. Unit tests cover fake X11/keymap receipts and scorer scheduling, not the real display/game path. The next live run still needs a fresh current-main freeze and explicit bounded allocation, must retain all assigned episodes and raw per-key/scorer event rows, and must preregister the threat schedule, useful-effect endpoint, recovery budget, and stop condition. The local readiness tests do not justify starting that run.
