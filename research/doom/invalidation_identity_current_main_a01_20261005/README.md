# V39 invalidation identity: current-main integration replay

This A01 replay checks whether the open #7963/#8031 invalidation identity repair composes with the current `main` snapshot. Its hypothesis, decision rule, source refs, runtime, controls, and limitations are frozen in `FREEZE.json` before the WSLc test run.

The exact input was current `main` `5db548aa351c8ccd351831485d5e5940a4967ff3` merged with PR #8031 head `bbdede97bf0ccfc1c3a0b6454422b402e8cf0b6f`. `git merge-tree --write-tree` returned `74e24a812f6ffa2bf9a79b310ae76eb9070eb44b`; the local merge index was independently checked against that tree. Four exact candidate implementation/test snapshots are retained under `source_snapshot/`, with both SHA-256 and Git blob identities recorded in `FREEZE.json`. The runner freezes those values before invocation, runs focused and adjacent suites in separate WSLc containers with network disabled and the repository mounted read-only, and retains raw stdout/stderr plus the sanitized argv, an executed-argv SHA-256, exit codes, and output hashes. The machine-specific mount path is replaced with `<repo>` in the publishable receipts. `audit_replay.py` records the initial merged-worktree audit; `audit_snapshot_v2.py` independently rechecks the immutable snapshots and raw logs from this evidence package. The post-redaction report is `audit-snapshot-v2-final.json`.

H: preserving the monitor's originating observation identity allows its health-only invalidation to cross the matched-frame barrier on current main without weakening stale-frame, pointer-binding, or RGB checks.

T: replay the exact merge tree in cached WSLc Python 3.12.14, run 16 focused tests and 40 adjacent tests, then audit the retained outputs independently.

D: pass only when the merge tree, four source hashes, test counts, exit codes, and independent log audit match the frozen decision rule.

C: all schedules use synthetic readers, images, queues, and process/executor fakes. PR #8031's own report states that its controller schedule delivers invalidation after model completion; this replay does not measure pending-model timing.

U: this is code-level integration evidence only. It does not test live game/model/GUI/X11/OS input, physical release, threat exposure, useful-feedback onset, recovery benefit, or MAP01 progress. No live or formal allocation was used.

## Reproduction

The original run used a disposable worktree whose source index was the exact merge tree above. To repeat it without changing the published raw result, create another disposable worktree from the frozen main commit, merge the frozen PR head without committing, then check out only `FREEZE.json` and `run_replay.py` from evidence branch `research/59-invalidation-identity-current-main-a01` before running the script. The runner uses a write-once results directory, so use a fresh disposable copy of the package for a repeat. The recorded `results/current-main-a01/runs.json` contains the full WSLc argument vector for both test selections with `<repo>` replacing the local mount path. Run `audit_snapshot_v2.py` separately to verify the source snapshots and retained outputs without a merge worktree.
