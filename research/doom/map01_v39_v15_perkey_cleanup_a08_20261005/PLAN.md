# A08 — current-main V39/V15 dropped-KeyRelease retry probe

## H — Hypothesis
On pinned V39/V15 batch-release and V4→V3→V12 owner sources, one synchronous fake-server dropped KeyRelease is detected as still down, retried once, and reaches neutral fake-server state before completed ExecutorV13 terminal.

## T — Test
One normal and one single-dropped-KeyRelease arm, each one F8 down/up fixture action. Test double supplies the fixed fake-session observed focus (41) to the V13-owned lease, then the test action-loop calls selected production release composition. Fake Xlib records keymap and drops exactly the treatment arm first KeyRelease.

## D — Decision
- **PASS:** Both arms complete; each has one verified release transition, false physical authority, neutral fake-server state and verified terminal release. Normal takes one successful attempt, treatment takes two attempts [still down, neutral], and independent audit passes.
- **FAIL:** Completed candidate violates retry or terminal-release invariants or reports verified while fake server remains down.
- **STOP:** Fixture/runtime/setup fails before both arms complete or no complete raw pair is produced.

## C — Confounds
- Synchronous deterministic fake-X updates do not model transport timing, server errors, competing clients, physical devices, or application consumption.
- Paired arms run sequentially in one host process.
- Host runtime has no container resource isolation.

## U — Limits
- Synthetic fake-X composition only; no real X11, GUI, Doom, model, physical keyboard, OS input, application effect, threat response, useful feedback, recovery efficacy, latency bound, or MAP01 result.
- Does not satisfy or authorize the separately gated live-exposure lane.


Exact hashes, commands, source commit, and one-shot rules are in `FREEZE.json`. Candidate has not run at freeze time.
