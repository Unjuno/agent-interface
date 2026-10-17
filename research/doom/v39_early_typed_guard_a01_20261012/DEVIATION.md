# Deviations and retained first outcomes

- Attempt 1 was rejected before candidate execution because an invalid `rw` field was supplied for a WSLc bind mount. The exact argv, CLI output and exit code are retained under `out/attempt1_cli_rejected/`; the corrected invocation uses the default writable output mount.
- Candidate v1 ran once: two assertions passed and two failed because the test expected invalidation to advance `last_pair_sequence` and expected a same-kind duplicate to use the cross-transport conflict reason. Those assumptions were wrong; the implementation preserves coherent-pair custody until matching artifact observation and classifies same-kind replays as nonadvancing.
- Candidate v2 ran once: three assertions passed and one failed on the same coherent-pair assumption for a soft typed-only event. The raw result is preserved.
- Candidate v3 explicitly checks that typed soft evidence preserves policy without advancing coherent-pair sequence, then an exact matching artifact observation confirms the pair and permits recovery without an extra wait.
- WSLc warned that swap limits are unavailable / cgroup is not mounted. The test requested 512 MB but makes no claim that memory or swap was enforced.
- No real model, game, image capture, Doom process, Executor, owner thread, OS input, physical input, task effect, or live allocation was used. This result is a monitor-boundary construction only.

- Supplementary checked-out-worktree regression: 37 tests passed, but test fixture modules differ from current main; do not call this a current-main suite pass. Exact production monitor and guard blobs are separately pinned and exercised by candidate v3.
