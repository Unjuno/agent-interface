# A09 preregistration - exact-main owner close on isolated Xvfb

**H.** The exact current-main V4->V3->V12 owner closure will admit one key on a focused Xvfb client and close with a verified terminal release.

**T.** One TCP-disabled Xvfb display `:131`; press `a`; verify KeyPress; close owner; verify matching KeyRelease, observer key-up, verified terminal owner release, stopped thread and Xvfb exit 0.

**D.** PASS_METHOD_SCOPED only if the frozen source hashes and all raw audit checks pass. Incomplete/setup evidence is STOP; complete semantic mismatch is FAIL. Candidate once; auditor once if raw exists.

**C.** Synthetic X-server state only; no desktop app, physical keyboard, game, model or private lane.

**U.** No claim of application consumption, useful task feedback, latency distribution, threat response, recovery or task completion.

Base main `f185a9059d485a4f8d5a65e9e7f6782897f67eae`. The only change from A08 is persisting extracted runtime dependencies on D: so WSL cleanup cannot remove them before the run.
