# Late cleanup beyond the A02 post-timeout wait bound — A03

## H / T / D / C / U

**H:** If the fake display's expiry-cleanup `sync()` remains blocked beyond the candidate's frozen 1.5 s owner-stop wait, the A02 candidate will emit the same failed/unverified terminal before the owner completes; the later physical up will not be drained, leaving F8 stale in the bridge ledger.

**T:** Reuse the byte-pinned current-main and PR #7805 A08 snapshots and A02 timeout schedule. In each matched arm, release the fake sync gate exactly 1.75 s after the owner-call timeout. Baseline propagates immediately; candidate waits its existing maximum 1.5 s and performs its existing conditional drain. Retain one pair only; no retries.

**D:** `FAIL_POST_BOUND_LATE_RELEASE_NOT_DRAINED` if the candidate wait expires before gate-open, the terminal remains failed/unverified, the owner later confirms physical up and stops, but the bridge emits no per-key up row and retains F8. `PASS_POST_BOUND_CUSTODY` only if the candidate bridges the delayed release no later than terminal while respecting the same bound and preserving failed/unverified terminal. Any source drift or schedule failure is HOLD/FAIL as appropriate.

**C:** A 1.75 s synthetic delay is selected to cross the 1.5 s cap by 250 ms and does not estimate how often or how long real X11 calls block. The run tests bounded custody behavior, not release safety or threat control.

**U:** Native Windows fake-display construction only; no real X11/OS input, game, application effect, useful feedback, recovery efficacy, latency distribution, safety, or MAP01 outcome.


**Runner version:** v2 corrects the helper import path after the retained v1 import-time failure; it does not alter the paired schedule or decision gates.

