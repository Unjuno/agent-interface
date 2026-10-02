# Allocation 01 pre-candidate STOP

The final current-main gate detected that main advanced after the local freeze from `4bd6d473eab20ce4e23d7ac2275aeae706187e7f` to `1326813275f1b73349acafc7c7cbc221e687dbd1`. The intervening commit only added unrelated archival live-control evidence and did not touch the Issue #6383 package. Nevertheless this allocation's run command requires an exact current-main freeze, so allocation `HUMAN-AUTONOMY-ENVELOPE-6383-T0-20261002-01` stopped before candidate.

Candidate=0; independent auditor=0; retries=0; WSLc candidate/auditor containers=0. No output directory was created. The original preparation freeze and checksum list are preserved as `FREEZE-0001-PRE-CANDIDATE.json` and `SHA256SUMS-0001-PRE-CANDIDATE.txt`. Its original `FREEZE.json` is retained byte-for-byte in this stop record's predecessor copy; it is not the active freeze.

The host-only construction suite previously passed 4/4 tests with all eight frozen corruption controls rejected. This does not consume a formal candidate or establish any human-factors result. A distinct fresh allocation 02 is prepared against the updated main, with a new output namespace; no retry under allocation 01 is permitted.
