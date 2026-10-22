# Isolated prestarted-supervisor Xvfb run 39620978807

## Frozen execution

- GitHub Actions run: `39620978807`; isolated job: `prestarted-cancel-xvfb`.
- PR #9315 head: `a5e72673e0b0ae79a9ba88adbb32a8e2b167fa68`.
- The raw receipt's `GITHUB_SHA` is `32aca662efc8103c863988d39dd963a96dc178d1`, the workflow merge ref, not the PR head.
- Ubuntu 26.04, Python 3.12.15, Xvfb 2:21.1.22-1ubuntu1.3.
- All downloaded run artifacts are retained byte-for-byte here. `SHA256SUMS` covers every retained file except the README and manifest themselves.

## Outcome

This attempt reproduces the rejected `owner_generation.child_pid` predicate from run 39620589667. The operation entered cancellation with child PID 2481 and an observed 1 ms event-loop heartbeat (9 samples; maximum gap 1.565791 ms). The owner retired with exit code -15. The cancellation call completed in 15.046108 ms as `UNKNOWN`; release remained unconfirmed, `task_success` remained null, replay was denied, the held-key obligation remained present in the receipt, and independent release readback and task oracle were absent. No XRes-confirmed disconnect or release result can be inferred.

The sibling `x11-integration` job succeeded, while the isolated supervisor job failed. Keep these outcomes distinct. The heartbeat shows that the event loop remained responsive in this trial; it does not explain or validate the supervisor cleanup request.

## Relation to source repair

This run used pushed PR head `a5e72673`; it predates the local PID-source correction now in the working tree. That correction uses the parent's retained `Process.pid` for both PID fields, preventing a post-retirement snapshot from dropping `child_pid`. The four focused Fake X modules, including its PID-source regression, pass 108/108 in normal and optimized Python on the current working tree; see the reproducible [R08 packet](../r08/README.md). A new isolated Xvfb composition on the corrected source is still required to verify the actual request and all later effect/readback stages.

This is a separate consumed attempt, not a rerun or replacement of earlier outcomes. It is not WSLc, MAP01, blocked-server release, task-success, reliability, or matched-efficiency evidence.
