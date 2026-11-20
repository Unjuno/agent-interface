# Release receipt failure boundary — #59 T1 A02

## H / T / D / C / U

**H:** The additive V10/V11 receipt path does not turn partial XTest/XSync
failure into a false transition claim. When an XTest request has been sent but
XSync raises, the owner may retain stale held bookkeeping even if the server
already applied the release. A later retry may complete request+sync without a
new key-state edge, which limits what `release_applied` can mean.

**T:** Using the source hashes and fixture blob in `FREEZE.json`, admit one
key, inject (1) an XTest failure before the fixture applies KeyRelease and (2)
an XSync exception after the fixture applies KeyRelease, then inspect the
exception/receipt, owner bookkeeping, server keymap and one retry. No real
display or OS input is used.

**D:** The call is fail-closed if the failed RPC returns no receipt. Determine
whether a later true receipt proves a state transition or only a completed
release request and XSync interval, using the independent fixture keymap.

**C:** FakeDisplay defines whether the release reached its in-memory server
before the injected exception; real Xlib/X server error delivery and external
input interleaving may differ.

**U:** No physical key state, external keyboard, application consumption,
latency, game, model, recovery quality or live runtime behavior is established.

## Reproduction

```powershell
python research/doom/map01_release_receipt_failure_boundary_59_t1_a02_20261004/probe.py
python research/doom/map01_release_receipt_failure_boundary_59_t1_a02_20261004/audit.py
```

## Result

Both injected failures propagated without fabricating a receipt. The XTest
failure happened before the fake server changed key state; retry sent one
release request and returned a successful receipt. In the XSync case, the
fake server had already applied the first KeyRelease when the client-side sync
raised. Retry then sent a second KeyRelease and returned `release_applied=true`
with a non-null `release_transition_interval_ns`, even though fake key state
was already up before that retry. Therefore those fields establish a
completed release request and sync during the caller bracket, but do not by
themselves establish that a physical key-state edge occurred in that bracket.

This is a scoped counterexample to interpreting `release_transition_interval_ns`
as a physical transition interval after an unreceipted partial failure. The
live path must retain failed release attempts or independently verify state
before making per-key occupancy claims. No live X server, keyboard, game,
model, or allocation was involved.
