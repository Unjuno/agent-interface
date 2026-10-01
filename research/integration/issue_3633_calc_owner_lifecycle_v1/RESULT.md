# Issue #3644 formal-01 result

**Decision: `HOLD_PROCESS_OWNERSHIP_UNRESOLVED`.** This preserves the preregistered gate; it is not a PASS.

On the pinned OrbStack Docker Linux/arm64 image, launcher PID/PGID/SID 12 and the visible Calc owner `soffice.bin` PID 37 were separate processes in the same dedicated process group. A single SIGTERM to PGID 12 removed Calc XID 4195109 by the second post-signal sample. The unrelated sentinel in PGID 11 survived. Xvfb was reaped and its private socket disappeared. Geometry, focus, input, model, and network operation counts were all zero. The in-container audit unit tests passed 6/6.

The group snapshot retained PID 12 in zombie state through the five-second observation, so “all captured group members disappear” was not demonstrated. Independent read-only audit recomputed the same HOLD, verified raw integrity and frozen source/image provenance with no errors, and detected all six corruption challenges.

**Interpretation caveat:** PID 12 was the direct launcher child. The frozen runner did not call `Popen.wait()` until after the group-sampling loop. The zombie may therefore be observer-side delayed reaping, not a live Calc process that survived SIGTERM. This caveat does not retroactively change formal-01’s HOLD; successor Issue #3657 tests the measurement-order ambiguity.

Evidence: `evidence/formal-01/`. Raw SHA-256: `6d110e3f3b7cbc0d1b970b50fb35a8d242c9cddb416190237419f78be8760824`.
