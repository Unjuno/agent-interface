# R42 preparation

R42 is one frozen native Windows attempt against main `e6192a4294aac0d94d51e75b24583216c718d654`. It follows R41's dispatch-queued/busy result with a bounded, user-authorized CUA activation gate for each exact owned fixture window. No public API observation or dispatch begins until CUA activation has a retained receipt and the process independently reads the same fixture HWND as the current foreground window.

The experiment has one phase-1 dispatch and at most one cancel. Phase 2 runs once only if every strict R36 release criterion passes; otherwise it is omitted. All mismatches and unknowns remain failures. No retry, replay, WSLc, Docker, MAP01, reliability, or efficiency claim is included.

The pinned R36 predecessor raw and audit are restored from the verified private backup and checked against their frozen SHA-256 values. R42's static files, runtime dependencies, predecessor references, and absence of output/activation markers are checked by `preflight_r42.py` before the one-shot runner.
