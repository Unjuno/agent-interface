# A06 — one dropped KeyRelease against current-main V39/V15 owner

## H — Hypothesis
On current main `10be950b8fb6e2799b837b541577fb5f32db858d`, the selected V39/V15 batch-release backend with the current V4→V3→V12 owner will detect one injected dropped KeyRelease through the fake server keymap, retry, and reach neutral fake-server state before a completed ExecutorV13 terminal.

## T — Test
Use one frozen candidate invocation with a normal arm then a single-dropped-KeyRelease arm in one process. Both arms have one F8 down/up action; fake Xlib/server records the keymap; production V39/V15 release composition and production current-main V4/V3/V12 owner source are imported from 21 Git-blob-pinned modules. Only the base controller action-loop and session are doubles. Independently audit raw invariants, each per-key attempt receipt, source snapshot hashes and exact materialized bytes. One-shot candidate execution; preserve any STOP/FAIL and do not rerun under A06.

## D — Decision
PASS only if both cases complete, server keys are neutral after executor close, each has exactly one owner release row and verified release with physical authority false; normal takes one successful attempt; dropped-up case records first attempt still down then a retry that is neutral; and the independent source/raw audit passes. FAIL if a dropped release remains down or terminal reports verified while fake server is down. STOP if setup fails before both cases begin.

## C — Alternatives and confounds
The deterministic fake server applies synchronous XTest-like state updates and does not model transport timing, server errors, other clients, device state or application consumption. Cases are ordered and share one process. The test-double action loop excludes the ViZDoom session and game.

## U — Limits
One construction run with two paired synthetic arms only. No real X11, GUI, Doom, model, OS input, physical key state, application effect, useful feedback, recovery efficacy, latency bound, threat response or MAP01 result. This does not authorize or satisfy #59's separately gated live allocation.
