# Issue #59 — cross-head allocation-owner counterexample

**Disposition: FAIL_GUARD_NOT_WORKFLOW_PATH_GLOBAL.** The current helper admits both retained runs as canonical owners for one fixed versioned workflow/allocation.

## H / T / D / C / U

- **H:** The owner selector's path-plus-head key permits duplicate formal entry when the same versioned workflow is run from distinct heads.
- **T:** Replay current-main owner-helper blob 85658f40c0fb689993d5034909326fd2364485d6 at source commit 4b7fe7837e4ee8c0d035ebfbf52baf014f042295 against the two run IDs and head SHAs in the immutable live-03 invalidation record. A separate oracle enforces at most one admitted run across the fixed workflow path/allocation.
- **D:** Candidate returned PASS_CANONICAL_OWNER and may_enter_formal_step=true for both IDs. Independent oracle returned FAIL_GUARD_NOT_WORKFLOW_PATH_GLOBAL, error multiple-runs-admitted-for-one-versioned-allocation. Existing 10 helper tests pass; they do not cover same-path, distinct-head ownership.
- **C:** This is a deterministic offline replay of the selector on retained completed-run metadata; it does not create a new race or MAP01 execution. The retained run summary provides ID/head but not run_number; the replay gives distinct synthetic rank placeholders, which cannot affect selection because the current code partitions each SHA into a one-row matching set.
- **U:** No workflow dispatch, current-run API race, pagination, main-ref filter, live VizDoom, X11, release telemetry, task efficacy, or MAP01 outcome was tested. This does not establish a live controller result and does not authorize reuse of live-03.

## Direct workflow evidence

The current live-03 workflow fetches runs using event=push&head_sha=$GITHUB_SHA, then passes those rows to the helper. The helper itself also filters by exact workflow path and head SHA. Thus the two retained runs on different heads each see a singleton owner set. The invalidation record independently shows both runs entered the formal step under the same allocation ID and marks it FAIL_DUPLICATE_FORMAL_EXECUTION.

This confirms the root cause and supplies a small deterministic regression case. It is not merely an assertion that concurrency serialization alone will solve the problem: sequential runs from different heads are still admitted.

## Repair gate

A new, separately versioned workflow must query all runs for that workflow path without head-SHA narrowing and select one canonical owner across heads. It must fail closed on incomplete pagination or current-run invisibility and require event=push plus ref=refs/heads/main before formal work. Keep non-cancelling concurrency; do not change or reuse live-03.

## Environment / scope

This exact offline replay is a small pure-Python check over two JSON run rows. Docker Desktop was present but its shared inventory/API was unresponsive and no exclusive lease was assigned; no engine/container was inspected or touched. Host CPU used. No model, game, GUI, input, network request during candidate/audit, or external effect occurred.
