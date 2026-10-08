# Actual early-exit child construction control

Initial host diagnostic 3a1597eec used /bin/false, which does not exist on
macOS. It exercised launch failure, NOT child early exit: absent liveness
fields caused None-is-not-False assertion failure. Do not mislabel it as a
runtime-pipe defect reproduction. This diagnostic is retained unchanged.

Successor 05c54032d uses actual /usr/bin/false on macOS and Ubuntu. It
temporarily changes the executable supplied to real Popen, restoring it in
finally; no mock Popen/wait/reader/filesystem. The producer starts one child,
observes abnormal exit1, saves baseline_eof.json and SUMMARY.json only,
returns1/STOP_FIRST_UNEXPECTED_CELL, starts none of the other three cells.
Test checks child PID, cleanup exit1/cleanup faults[], and child+reader no
longer alive after cleanup. Before-cleanup observations are separate fields;
never infer live-child formal semantics from cleanup observations.

Host whole package suite 9 PASS, 0.572s. Owned isolated Docker
f03-runtime-stop-v1: 9 PASS, 0.584s, python3 -B -O -W error.
2026-10-03T23:30:52.483851409Z–23:30:53.369398139Z,
exit0/noOOM. Image sha256:560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b.
Host/guest/container archive SHA256 matched
2603d4415cea34d810f053ab1422f13d2e0924cbf288ba795bbf591de721ecfb.
Network none; root/input read-only; tmpfs; UID501;
configured CPU1/memory1GiB/swap0/pids128 (no empirical cgroup read this run).

PASS_CONSTRUCTION_ONLY. This verifies actual early child exit and first-cell
STOP orchestration, not a live-child malformed handshake or normal-case
formal comparison. Formal native0/official auditor0/model0. Temporary output
is test-asserted, not separately exported/hash-anchored. Existing consumed
formal runs never replayed. Repository-wide tests not run. Source/execution
freeze, original/export receipt custody and independent prelaunch review
remain mandatory before new formal execution.
