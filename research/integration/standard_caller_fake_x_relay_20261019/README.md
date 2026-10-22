# Standard MCP caller + Fake X relay composition

**Disposition: `PASS_FAKE_X_BOUNDED_CANCEL_SCOPED`.** The standard guarded MCP caller reached a key press, then blocked its owned child on a selected 32-byte `GetPointerControl` reply held by a process-local socket-pair relay. In both Python modes, cancel retired the child in about 1.0 s, returned a terminal result within the predeclared local bound, preserved the held-key obligation, and kept release `UNKNOWN`, task success null, and replay disabled.

This is a finite local composition result. It shows that this caller fixture can stop waiting for the blocked child and return uncertainty within the test's bound. It does not show that the key was released by an X server or OS, that the target application consumed it, or that the task succeeded.

## Question and frozen conditions

**H:** With the owned MCP child blocked in synchronous socket I/O after a press, can the standard caller retire the exact child and produce a fail-closed terminal result within a fixed local bound, without claiming release or replay? A separate stale-generation control must refuse before the relay sees input.

**T:** Run the same two regression cases once under Windows Python 3.11.9 normal mode and once under `-O`, using MCP 1.30.0 and python-xlib 0.33. The relay, fake upstream and independent synthetic receipt observer communicate only over local `socketpair()` channels. The selected reply timeout is 8 s; the frozen caller-response bound is 3,000 ms and the terminal-result bound is 5,000 ms. The conditions file and source identities are retained beside this report.

**D:** Pass only if both modes preserve the 32-byte held reply, retire the owned process, retain `a`/keycode 2 as an input obligation, return within both local bounds, and keep release `UNKNOWN`, task success null and replay disabled. The generation-change control must refuse before any relay press. A timeout, unexpected input, optimistic release/success, replay, mode disagreement or missing raw is a failure of this construction check; no result is retried or reclassified.

**C:** The synthetic effect observer records that a Fake X request was accepted; this is not an application effect. The disconnect fence is deliberately fixed to `unknown`, so the test exercises cancellation and conservative reporting without asserting XRes or server disconnect. The bounded time includes only this Windows test harness and its child supervisor; it is not a physical release deadline.

**U:** One execution in each interpreter mode does not estimate a timing distribution. The test uses no X server, GUI, OS input, model, external network, Docker, WSLc or formal allocation. It cannot establish real-server queue drainage, physical key-up, application task effect, MAP01 progress, cross-platform behavior or universal cancellation bounds.

## Observations

Both modes passed 2/2 composition tests. A combined replay of the offline relay/parser tests and the caller composition then passed 29/29 in normal mode and 29/29 under `-O`. The normal composition run recorded 1,031 ms to return from cancel and 32 ms to observe the terminal result; the optimized run recorded 1,015 ms and 16 ms respectively. The held reply contained 32 bytes and a separate receipt observer saw the matching synthetic `KeyPress`. The child retired with obligation `{keys: {a: 2}, buttons: []}`. Because the disconnect fence was unknown, release was not attempted or confirmed; the terminal status was `runtime_failed`, cleanup `UNKNOWN`, task success `null`, replay disabled, and `late_server_request_possible=true`.

After the alias was minted, changing the process-generation marker caused the standard caller to return `refused` with `input_dispatched=false`; the relay saw no press. The normal and optimized raw result semantics matched under a separate raw-only audit in both Python modes.

Exact test output and per-mode JSON records are under [`raw/`](raw/). The machine-readable run receipt is [`run-receipt.json`](run-receipt.json); frozen inputs are [`conditions.json`](conditions.json) and [`source-identities.json`](source-identities.json). [`SHA256SUMS`](SHA256SUMS) binds the report, code, conditions, raw logs and source inputs. The preceding [offline framing/relay packet](../offline_proxy_reply_framing_20261019/FAKE_RELAY.md) remains unchanged and separately checksums its own source and results.

## Next boundary

The local blocked-I/O cancellation seam is now composed through the standard caller, but only with a forced-unknown disconnect receipt. The remaining release question is whether an eligible real X server can independently establish owner disconnection and input release under the required failure conditions. That requires an unused, verified allocation and the applicable owner authorization; this Fake X construction does not authorize or substitute for it. Until then, retain `UNKNOWN` and do not claim a release deadline or task success.
