# Persistent native release quarantine

2026-09-20. Integration of one condition motivated by Issue #2437, on base
`47c84c4c10ac813b978f32b7910320310a3adf5a`. This is not closure of that issue.

The X11 session now refuses subsequent dispatch with INPUT_RECOVERY_REQUIRED
when release evidence is missing, malformed, unverified, non-neutral, or an
unexpected execution exception loses the receipt. Completed, partial-failure,
and backend-preflight cleanup paths retain their original result distinctions.
A successful observation or explicit window review cannot reset the latch;
the research handle bridge also refuses mint/click while it is set. Backend
cleanup and read-only observations remain possible. There is deliberately no
reset/re-admission method until independent recovery ownership is defined.

## Native experiment

A private Xvfb/Tk fixture receives a real left-button press followed by an
injected execution failure and suppressed cleanup. A separate X11 connection
observes left still down. The same session refuses a new program with fresh
sequence/revision, without additional emissions or a saved task effect.
Explicit backend cleanup restores an independently observed empty button state,
but the original session still refuses dispatch. Existing healthy controls
produce exact independently saved text and verified release.

`attempt-3/live-trace.json` retains all three dispatch results, cleanup receipt,
and separate-connection button observations. Nine native tests plus 25 focused
unit/adapter/bridge tests passed (34 total). The bridge test additionally proves
window review cannot clear input recovery. These are automated runtime tests,
not assistant visual gameplay/self-use or a latency/token benefit measurement.

## Retained attempts and limits

Attempt 1: native regression passed; 2 of 34 tests failed because the inert
adapter fixture supplied only verified=True without neutral-state fields.
Attempt 2: 34 passed after supplying the actual backend-shaped fixture.
Attempt 3: 34 passed after adding malformed/missing release controls and checking
partial-failure recovery flags. All logs, traces and Xvfb cleanup statuses remain.
`final-source/` contains the final source; earlier source snapshots were not
captured, so do not claim exact source replay of attempts 1 or 2. The driver
is the final attempt driver and requires the local Tk dependency environment
documented in native-partial-live-01. CI runs these tests with its own Xvfb.

Scope is one persistent Python session/connection owner. It is not a global
input lock, a crash-persistent supervisor, a host/compositor failure test, or a
safe cross-session restart protocol. Constructing a new session is not proof of
recovery. Key neutrality is the existing backend's tracked-key check, not a
claim that every physical keyboard key is observed. X server calls can block;
no hard cleanup deadline is promised. Private fixture files are temporary and
not retained; the ordered failure trace and test logs are retained.

SHA256.json covers retained files except itself and this README.
