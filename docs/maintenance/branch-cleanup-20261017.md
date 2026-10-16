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

## Ambiguous cleanup terminal identity

Removed the superseded branch `fix/8687-terminal-identity-completeness` after
checking its closed PR, current-main successor, primary-clone worktree registry
and retained PR source reference.

| Check | Evidence |
|---|---|
| Exact source tip before deletion | `c80db274e4e99ddaefee1aa500cfc8c53195e4cb` |
| Branch/PR state | Unprotected branch; [PR #8831](https://github.com/Unjuno/agent-interface/pull/8831) is closed and unmerged, with the exact tip as head. No open PR used the branch as head or base. |
| Current-main successor | The final PR comment says [PR #8771](https://github.com/Unjuno/agent-interface/pull/8771) supersedes this fix and includes the orphan-terminal case. PR #8771 is merged. Current main requires `accepted_ids == terminal_ids` and tests `test_unmatched_or_invalid_event_ids_fail_closed`. |
| Worktree / Issue references | No registered primary-clone worktree or exact Issue-body branch-name match was found. |
| Remote retention after deletion | `git ls-remote origin refs/pull/8831/head` returned the exact tip SHA after the branch ref disappeared. |
| Final verification | Remote `refs/heads/fix/8687-terminal-identity-completeness` absent; the closed PR head still points to the exact source tip. No test or experiment was run for this ref cleanup. |

No separate implementation or retry was needed; the merged successor and
closed PR preserve the behavior record and source history.

## Terminal health report duplicate

Removed the superseded child branch `fix/8816-terminal-report` after checking
its closed PR and merged parent successor.

| Check | Evidence |
|---|---|
| Exact source tip before deletion | `9808cec49c379a748e8bd802ef9220d97b5f3901` |
| Branch/PR state | Unprotected branch; [PR #8823](https://github.com/Unjuno/agent-interface/pull/8823) is closed and unmerged, with this exact head. No open PR used the branch as head or base. |
| Successor | Parent [PR #8816](https://github.com/Unjuno/agent-interface/pull/8816) is merged at head `88adef65f48874d681d5600f910ec009e6e662b1`. The #8823 close comment states the parent revision supersedes the child and includes the terminal-observation separation regression. |
| Worktree / Issue references | No registered primary-clone worktree or exact Issue-body branch-name match was found. |
| Remote retention after deletion | `git ls-remote origin refs/pull/8823/head` returned the exact tip SHA after the branch ref disappeared. |
| Final verification | Remote `refs/heads/fix/8816-terminal-report` absent; the closed PR head retains the source SHA. No source run or test was performed for this ref cleanup. |

The updated parent PR is the integrated path; the child branch name was
redundant.

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

## Retained Win32 release-tracking rescue branch

Keep `rescue/win32-release-retain-7772-currentmain-20261007` pending an
explicit resolution of the source proposal and its custody decision. Do not
delete or merge it based only on the presence of newer, similarly named tests
in main.

- Current branch tip is `0d05169be4f937e534aa6c2c6abd6027d87c12ec`; the branch
  exists remotely. It has no open PR of its own. The direct source proposal is
  closed unmerged [PR #7169](https://github.com/Unjuno/agent-interface/pull/7169),
  whose retained head is `bee11a6ac5cd67c13515a21edf7cc91766de2ecd`.
- The PR proposed five regressions for retaining Win32 input tracking across
  healthy, persistent, eventually-cleared, query-exception and send-exception
  cases. Its proposal explicitly required distinct nonauthor agreement and
  current-tree qualification; closure without merge does not establish either.
- The earlier #672 custody note explicitly said to preserve this rescue branch
  until its unique test coverage was proven elsewhere. Current main has newer
  release-ledger tests, including query/send exception preservation and
  persistent-down behavior, but the original test entry and all five named
  cases were not established as a complete equivalent port in this review.
  Similar behavior is not enough to overturn the explicit preserve decision.
- No deletion or source execution was performed. Revisit only after recording
  an evidence-backed coverage mapping and resolving the original proposal's
  governance/custody conditions.

## Main-merged terminal fixes and A07 correction source

Removed three redundant remote branch names after checking their exact tips,
PR destinations, retained source refs and worktree state. The operation removed
remote refs only; the two attached local fix worktrees and the A03 source
worktree remain intact.

| Branch | Exact tip | PR and preservation evidence | Final state |
|---|---|---|---|
| `fix/doom-terminal-health-zero-a16` | `88adef65f48874d681d5600f910ec009e6e662b1` | Merged [PR #8816](https://github.com/Unjuno/agent-interface/pull/8816) at the exact head; main comparison reported zero commits ahead. Its local worktree remains at `/Users/taka/Documents/Codex/2026-10-09/agent-interface-59-live-threat-guard-a01/results-local/doom/a16-health-zero-terminal-fix`. | Remote branch absent; pull-request head ref retains the tip. |
| `fix/59-cleanup-lease-aware-terminal-receipt-a01-20261009` | `a0acd7e96032cd3d9cf0e5ae86b20140d9abca3f` | Merged [PR #8763](https://github.com/Unjuno/agent-interface/pull/8763) at the exact head; main comparison reported zero commits ahead. Its local worktree remains at `/Users/taka/Documents/Codex/2026-10-09/agent-interface-59-live-threat-guard-a01/results-local/doom/a10-cleanup-fix`. | Remote branch absent; pull-request head ref retains the tip. |
| `research/59-a07-audit-v3-correction-20261009` | `29143d84d7e0e5288f7bc316a1a4f8b77967068c` | [PR #8707](https://github.com/Unjuno/agent-interface/pull/8707) merged to `research/59-live-threat-guard-a03-20261009` at `ce6724b870696916d8d421e20d9bcd18362af88c`, not to main. The current A03 tip `44f15471bd07705f1bbe565c017b6f9df29e87ec` contains that merge commit; comparison reported zero commits ahead. The A03 worktree at `/Users/taka/Documents/Codex/2026-10-09/agent-interface-59-live-threat-guard-a01/results-local/doom/a03-source` remains. | Redundant A07 remote branch absent; `refs/pull/8707/head` still equals the exact tip. |

No experiment or test was run for these ref removals. In particular, the A07
correction package remains available through the retained A03 branch and pull
request ref; this receipt does not claim that it is present on main.

## Closed superseded PR branches

Removed these nine remote branch names after rechecking that each exact tip
was the head of a closed, unmerged PR, no branch was protected, no registered
worktree or open PR referenced the branch as head/base, and the closed PR head
ref still retained the exact tip. Successor/retention evidence was checked in
the PR close discussion and merged successor where applicable. Remote branch
deletion does not remove the PR or its retained head ref.

| Branch | Exact tip / closed PR | Disposition and retained path |
|---|---|---|
| `fix/8252-held-modifier-current-main` | `db73d5c87fa3503d5b403d93f4822918b5f7b9cb` / [#8296](https://github.com/Unjuno/agent-interface/pull/8296) | Explicitly withdrawn; closed PR head remains the source record. |
| `research/59-current-main-a12-20261009` | `320d39b6d8f495c78e4863d15a747ce54eed17ed` / [#8812](https://github.com/Unjuno/agent-interface/pull/8812) | Superseded by merged [#8967](https://github.com/Unjuno/agent-interface/pull/8967), which preserves all 48 source files; PR head retains this exact tip. |
| `research/59-currentmain-guard-boundary-a01-20261009` | `5d195dad8750a02a4f6597c76251127680893134` / [#8801](https://github.com/Unjuno/agent-interface/pull/8801) | Superseded by merged [#8933](https://github.com/Unjuno/agent-interface/pull/8933), with original source/raw/audit and follow-up additions preserved. |
| `research/59-hard-recovery-pending-a01-20261009` | `e27c0b43625bbe986b8363c448e52abdb20ebc10` / [#8792](https://github.com/Unjuno/agent-interface/pull/8792) | Converged through merged [#8988](https://github.com/Unjuno/agent-interface/pull/8988); original files are retained there. |
| `research/59-v39-health-guard-boundary-a01-currentmain-pr-20261009` | `1fcb9e6332cd02f62481b7abb606defac6756e59` / [#8814](https://github.com/Unjuno/agent-interface/pull/8814) | Superseded by merged #8933; exact PR head retained. |
| `research/59-v39-visual-active-hold-xvfb-a01-20261012` | `0aca0e31216659a44f285b62db3edb3b5eb228b9` / [#8876](https://github.com/Unjuno/agent-interface/pull/8876) | Superseded by merged [#8994](https://github.com/Unjuno/agent-interface/pull/8994), whose records preserve all 614 changed-path head blobs and seven dependencies. |
| `research/8681-cleanup-identity-a03-malformed-events` | `31e1b6372b3e7ebe24b5dfb57f6aa1dd01a55931` / [#8850](https://github.com/Unjuno/agent-interface/pull/8850) | Redundant after merged [#8771](https://github.com/Unjuno/agent-interface/pull/8771); exact PR head retained. |
| `research/8681-malformed-cleanup-identity-a01-20261012` | `6dd3086e93854231b9b2e06e337e308bcc847030` / [#8852](https://github.com/Unjuno/agent-interface/pull/8852) | Redundant after merged #8771; exact PR head retained. |
| `research/issue59-v39-configured-mcp-disable-20261011` | `cf399788e32d1430fa233c7ac41deb83a2711d67` / [#8839](https://github.com/Unjuno/agent-interface/pull/8839) | Superseded by merged [#8946](https://github.com/Unjuno/agent-interface/pull/8946), which retains the original proposal/tests. |

After deletion, all nine `refs/heads/*` names were absent and each
`refs/pull/<number>/head` still resolved to the exact SHA in the table. No
source or experiment was run for this remote-ref cleanup.
