# V39 soft-stale renewal regression

## Result

**PASS — local code-level regression only.** A soft observation may arrive after the controller chooses an expected observation sequence but before the renewal admission response. If the executor then returns its exact stale-sequence rejection, V39 now records that renewal as not admitted, preserves the preceding terminal, and continues the pending planner turn without cancelling or waiting for a terminal from the rejected renewal. While no cover is active, observations continue to be monitored; a policy or running-action invalidation interrupts the planner.

Unexpected renewal rejections still fail closed. Accepted renewals retain their existing path.

## Evidence

- The 4-case focused suite fails against the exact parent source at `9234613a2396040eb5352318e50b06a2467d432e` (RED; four missing-function failures) and passes 4/4 against the candidate in normal and optimized Python (`-O`). Logs are in `results/red.txt`, `results/green-normal.txt`, and `results/green-optimized.txt`.
- `py_compile` and `git diff --check` passed; captured in `results/compile.txt` and `results/diff-check.txt`.
- The existing V39 integration test could not import because Pillow is absent in this environment. The precise import failure is retained in `results/legacy-import.txt`; no integration-suite PASS is claimed.
- No game, model, GUI, executor session, formal candidate/auditor, or live input was run. The private execution lane remains unassigned. This package does not establish real-time task effect, release correctness, reaction latency, or overall computer-control success.

## Reproduction

From the repository root:

```sh
python -m unittest research.doom.test_v39_soft_stale_renewal_v1
python -O -m unittest research.doom.test_v39_soft_stale_renewal_v1
python -m py_compile research/doom/map01_overlap_controller_v39.py research/doom/test_v39_soft_stale_renewal_v1.py
git diff --check
```

The RED command used `V39_CONTROLLER_SOURCE` pointing to the parent controller snapshot in `results/base_controller.py`.

## Scope and limitations

This is a narrow admission-race fix stacked on PR #7930. It does not resolve the Issue #59 live control goal. In particular, actual threat exposure, policy stop/alter/escalate behavior under gameplay, damage/ammo/progress/outcome, verified release, reaction-time bounds, and the separately labeled MAP01 attempt still require an assigned private lane and end-to-end evidence.
