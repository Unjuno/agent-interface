# A05 result — corrected X11 client-window routing

**Disposition: `PASS_EVENT_ROUTING_CONTROL`, scoped to the frozen virtual X11 test.** The candidate ran once (exit 0); its raw file has SHA-256 `903f1063eb1cb7e9011ddbf871d7083946c62835baea1f5eb6afa0cfddb3dde6` on both the isolated guest and the host copy. The frozen raw-only auditor ran once after candidate exit 0 and passed all checks (exit 0, zero errors). The observed keymap pattern is false→true→false for both routes. The client received exactly one matching KeyPress and one KeyRelease per route on window `4194304`, keycode `25`; the test client counter advanced `0→1→2`. InputOwner v10 returned a verified empty explicit release and close record. Xvfb was stopped normally (exit 0), with no cleanup errors.

The A05 candidate reads `event.window`, matching Python-Xlib 0.33's retained KeyPress/KeyRelease field, instead of the wrong `event.event` used by frozen A04. A04 remains unchanged and retains its original `FAIL_AUDIT`; A05 is a distinct fresh allocation and unique path.

The guest was an isolated OrbStack Ubuntu 24.04 arm64 machine, with Python 3.12.3, Python-Xlib 0.33-2 and Xvfb 21.1.12-1ubuntu1.8. Package installation occurred during setup; the candidate made no network calls and Xvfb TCP was disabled. Effective resource caps were not verified.

This only demonstrates routing into a minimal Xlib test client and its counter. It does not test Freedoom, another production application, a high-capability model, independent useful feedback, recovery, matched conditions, physical input, or MAP01 progress. The #59 live task-effect and matched recovery gate remains open.
