# Issue #3657 formal-01 result

**Decision: `PASS_PRIVATE_PROCESS_GROUP_CLEANUP_SCOPED`.** Independent auditor agreed.

Pinned OrbStack Docker Linux/arm64 image: `sha256:e6ced3789130dae21c7b42b7b9d25cd590a271a77910e16c01d2edf87e44cee6`; frozen base main: `f46f9f3db778443764581d5e7c522d5029fdf7a2`.

Launcher PID/PGID/SID 10 and visible Calc `soffice.bin` owner PID 35 were distinct processes in the same dedicated group. Exactly one SIGTERM was sent to PGID 10, followed immediately by `Popen.wait(timeout=1.0)` on the direct launcher; it was reaped with return code 255. The owner PID+start-time, remaining group members, and Calc XID disappeared within the five-second observation. Sentinel PGID 11 survived until its own cleanup. Xvfb was reaped and its private socket disappeared. Geometry/focus/input/model/network operations were zero; the six audit unit tests passed.

The independent read-only auditor verified raw integrity and frozen source/image provenance with no errors and detected all six corruption challenges. Raw SHA-256: `e3d6dcec0fd9f0d1bddae7e8b0c86abb284ff09200cf5f86349db21b917a2068`.

This confirms the wait-order ambiguity for this fixture: immediate direct-child reaping permits the process group to reach empty without the delayed launcher zombie seen in #3644. It is not evidence for generic daemon or cross-platform cleanup.
