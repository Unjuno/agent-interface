# Issue #59 — workflow-path-global one-shot owner counterexample

## H / T / D / C / U

- **H:** The current owner guard does not enforce one-shot ownership globally for a versioned workflow/allocation: it filters matching runs by both workflow path and head_sha, so distinct commits on the same workflow path can each appear to be the sole canonical owner and both enter the formal step.
- **T:** Replay the exact current-main owner helper against the two distinct-head run IDs in the immutable live-03 invalidation record. Keep workflow path/allocation fixed. An independent invariant oracle counts formal admissions over the complete two-run set.
- **D:** Guard failure is reproduced if more than one of the distinct runs returns may_enter_formal_step=true; gate is adequate only with at most one admitted run across all heads. A single admitted run must pass; malformed/missing current run must remain fail-closed.
- **C:** This is an offline deterministic reconstruction of the owner-selection function using retained run metadata, not a new GitHub Actions race or duplicate formal execution. Both retained rows are completed, so the replay establishes a selector defect, not timing or a newly consumed MAP01 allocation.
- **U:** Does not test GitHub API pagination/eventual consistency, branch/ref gating, concurrency timing, Xvfb/VizDoom, release telemetry, game behavior, or #59 efficacy. It authorizes no live run.

## Frozen source and retained fixture

- Source main commit: 4b7fe7837e4ee8c0d035ebfbf52baf014f042295.
- Owner helper path: research/orchestration/o3-g6/launch-owner/formal_allocation_launch_owner_v1.py.
- Owner helper Git blob: 85658f40c0fb689993d5034909326fd2364485d6.
- Predecessor invalidation record: research/doom/results/map01-measurement-integration-live-03/invalidated-summary.json, blob 0292a415300336844d5c3f57c5466c68017affb8.
- Workflow path under test: .github/workflows/map01-measurement-integration-live-03.yml; the current workflow also queries runs using head_sha=$GITHUB_SHA before invoking the helper.

## Formal protocol

Construction checks validate the independent oracle. Freeze all files and verify the helper blob identity from its source commit. Run candidate.py once; retain exact stdout directly as candidate_output.json. Run auditor.py once on that immutable output; preserve any nonzero exit. No workflow dispatch, model, game, GUI, Docker container, external input, or network call is part of the formal candidate/audit execution.

## Repair constraints for a future separately reviewed workflow version

Treat the immutable versioned workflow path as the allocation-global key: query all runs for that workflow path without head_sha narrowing; select one canonical owner across differing heads; fail closed if pagination/visibility is incomplete; and explicitly require event=push plus ref=refs/heads/main before formal work. Keep non-cancelling workflow concurrency. Do not reuse live-03's consumed allocation or mutate its historical outputs.
