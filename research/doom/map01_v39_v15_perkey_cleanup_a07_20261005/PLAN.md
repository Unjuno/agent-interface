# A07 — current-main V39/V15 dropped-KeyRelease retry probe

## H — Hypothesis
On pinned V39/V15 batch-release and V4→V3→V12 owner sources, one synchronous fake-server dropped KeyRelease is observed as still down, retried once, and reaches neutral fake-server state before completed ExecutorV13 terminal.

## T — Test
One normal arm and one single-dropped-KeyRelease arm, each one F8 down/up fixture action; fake Xlib records keymap and drops exactly first release in treatment arm. Imports pinned production release/owner code. Controller action loop, session and X server are doubles.

## D — Decision
- **PASS:** Both arms complete, each has one verified release transition with non-authoritative physical verification, neutral fake-server state and verified terminal cleanup; normal has one successful attempt; dropped arm has two attempts [still down, neutral]; auditor passes all frozen source and raw checks.
- **FAIL:** Candidate completes but retry/terminal cleanup invariants fail, or claims verified cleanup while fake server remains down.
- **STOP:** Setup/runtime/fixture failure prevents both arms completing and raw evidence is absent or incomplete.

## C — Confounds
- Synchronous deterministic fake XTest updates do not model asynchronous transport, server errors, competing clients, physical devices, or application consumption.
- Paired arms run sequentially in one host process.
- Host runtime has no container resource isolation; runtime metadata is descriptive only.

## U — Limits
- Synthetic fake-X owner composition only; no real X11, GUI, Doom, model, physical keyboard, OS input, application effect, threat response, useful feedback, recovery efficacy, latency bound, or MAP01 claim.
- Does not satisfy the fresh live-exposure gate or authorize a live lane.


## Frozen invocation

Candidate and independent auditor hashes, exact commands, source commit, and one-shot policy are recorded in `FREEZE.json`. The candidate has not run at freeze time.
