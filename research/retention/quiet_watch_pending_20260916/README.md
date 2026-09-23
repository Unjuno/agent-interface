# Prior quiet-watch evidence: publication reconciliation

Issue #214 uses and independently re-audits the previously uploaded conversation bundle `quiet_watch_pending_updates.tar.gz`, SHA-256 `682bbf5ac421cefcbe06f4697c22d043d42b59fb2178d1a9f2e5776adc4d02d7`.

The local short-cue task `QUIET-WINDOW-SHORT-CUE-PHASE-20260916-002` (120 cases, widths 2/5/8/10/20/80 ms, offsets 150..158 ms) is NOT the distinct GitHub-frozen #186 schedule. The local `QUIET-WATCH-ACK-LATCH-20260916-004` task (40 cases) is under `quiet_window_ack_latch_v1`, not a silent replacement for #200's namespace or first outcome. Preserve these identities.

In this response both unchanged raw-data audits passed (120 and 40 cases), and the nine original EventLatch protocol tests passed. The exact resulting audit JSONs, protocol test log and original latch.py are retained in `research/live_control/quiet_latch_restart_v1/prior_audits.json.xz.part00`; use that directory's manifest and reconstruct.py to recover them.

Previous measured results, newly rechecked: short-cue detections 3/15, 7/15, 12/15, 15/15, 15/15, 15/15 at 2/5/8/10/20/80 ms, with 23 misses; cooperative 2-ms warning detection 3/15 ephemeral versus 15/15 latched. These are previous experiments, NOT new measurements in #214.

RETENTION BOUNDARY: the earlier full 120/40-case raw GUI bundle and its patch remain conversation attachments, not newly uploaded GitHub raw evidence. The four-file prior audit archive does not replace those original raw files. Do not claim complete earlier raw retention on GitHub. This limitation does not apply to the new restart experiment, whose complete 200-file source/raw/database/failure archive is committed in this PR.

No earlier experiment has been rerun live, overwritten, relabelled or accepted as another worker's allocation. The previous bundle remains available to the user as `quiet_watch_pending_updates.tar.gz`; its hash above identifies the exact bytes required for full prior reconstruction.
