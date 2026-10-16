# A15 supervisor emergency-release primitive

A14 found that killing the owner service leaves its keys and button held, without a recovery receipt. A15 keeps the same two-key/Button1 session and owner-service SIGKILL, then tests a narrowly scoped fallback: once the owner is confirmed dead/zombie and the original focus identity still matches, the supervisor X connection issues explicit XTEST KeyRelease for only the two recorded keycodes and ButtonRelease for Button1, syncs, and independently verifies all states/events are up.

This tests only the recovery primitive under an isolated Xvfb display. It does not claim the outer V39 controller currently implements this recovery. One candidate invocation; no retries.
