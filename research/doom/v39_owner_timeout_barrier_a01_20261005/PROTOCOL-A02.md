# Bounded late-owner drain after timeout — A02

## H / T / D / C / U

**H:** After V13's two-second owner request timeout, waiting up to 1.5 seconds for the owner thread to stop and then draining its final records can clear the V39 bridge's stale F8 and emit any retained per-key release row before ExecutorV3's failed terminal, while preserving `release.verified=false`.

**T:** Reuse the byte-pinned current-main and PR #7805 A08 snapshots in `FREEZE.json`. Run one matched fake-display baseline and one candidate. Both block expiry cleanup in fake `sync()` until `InputOwner.call("release")` reaches its frozen timeout. The baseline opens the gate and immediately propagates failure. The candidate opens the same gate, waits at most 1.5 seconds for `owner.stopped`, drains once more, then propagates the same timeout. Retain full terminal, bridge-event, and owner-release summaries for both arms. No retries.

**D:** `PASS_BOUNDED_LATE_DRAIN_SCOPED` only if baseline reproduces terminal-before-drain with stale F8; candidate preserves one failed/unverified terminal, stops the owner within the additional bound, leaves physical and bridge state empty, emits no event after terminal, and forwards each available per-key row at most once before terminal. Do not require a confirmed-up classification when the source row is unavailable. Timeout outside 1.8–2.5 seconds or candidate wait above 1.5 seconds is FAIL; source drift is HOLD.

**C:** The explicit fake sync barrier forces one ordering and does not establish how often X11 calls block. The added wait can improve record custody while extending terminal time by up to 1.5 seconds; no live recovery benefit is inferred.

**U:** Native Windows fake-display construction only. No real X11/OS input, game, task effect, independently useful feedback, live threat exposure, matched recovery efficacy, latency distribution, safety, or MAP01 outcome.
