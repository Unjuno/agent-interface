# Current InputOwner process isolation under session SIGKILL — Xvfb A06

## Decision

**A02: `PASS_METHOD_SCOPED`.** The test used the exact `input_transition_owner_v4.InputOwner` class selected by the V15 backend. Its default composition created the V3 wrapper over the current V12 X11 owner thread. A detached service process owned that stack, accepted a versioned local request with an actual `Lease`, intent token and observed focus-window ID, then pressed key `a`. After the session process was SIGKILLed, socket EOF caused the service to call the real `InputOwner.close()`. The owner emitted one identity/deadline-bound verified `owner_release` with empty key/button/unknown/error state; its X11 thread stopped; the service fsynced its receipt and exited 0. A separate X connection observed KeyRelease and keymap-up.

This advances the minimal A05 process proof to the production InputOwner implementation used by the opt-in V15 backend. It remains a process/RPC prototype, not production V15 backend wiring or task-level integration.

## Preserved arms

**A01: `STOP`.** The session was killed after actual admission. The independent observer saw KeyRelease and keymap-up, but the owner process failed after `close()` while the harness followed an incorrect internal wrapper chain to inspect the stopped-thread flag. It exited 1 without persisting its release record. The raw arm and `RUNNER/A01-owner-receipt-error.txt` preserve that failure; it is not promoted based on the observer alone.

Two earlier setup attempts failed before a scored arm. The first did not preserve child stderr. The second sent the observed focus ID as a JSON string; the strict decoder correctly refused it. `RUNNER/SETUP_ATTEMPTS.txt` and the captured rejection transcript retain the distinction.

## A02 evidence

See `results/A02/RAW.json`, `results/A02/AUDIT.json`, and `FREEZE.json`. The session returned `-9`; the owner observed EOF after the kill request and began close 8.8 microseconds later. Its XTest KeyRelease began 202 microseconds after EOF; XSync returned and the V12 keymap sample found the key up. The independent connection observed KeyRelease and independently sampled the keymap up. The identity-bound owner record's intent token and deadline match the admitted lease; the receipt is fsynced; no forced service termination occurred; Xvfb exited 0.

`test_protocol.py` passes eight standard-library unittest cases for exact RPC fields, key allowlisting, integer deadlines, observed focus, successful recovery audit, missing verification and mismatched intent. The raw-only audit rejects A01 and passes A02. Candidate and imported owner sources are pinned by SHA-256.

## Limits and next work

The local protocol covers one key and one request. The session receives a focus ID from the harness; production must bind this to its actual observation and include display identity and owner readiness in its handshake. The test does not wire through `doom_owner_thread_release_batch_backend_v1.Backend`, session V15 or the outer V39 controller. It also does not cover mouse buttons, multiple held keys, partial or duplicate frames, focus drift, service/supervisor failure, durable receipt discovery by the controller, or a gate preventing display reuse. No VizDoom game, model, GUI application, physical input or MAP01 allocation was used.

Next, connect the remote adapter to the opt-in V15 backend behind a feature flag, pass observed display/focus identity through the session handshake, and make outer cleanup wait for the fsynced owner receipt before allowing display reuse. Test ordinary down/up and session kill with one and multiple keys before considering any live lane.
