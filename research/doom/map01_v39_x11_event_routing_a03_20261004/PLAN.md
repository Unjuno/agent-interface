# A03: X11 event-routing control versus InputOwner v10

Issue: [#59](https://github.com/Unjuno/agent-interface/issues/59)

## H / T / D / C / U

- **H:** On one private Xvfb, both direct XTEST and current-main InputOwner v10 deliver a matching `W` press and release to the same focused Xlib client, whose event loop increments its counter once per press.
- **T:** One frozen candidate invocation compares a direct XTEST control with one sequential v10 down/up occurrence. An independent observer samples server keymap state, while the client retains every key event it receives, including mismatches.
- **D:** PASS only if both routes have false/true/false keymap samples and exactly one matching focused-window press and release; client counter advances once per route; v10 owner state and explicit release are verified; and Xvfb cleanup succeeds. A complete mismatch is FAIL. Incomplete execution is STOP. Never retry.
- **C:** Xvfb and the client are virtual. Direct XTEST is a routing control, and the sink is a minimal test client, not a production app.
- **U:** Tests event delivery and a minimal client-side state change only. It does not test DOOM, model latency, useful feedback, recovery, physical input, task success, safety, or threat exposure.

A02 timed out in a wait function that discarded nonmatching key events and failed to save partial state. A03 changes the measurement: it includes a direct XTEST route control, retains all key events, and writes partial raw state even when incomplete.
