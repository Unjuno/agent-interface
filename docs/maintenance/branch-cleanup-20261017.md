# Branch cleanup receipts — 2026-10-17

## V39 cancellation batch race

Removed the superseded remote branch
`research/v39-cancel-batch-race-a01-20261009` after checking its current refs,
worktree registration, protection, successor code and retained provenance.

| Check | Evidence |
|---|---|
| Exact source tip before deletion | `1c1eedfabb82b02419878b5b84c4ad15088b3210` |
| Branch state | Unprotected; branch ref pointed to the exact tip above. |
| Worktree / Issue references | No registered worktree in the primary clone and no Issue title/body match for the exact branch name. |
| Pull request state | [PR #8688](https://github.com/Unjuno/agent-interface/pull/8688) is closed, unmerged, and its head is the exact tip above. The PR comment says its fallback is included in [merged PR #8691](https://github.com/Unjuno/agent-interface/pull/8691), with no unique retained result. |
| Successor evidence | Current `main` contains the corresponding backend cancellation handling and regression tests, including `test_verified_empty_owner_cancel_maps_race_to_cancelled_and_keeps_unknown_receipt` and `test_without_verified_cancel_preserves_original_failure`. The later-main tree adds `test_cancelled_pending_disposition_survives_later_step_failure`. |
| Remote retention after deletion | `git ls-remote origin refs/pull/8688/head` still returned the exact tip SHA after the branch ref disappeared. The closed PR therefore retains a direct fetchable source ref. |
| Workflow side effects | No workflow declares a `delete` event. A tag was not pushed because unfiltered push workflows could run for a tag push. |
| Final verification | Remote `refs/heads/research/v39-cancel-batch-race-a01-20261009` absent; `refs/pull/8688/head` still equals the original tip. No experiment or test was run for this ref cleanup. |

The PR author's prior provenance preference is preserved through the closed PR
and its retained head ref. The deletion removed only the redundant branch name;
the exact source commit remains reachable for review and recovery.

## Owner release known-empty receipt

Removed the superseded remote branch
`fix/59-cleanup-owner-release-known-empty-a01-20261009` after verifying its
closed PR, merged successor, current-main behavior and retained provenance.

| Check | Evidence |
|---|---|
| Exact source tip before deletion | `3b426e665d6598357637ac39969d35e93399a946` |
| Branch state | Unprotected; branch ref pointed to the exact tip above. |
| Worktree / Issue / dependent PR references | No registered worktree in the primary clone, no Issue title/body match for the exact branch name, and no PR used this branch as its base. |
| Pull request state | [PR #8787](https://github.com/Unjuno/agent-interface/pull/8787) is closed and unmerged; its head is the exact tip. Its base is `fix/59-cleanup-lease-aware-terminal-receipt-a01-20261009`. |
| Successor evidence | [PR #8771](https://github.com/Unjuno/agent-interface/pull/8771) is merged. PR #8787's review comment says the five malformed present-token values and absent-token legacy control are covered by the successor. Current main explicitly requires `keys_unknown == []` and `key_state_errors == []` in the shared empty-release predicate. |
| Remote retention after deletion | `git ls-remote origin refs/pull/8787/head` returned the exact tip SHA after the branch ref disappeared. |
| Final verification | Remote `refs/heads/fix/59-cleanup-owner-release-known-empty-a01-20261009` absent; `refs/pull/8787/head` still equals the original tip. No experiment or test was run for this ref cleanup. |

The closed PR head retains the exact source commit for review and recovery; no
tag push or source rerun was needed.

## Cancelled pending-UP branch

Removed the superseded remote branch
`fix/59-v15-cancelled-up-batch-20261009` after verifying its closed PR,
successor composition, current-main implementation and retained source ref.

| Check | Evidence |
|---|---|
| Exact source tip before deletion | `1f5a0d98cc48daa4e7c8399ee3508692e924feb7` |
| Branch state | Unprotected; branch ref pointed to the exact tip above. |
| Worktree / Issue / dependent PR references | No registered worktree in the primary clone, no Issue title/body match for the exact branch name, and no PR used this branch as its base. |
| Pull request state | [PR #8684](https://github.com/Unjuno/agent-interface/pull/8684) is closed and unmerged; its head is the exact tip. The PR comment says its pending-UP guard was composed into merged [PR #8691](https://github.com/Unjuno/agent-interface/pull/8691). |
| Successor evidence | Current main retains `cancel_requested` handling, the `not_attempted_owner_cancel_release` disposition, and regression tests for both verified owner cancellation and the ordinary-failure control. |
| Remote retention after deletion | `git ls-remote origin refs/pull/8684/head` returned the exact tip SHA after the branch ref disappeared. |
| Final verification | Remote `refs/heads/fix/59-v15-cancelled-up-batch-20261009` absent; `refs/pull/8684/head` still equals the original tip. No experiment or test was run for this ref cleanup. |

The closed PR head retains the exact source commit for review and recovery; no
tag push or source rerun was needed.
