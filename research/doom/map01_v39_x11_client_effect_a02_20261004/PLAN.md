# A02: focused X11 client event effect

Issue: [#59](https://github.com/Unjuno/agent-interface/issues/59)

## H / T / D / C / U

- **H:** Current-main InputOwner v10 sending `W` to a focused X11 client on private Xvfb delivers one `KeyPress` and one `KeyRelease` to that client; its event handler increments a counter once per press.
- **T:** One frozen candidate invocation, two distinct press/release occurrences, real Xvfb, a separate observer connection for `XQueryKeymap`, and an event-driven Xlib client window. Retain client events, counter state, owner state, exact source identities, and an independent audit.
- **D:** Pass only if each occurrence has keymap false/true/false, exactly one matching client press and release event for the focused window/keycode, counter transition 0→1→2, correct owner-held state, and verified empty close. No retries.
- **C:** Xvfb is a virtual X server. The sink is a minimal Xlib client, not a game or production GUI; no physical keyboard is involved.
- **U:** Establishes event delivery and a minimal client-side state change only. No DOOM behavior, useful feedback onset, bounded recovery, latency benefit, task success, safety, or live threat-control result.

The candidate calls v10's direct down/up API and explicit owner release boundary. It does not exercise the v39 typed backend. That separation makes the client event effect the changed factor from the keymap-only controls.
