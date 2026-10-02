# Issue #59 T2 — delivered repeats and client callback state effects

## H / T / D / C / U

- **H:** When a minimal focused X11 client receives the later autorepeat
  `KeyPress` events seen in T1, its ordinary event callback can mutate
  client-owned state even though the initiating press was delivered to the
  previous focus. The local effect counter should advance one-for-one with
  delivered W `KeyPress` callbacks while global W remains down.
- **T:** Start one private Xvfb with two windows A/B and a client callback that
  increments a per-window in-memory `movement_tick_counter` on every delivered
  W `KeyPress`. Run a 1.2-second held positive control on A. Then press W on A,
  move focus to B while still held, and run the same 1.2-second interval. Record
  full event stream, callback effect rows and before/after state, full 32-byte
  XQueryKeymap samples, focus and action timestamps. Candidate once, independent
  raw-only audit once, zero retries.
- **D:** `PASS_X11_CALLBACK_EFFECT_MATCHES_DELIVERED_KEYPRESS` iff the A control
  establishes at least two W `KeyPress` callbacks, A gets the transfer's
  initiating press, B is focused while W remains globally down, and B's
  callback counter increases exactly once for every W `KeyPress` delivered to
  B in the held interval. Every counted effect must link to one unique event,
  observe W down and B focused, and counters must be contiguous. A well-formed
  run with no B callback/effect is a scoped FAIL. Missing control, identity,
  event/effect linkage or cleanup is STOP.
- **C:** Successor to Issue #59 T1 on main
  `8d9b496dd23b72bf73ca06756e23c329f5489735`. T1 observed 14 B KeyPresses and
  14 KeyRelease/KeyPress pairs after focus transfer; it measured protocol
  delivery, not client callback state. This experiment adds one explicit
  event-handler state mutation per W KeyPress; it does not rerun MAP01 or claim
  a real application effect.
- **U:** A deliberately minimal in-memory counter is the only client effect.
  XTEST/private Xvfb only; no physical input, real app/game, model, threat
  response, MAP01 progress/survival, safety, or efficacy claim. Counter changes
  are not useful task effects or proof any external application acted.

## Stop rule

Freeze source/image/fixture before one candidate run. One independent raw-only
audit; zero retries. Preserve raw and any failure/STOP unchanged.
