# A12 preregistration - owner close on private-loopback Xvfb

**H.** The exact current-main V4->V3->V12 path admits one key to a focused Xvfb client and closes with the matching KeyRelease, key-up sample, verified terminal owner release and stopped owner thread.

**T.** Start Xvfb display `:134` with TCP enabled and Unix sockets disabled inside a private network namespace. The client and owner connect only to `127.0.0.1:134`; press `a`, verify, close, verify release and cleanup.

**D.** PASS_METHOD_SCOPED requires exact-main source digests and all independent raw audit checks. Setup/incomplete trace STOP; complete mismatch FAIL. One candidate and one auditor.

**C/U.** Isolated synthetic X server only. Does not establish application consumption, physical key state, useful feedback, task effect, threat response, recovery or task completion.

Base main: `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.
