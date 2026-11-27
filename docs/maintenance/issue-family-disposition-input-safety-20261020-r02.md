# Issue #17 disposition r02 — fault-layer evidence crosswalk

Reviewed 2026-10-20 against live Issue #17 and current `origin/main` at
`434c75ec8dd63c1a76af405026fed91c416bc598`. This record routes existing
evidence by fault layer; it does not replace raw packets, change an outcome,
or authorize a new live allocation.

## Disposition

Keep [Issue #17](https://github.com/Unjuno/agent-interface/issues/17)
`open/actionable`. The question is whether cancellation, expiry, authority
revocation, and input release remain bounded and reachable when planner-facing
observation, receipt persistence/serialization, event delivery, or platform I/O
stalls. Current results answer different slices of that question and cannot be
combined into a general guarantee.

| Fault layer | Retained evidence | What it supports | What remains unproved |
|---|---|---|---|
| Journal write/flush stall | [`JOURNAL_STALL.md`](../../research/live_control/JOURNAL_STALL.md) and its linked raw/tests: `journal-stall-02` had release in four scoped cases but one write/cancel receipt-order failure; serialized `journal-stall-03` passed four probe cases with order preserved. | A probe can release under the tested write/flush schedules; the first ordering failure and its serialized follow-up remain distinct. | The probe is not the public caller, and cancellation had not returned while blocked notification resumed. |
| Owner blocked in Xlib `Display.sync()` while X server remains responsive | The [retained r01 packet](../../research/integration/standard_caller_xvfb_blocked_release_20261020/r01/README.md), captured for PR #9225 and carried forward with PR #9226's liveness-timestamp/test update, preserves five trials from one private-Xvfb job: the independent synthetic task oracle passed; held and delayed keys were up at independent readback/horizon. The standard caller still returned `cancel_unconfirmed`, release/cleanup `UNKNOWN`, `task_success=null`, replay denied. | Bounded independent release can succeed in this exact owner-blocked schedule when the X server accepts the separate release connection. | Five within-job trials are not independent environment replications. They do not establish full-server-outage release, physical desktop release, MAP01, broad reliability, or efficiency. The later liveness-timestamp source/test change is not a new live environment replication. |
| Full X server stopped | [PR #9220 r01](../../research/integration/standard_caller_xvfb_server_stop_20261020/r01/README.md) retained the adverse result: held key remained down at 8.5 s and the independent task oracle failed while service was unavailable. [PR #9225 r02](../../research/integration/standard_caller_xvfb_server_stop_20261020/r02/README.md) records one post-resume explicit close with independent key-up readback. | The outage result is a counterexample to release during that server stop; one post-resume release-only recovery observation exists. | Post-resume cleanup does not upgrade the earlier cancel/task result or establish an outage-time deadline, repeated recovery reliability, physical release, MAP01, or efficiency. |
| Stdout delivery and image/receipt serialization stalls | No matching composed-path result was identified in the checked #17 family records and source/test crosswalk. | These remain explicit coverage gaps. | This bounded search does not establish that no such result exists elsewhere in the repository. |

## Next decision

Keep the fault layers separate. The next live discriminator must use the
standard caller, establish held input and an independently scored task effect
before fault injection, declare cancel/recovery horizons in advance, and retain
raw for both outage and post-resume states. It must distinguish requested,
injected, independently read-back, and physically confirmed release; recheck
target/process generation after recovery; and report every attempt. First verify
that an unused allocation is actually available. WSLc #7924 remains STOP/HOLD;
this triage did not use or release WSLc, Docker, or a formal allocation.

No Issue was closed. The broader repository cleanup and #17 acceptance criteria
remain incomplete.
