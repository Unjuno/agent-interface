# Writer UNO serialization negative v1

Question: do available LibreOffice Writer UNO primitives close the post-guard compare/write race?

Frozen arms: `compare_set`, `recheck_set`, `controllers_lock_set`.
Each arm runs in three fresh private Xvfb/Openbox/Writer sessions, fixed counterbalanced schedule:
`compare_set, recheck_set, controllers_lock_set, controllers_lock_set, compare_set, recheck_set, recheck_set, controllers_lock_set, compare_set`.

In every session A starts `book`. Candidate checks the expected text. `recheck_set` performs a second final read; `controllers_lock_set` holds `lockControllers()`. Candidate then publishes a barrier. A separate UNO process must write `boox` after that barrier and return before candidate is released. Candidate then writes stale desired text `bookkeeperoffice`.

PASS_NEGATIVE if all 9 sessions prove the external mutation completed after the final candidate check/lock and before the candidate write, and the candidate overwrote `boox`; lock arm must additionally observe `hasControllersLocked()==true` from the external process. This PASS rejects these mechanisms as atomic serialization; it is not application-task success.

No XTest/model/provider/network/shared-runtime calls. Private X11/Writer/UNO only. No claim about macro execution or unavailable atomic application extensions.
