# V39 owner-reply timeout under the inherited release barrier — A01

## H / T / D / C / U

**H:** The current V39 A08 completion barrier uses the V13 owner's finite two-second request wait. If the owner remains blocked in fake-display `sync()` after applying a key-up, ExecutorV3 should terminate failed and unverified within a bounded interval; after the owner is released, the confirmed per-key-up should either reach the bridge or leave a clearly stale bridge ledger requiring a new repair.

**T:** Freeze current `main` 563f636 and the exact A08 candidate/source snapshot from PR #7805 head 61502e4. Using its inherited V39 × ExecutorV3 fake-display harness, admit F8, let expiry initiate owner cleanup, block cleanup `sync()` beyond the two-second `InputOwner.call` bound, and wait for the final release barrier to time out. Record elapsed time, terminal status/release verification, then release the gate and observe owner/physical/bridge state and receipt delivery. One run; no retry.

**D:** `PASS_BOUNDED_FAIL_CLOSED` only if the release call times out in 1.8–2.5 s, ExecutorV3 emits one failed terminal with `release.verified=false` before the owner gate opens, and the eventual owner cleanup is neutral. A missing confirmed-up bridge receipt or stale bridge-held key after owner cleanup is separately reported as a recovery defect; a false verified terminal or unbounded wait is FAIL. Source drift or harness mismatch is HOLD.

**C:** A gate held beyond the request timeout is a deliberately forced schedule, not an estimate of real X11 blocking frequency. Fake `sync()` controls ordering; it does not prove when an OS or target application consumes the release.

**U:** No real X11, OS keyboard, game, task effect, model, independently useful feedback, live threat exposure, matched recovery efficacy, latency distribution, or MAP01 result is tested. This is a local fake-display construction experiment, not the separately gated live #59 allocation.
