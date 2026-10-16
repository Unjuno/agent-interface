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

## Superseded compiled callback custody proposal

Removed the unprotected remote branch
`fix/compiled-callback-custody-01a0ff35-20261003` after confirming that its
closed proposal is superseded by integrated current-main work and its exact
source remains retained by the closed PR head.

| Check | Evidence |
|---|---|
| Exact source tip before deletion | `b332fddcd1372e0cbba07c50691c215b20bd5831` |
| Branch/PR state | Branch was unprotected; [PR #6934](https://github.com/Unjuno/agent-interface/pull/6934) is closed, unmerged, and its head was the exact tip. No open PR used this branch as head or base. |
| Current disposition | The final PR comment says the proposal is superseded by integrated current-main work, with remaining safety residue tracked in #8965. It states all 184 original evidence paths are exact Git-blob matches in main and warns that merging the old whole tree would regress newer behavior. |
| Unique old tests | The old tip also contains `runtime/backends/win32_v1/test_release_custody.py` and `test_session_custody.py`, whose paths are absent from current main. Current main has the consolidated `test_release_ledger.py`, `test_explicit_up_ledger.py`, `test_unknown_release_custody.py`, and `test_integration.py` suites. The exact old tests remain fetchable from `refs/pull/6934/head`; this cleanup does not claim a line-for-line test port. |
| Worktree / local checkout | No matching worktree registration or checkout path was found in the inspected primary clone, `/private/tmp`, or the Codex workspace directories. |
| Remote retention after deletion | `git ls-remote origin refs/pull/6934/head` returned the exact tip SHA after the branch ref disappeared. |
| Final verification | Remote `refs/heads/fix/compiled-callback-custody-01a0ff35-20261003` absent; closed PR head retains the original SHA. No source run or test was performed for this ref cleanup. |

The old whole branch is not a current-main candidate. Its PR head preserves
the exact commit and historical tests while the redundant remote branch name
is removed.

## Compiled callback receipt handling

Removed the superseded remote branch
`fix/57-compiled-effect-verifier-receipt-20261005` after verifying that its
closed PR changes were integrated through a merged successor and its source
files remain pinned in current main.

| Check | Evidence |
|---|---|
| Exact source tip before deletion | `f18c378f1eef3f48ea10207e17eb7f184bb5d8a5` |
| Branch/PR state | Unprotected branch; [PR #7954](https://github.com/Unjuno/agent-interface/pull/7954) is closed and unmerged with the exact tip as head. No open PR used it as head or base. |
| Successor | [PR #8985](https://github.com/Unjuno/agent-interface/pull/8985) is merged at `d6121c641ac1e56377e0ebb4bff6fb88d2d66833`. |
| Evidence custody | Current main contains `research/integration/compiled_callback_convergence_20261016/PR7954_ORIGINAL_FILES.json`, which binds the six original file blobs, and `PR7954_SNAPSHOT.json`, which preserves the original PR body and comments. The six source snapshots are present under `original-pr/`. |
| Worktree / local checkout | No matching registration in the primary clone and no matching directory in the inspected temporary or Codex workspace paths. |
| Remote retention after deletion | `git ls-remote origin refs/pull/7954/head` returned the exact tip SHA after the branch ref disappeared. |
| Final verification | Remote `refs/heads/fix/57-compiled-effect-verifier-receipt-20261005` absent; the closed PR head still points to the source tip. No source run or test was performed for this ref cleanup. |

The merge successor and pinned source archive remain the current integration
and provenance paths; the branch name was redundant.

## Reviewed and retained: #8243 verifier freeze

The branch `fix/8243-verifier-r2p6-20261006` remains because it is an Issue/PR-
cited, unique pre-execution source package, not an obsolete implementation
branch ready for deletion.

- Exact current tip: `44f4d99480344e50f504fe5c92f5f2cd58c5dec1`; unprotected and
  not an ancestor of current main. The one-commit delta adds eight files under
  `research/live_control/validation_r2p6/`, including the freeze, protocol,
  verifier and four literal source fragments; that package path is absent from
  main.
- Merged [PR #8243](https://github.com/Unjuno/agent-interface/pull/8243)
  comment [#6016739963](https://github.com/Unjuno/agent-interface/pull/8243#issuecomment-6016739963)
  names the exact branch and SHA as the frozen source. The follow-up
  [comment #6016757229](https://github.com/Unjuno/agent-interface/pull/8243#issuecomment-6016757229)
  records one 80-subprocess engineering matrix and a separate raw audit,
  with the original unqualified claim explicitly withdrawn. This is not a
  live/runtime result and must not be promoted beyond that scope.
- No head PR, base PR, or registered primary-clone worktree references this
  branch. The Issue/PR freeze and the unique source package are sufficient
  custody reasons to retain it; no deletion or rerun was performed.

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
