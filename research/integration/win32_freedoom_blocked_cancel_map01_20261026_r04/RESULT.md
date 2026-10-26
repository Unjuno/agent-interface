# R04 — live Win32 blocked-callback cancellation

**Disposition: PASS for one preregistered live MAP01 held-callback cancellation and bounded recovery.**

The standard supervised Win32 public caller made one dispatch and one cancellation against the exact target generation `864b75e3eba68d70d3317f30567ad68ebf40fc8b42f444f825d91965ca9084f4`. The low-level hook recorded injected CTRL-down before cancellation. In the shared performance-counter domain, cancellation's cleanup request followed hook-entry by 247.5422 ms. The callback returned 1.6008 ms after that request with `release_gate_set=true` and `failsafe_timeout=false`.

The first cancellation response was `pending`. Exact call reconciliation returned `recovered` in 47 ms, before the runtime cleanup deadline. Release was confirmed, replay was denied, and the session closed without unresolved calls. The recovery receipt itself says `completion_readback_outcome=not_attempted`; two separate same-generation Ctrl-up reads immediately after verification and 1.5 seconds later both reported neutral.

The independent task verifier accepted the exact call, action operation, and generation. Recalculation over the frozen raw capture bytes found 231,260 of 256,000 world pixels changed (90.3359%), above the strict 5% threshold. This confirms a visible MAP01 effect, not a level clear. A local independent audit passed all 13 checks, including raw-pixel hash and count recomputation, event/cancel ordering, bounded recovery, receipt binding, and exact process cleanup.

The test-owned process exited after graceful close; no forced termination was used. The hook thread stopped. The close-level `release_confirmed=false` is separate from the recovered action's `release_confirmed=true`.

R01–R03 remain immutable observation-gate misses; none sent a cancel. R04 changed the monitor to poll public results while waiting for hook entry. Do not pool the four runs as a reliability rate. The complete raw packet remains local because original Win32 records contain local paths and process/window identifiers. Its 50-entry manifest SHA256 is recorded in `AUDIT-SUMMARY.json`; this sanitized derivative does not allow replay of the original receipt audit.

## H/T/D/C/U

- **H:** Cancel during the held callback recovers the exact action with release, neutral input and preserved visible effect, without replay.
- **T:** One fresh MAP01 run through the standard public caller with event-gated cancellation and concurrent read-only reconciliation.
- **D:** PASS only for the specific event order, recovered state, release and effect gates above; otherwise no blocked-cancel claim.
- **C:** Producer scheduling/target timing can make a fixed hook window miss; this was observed in R01–R03.
- **U:** One run, one application and one task effect. No MAP01 completion, efficiency comparison, or generalized reliability claim.
