# Edge local effect smoke, fresh run 2 (2026-11-16)

This is a new one-use local smoke to verify the bounded cleanup repair from
commit `ce4926cdcf189546342e1f202a1efe09b914f05f`. It does not reuse the
previous browser profile or task allocation. The only target is the test's
loopback synthetic form in a fresh Edge profile.

- One input attempt; no retry after dispatch.
- The offline test double supplies the target contract; no provider/model call.
- Require one exact expected-value POST, caller task success, verified release,
  one completed transition and zero frontier-model resumptions.
- Require the test-created Edge process/profile cleanup to finish with no
  exception and no profile directory remaining.
- On any mismatch or cleanup failure, preserve it and stop.

This remains a local smoke, not a matched Issue #57 comparison. Test and worker
hashes, environment and the command transcript are recorded in `RUN-v2.json`
and `attempt-03.log`.
