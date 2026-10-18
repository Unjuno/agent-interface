# A05 — corrected X11 client-window event routing

Issue: [#59](https://github.com/Unjuno/agent-interface/issues/59)

## H / T / D / C / U

- **H:** With the same Python-Xlib 0.33/Xvfb fixture as A04, reading `event.window` will bind each received KeyPress/KeyRelease to the focused client window; both direct XTEST and frozen InputOwner v10 will increment that client's counter exactly once per press.
- **T:** One frozen candidate invocation runs the direct-XTEST control and one InputOwner v10 down/up occurrence in a fresh isolated OrbStack Ubuntu 24.04 arm64 guest. An independent X connection samples the server keymap; the focused client retains every key event and counts only the exact window/keycode match. Run the raw-only auditor only after candidate exit 0.
- **D:** PASS only if both routes yield pre/down/up keymap states false/true/false, exactly one matching client press and release in order, one counter increment each, v10 verified-empty explicit release and close, and clean Xvfb teardown. A completed mismatch is FAIL. Missing custody, timeout, or candidate failure is STOP. Candidate once; no retry.
- **C:** This checks the corrected Python-Xlib field against the previously retained A04 failure. The minimal client counter is a routing control, not a production application's useful task effect.
- **U:** Virtual X11 only. No Freedoom/game, host model, live task, feedback usefulness, recovery, physical input, latency benefit, or MAP01 claim.

A04 remains unchanged with its original `FAIL_AUDIT`. A05 uses a new allocation ID, fresh VM, unique output, and frozen candidate/auditor. Package installation occurred during setup; the candidate itself makes no network calls, and Xvfb TCP listening is disabled.
