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

## Fresh audit of unreferenced remote branches (2026-10-17)

Refreshed GitHub state returned 564 remote branches and 521 open PRs. Comparing
open PR head/base names with the 66 registered worktrees leaves 29 branches
outside those references. All 29 are unprotected. This is an inventory, not a
deletion list: absence from open PRs and worktrees does not establish that a
branch's source or one-shot evidence is redundant.

All 29 exact tips were fetched into local audit refs and compared with current
`main` at `1ece47014d05db898bf73afcd722a14524462e15`. None is an ancestor of
main. Each has 1–20 branch-only commits and a merge-base diff of 1–585 paths.
They are not removable as already-main duplicates. Deletion would require a
per-branch Issue/allocation mapping and an independently retained source path
for its delta; that custody step remains open for the candidates without exact
closed-PR head refs.

Eight branches exactly match closed PR heads. Their exact tips and linked PRs
were read back. These are retained because their PR discussions preserve
unique failures, stacked source lineage, or an explicit branch/evidence
retention decision; closure of an integration PR does not erase that record.

| Branch | Exact tip | PR-specific retention evidence |
|---|---|---|
| `research/59-renewal-soft-stale-admission-a01-20261005` | `66ba74f69d1373399811f62ad950743caad770ed` | Closed [#8006](https://github.com/Unjuno/agent-interface/pull/8006) says the branch and original evidence remain available for provenance; review found a caller-transition coverage gap. |
| `research/59-v39-current-admission-fix-a01-20261005` | `1403c822609395f9ab21e0cdbb36b7b4c8ee044d` | Closed [#7904](https://github.com/Unjuno/agent-interface/pull/7904) has unresolved renewal-path review history and is the recorded base of stacked #8013. |
| `research/59-v39-keymap-batch-a06-20261005` | `0a43cd9528c1de28af389945c8ce31b3e33e8bf5` | Closed [#7908](https://github.com/Unjuno/agent-interface/pull/7908) explicitly retains the distinct dropped-key-up failure and post-hoc reconciliation. |
| `research/59-v39-renewal-invalidation-a01-20261005` | `fc3d88686ef17d3d9b721592eb64d862890cff8b` | Closed [#8013](https://github.com/Unjuno/agent-interface/pull/8013) is a stacked follow-up to #7904; retain the exact parent/child source lineage. |
| `research/8651-observation-response-factorial-a01-20261009` | `1910f60b3f4aa8699cb7640a549732e58e4375e3` | Closed [#8655](https://github.com/Unjuno/agent-interface/pull/8655) preserves the pre-row output-path STOP; merged #8660 superseded integration, not the historical outcome. |
| `research/8651-observation-response-factorial-a02-20261009` | `f5a4e7563862734c0e57b21cda66ddbe230e1ab6` | Closed [#8656](https://github.com/Unjuno/agent-interface/pull/8656) preserves the candidate/auditor output and `ARG_MAX` retention failure; no scientific contrast was asserted. |
| `research/8651-observation-response-factorial-a03-20261009` | `d7022f5c2a5c9535a66519f70e1b12e5090163cf` | Closed [#8657](https://github.com/Unjuno/agent-interface/pull/8657) preserves the checksum-preflight STOP before image pull or candidate invocation. |
| `research/v39-import-preflight-a01-20261009` | `1d7cc0e13f18484260012f2c487e86679bd8b534` | Closed [#8697](https://github.com/Unjuno/agent-interface/pull/8697) explicitly retains the branch and local reproduction artifact; its narrow Pillow preflight was superseded by broader preparation. |

At that census snapshot, the remaining 21 were retained pending specific custody resolution. The unique
frozen package `fix/8243-verifier-r2p6-20261006` and the explicit preservation
decision for `rescue/win32-release-retain-7772-currentmain-20261007` are recorded
above. `research/v39-retained-trajectory-posthoc-a01-20261008` differs from
closed PR #8543's head, so that PR does not establish custody for the current
branch tip. The other 18 have no exact closed-PR head mapping in the refreshed
inventory. Their allocation/source contents and retained evidence destinations
have not yet been reconciled.

| Branch | Current exact tip |
|---|---|
| `fix/8243-verifier-r2p6-20261006` | `44f4d99480344e50f504fe5c92f5f2cd58c5dec1` |
| `rescue/win32-release-retain-7772-currentmain-20261007` | `0d05169be4f937e534aa6c2c6abd6027d87c12ec` |
| `research/1998-temporal-focus-payload-a10-20261009` | `86ee215887a61c5ee014db4e3dc2000ade10746e` |
| `research/59-early-typed-guard-a01-20261012` | `075aa109c9464a8fcd1b81a35700b231bfda37bc` |
| `research/59-v15-owner-integration-20261012` | `cf3c31e02e5d9b25240474499b1ec4393849b593` |
| `research/59-v39-main-source-identity-a01-20261009` | `0d0f4d4a09e3b6de5b009ac315a3e57e888b195a` |
| `research/59-v39-v15-cleanup-a05-current-main-20261005` | `4ede220fc567e74d4d7432b6eda3ade7652d8550` |
| `research/59-xvfb-audit-v3-a02-20261005` | `1ec6556ba8568de289625b5f167e7b8c21e1f72c` |
| `research/8553-observation-branch-a02-20261009` | `5c386c316dd5a26629f2a8bcecd058efed939ca7` |
| `research/8581-feedback-artifact-bypass-t0-20261009` | `5c80abe8dc51e7a8ab5e42384fdce0066aca12a0` |
| `research/8592-dpor-t0-a01-20261008` | `b0951ae1a8cfd5befbb6988935dd4d931f595fb2` |
| `research/8592-dpor-t0-a02-20261008-r1` | `bb19587730eab16061bfe4dcd1188137140f2c04` |
| `research/8596-chance-bounded-progress-t0-a01-20261009` | `2ecf498101453ce52869cdfb5d643bb7d2b19991` |
| `research/8638-split-control-voi-a01-20261008` | `16d846740645a338ea11ac70c8e4e931b71f1408` |
| `research/8648-hysteresis-c01-20261009` | `4ce63dfedcdef07d1763147dfc2575fc46077aa1` |
| `research/8654-c06-stochastic-support-20261009` | `7f8bab0b6eece49bb5dfedb9598d3c48b30fb725` |
| `research/carbon-window-7794-a05-bytebound-recheck-20261008` | `0b5af59e7ec4333f5c8f615176180e14229fb70d` |
| `research/held-chord-h7k3-20261007` | `f150937577c3b84c5ab61e82cd0b920fedc3900d` |
| `research/issue59-two-key-dual-release-a12-20261008-codex` | `4e84fc655c634267d9ec818b8a3b31b216cce99c` |
| `research/predictive-display-t0-5935-20261006-v1` | `b4e108c52497018f5722f2e9b96feed3d9b9ded7` |
| `research/v39-retained-trajectory-posthoc-a01-20261008` | `87f2dab936bff72c9906126884141925a20fc547` |

No remote branch was deleted during this refresh. Revisit each retained candidate
only after matching its exact current tip to its Issue/allocation and verifying
an independently fetchable source/evidence path or a complete integrated
successor.

## Retired A01 branch after exact successor-custody verification

Removed `research/8596-chance-bounded-progress-t0-a01-20261009` with an exact
tip lease after establishing that its complete A01 source was already carried
by the open successor PR.

| Check | Evidence |
|---|---|
| Exact branch tip before deletion | `2ecf498101453ce52869cdfb5d643bb7d2b19991` |
| Branch state | Unprotected; no open PR used the branch as head or base, and no registered worktree used it. The branch ref matched the expected SHA immediately before deletion. |
| Successor custody | Open [PR #8721](https://github.com/Unjuno/agent-interface/pull/8721) head `e78551d4ec48da1c247141514456aafb7dedfb83` descends from the exact A01 tip. All 11 paths in the A01 delta have identical blobs at that PR head. Its Issue record preserves A01's pre-formal invalidation and separately freezes A02. |
| Deletion method | Remote delete used `--force-with-lease` for the exact branch ref and expected SHA. |
| Final verification | `refs/heads/research/8596-chance-bounded-progress-t0-a01-20261009` is absent; `refs/pull/8721/head` remains at the verified successor SHA. Fresh inventory: 563 remote branches, 521 open PRs, 66 registered worktrees, 28 unreferenced candidates. |
| Scope | Branch-ref cleanup only; no experiment or candidate rerun was performed. |

This removes only a redundant branch name. The closed experimental history is
not changed, and the A01 source remains fetchable through the open successor PR.

## Retired byte-bound replay branch after merged-artifact verification

Removed `research/carbon-window-7794-a05-bytebound-recheck-20261008` after
verifying its full content delta is already preserved in current main and the
merged A05 publication PR.

| Check | Evidence |
|---|---|
| Exact branch tip before deletion | `0b5af59e7ec4333f5c8f615176180e14229fb70d` |
| Branch state | Unprotected; no open PR used the branch as head or base, and no registered worktree used it. The branch ref matched the expected SHA immediately before deletion. |
| Artifact custody | Against current main `1ece47014d05db898bf73afcd722a14524462e15`, all 20 delta-path blobs were found byte-identically: 16 in main (including six preparation files moved from `research/analysis/` to the published package) and four in merged [PR #8393](https://github.com/Unjuno/agent-interface/pull/8393)'s retained head (`research/README.md`, `REPORT.md`, `RUN.json`, `SHA256SUMS`). Merged [PR #8395](https://github.com/Unjuno/agent-interface/pull/8395) records the final scoped gate wording. |
| Deletion method | Remote delete used `--force-with-lease` for the exact branch ref and expected SHA. |
| Final verification | The branch ref is absent; `refs/pull/8393/head` and `refs/pull/8395/head` remain fetchable at their verified merge heads. Fresh inventory: 562 remote branches, 521 open PRs, 66 registered worktrees, 27 unreferenced candidates. |
| Scope | Branch-ref cleanup only; no candidate, auditor, model, or GUI run was performed. |

This retires the redundant branch name while retaining its exact source and
result bytes through main and the merged PR head.

## Targeted source-to-successor checks for remaining branches

The following comparisons found branch-only bytes or frozen source that are
not present in the proposed successor. These are retained evidence, not stale
merged branch names.

| Branch / issue | Exact-custody finding | Disposition |
|---|---|---|
| `research/1998-temporal-focus-payload-a10-20261009` / [#1998](https://github.com/Unjuno/agent-interface/issues/1998) | Full 537-path delta mapped: 483 A04 blobs plus the changed analysis README are byte-identical in open [#8794](https://github.com/Unjuno/agent-interface/pull/8794) and stacked [#8798](https://github.com/Unjuno/agent-interface/pull/8798); 26 A09 and 27 A10 blobs were absent from main and those PR heads. The A09 and A10 directories are now copied byte-for-byte at their original research paths in PR #9012; all 26 A09 output checksums pass. A09 is `FAIL_NO_CROP_TOKEN`; A10 remains pre-launch at candidate/auditor 0/0. | After #9012 merges, recheck the exact remote tip `86ee215887a61c5ee014db4e3dc2000ade10746e` and branch references, then retire this redundant source branch. The distinct A04 source remains retained by #8794/#8798. |
| `research/8553-observation-branch-a02-20261009` / [#8553](https://github.com/Unjuno/agent-interface/issues/8553) | Seven of the 12 changed-path blobs are absent from current main and open audit-only successor [#8824](https://github.com/Unjuno/agent-interface/pull/8824). | Keep A02 freeze, protocol, and construction provenance. |
| `research/8592-dpor-t0-a01-20261008` and `research/8592-dpor-t0-a02-20261008-r1` / [#8592](https://github.com/Unjuno/agent-interface/issues/8592) | Five A01 and six A02 source blobs are absent from current main and merged [#8602](https://github.com/Unjuno/agent-interface/pull/8602). The Issue says each allocation's stopped outcome remains in its immutable branch history and report. | Keep both distinct first-outcome records. |
| `research/8638-split-control-voi-a01-20261008` / [#8638](https://github.com/Unjuno/agent-interface/issues/8638) | Its sole A01 `experiment.mjs` blob is absent from current main and the distinct open A02 result [#8740](https://github.com/Unjuno/agent-interface/pull/8740). | Keep A01 source separate from A02. |
| `research/8654-c06-stochastic-support-20261009` / [#8654](https://github.com/Unjuno/agent-interface/issues/8654) | Eleven C06 source/report/raw-manifest blobs are absent from current main and merged C07 audit [#8671](https://github.com/Unjuno/agent-interface/pull/8671). C07 preserves C06 input shards but does not rewrite the C06 failure. | Keep the first failed auditor record and unique package files. |
| `research/held-chord-h7k3-20261007` / [#8252](https://github.com/Unjuno/agent-interface/issues/8252) | Ten of 15 changed-path blobs are absent from current main and merged production repair [#8308](https://github.com/Unjuno/agent-interface/pull/8308); that PR does not contain this branch's frozen comparison package. | Keep the experiment source and freeze. |
| `research/predictive-display-t0-5935-20261006-v1` / [#5935](https://github.com/Unjuno/agent-interface/issues/5935) | The Issue says this branch contains only duplicate preformal PLAN/INPUT/ENV/FREEZE metadata, with zero formal rows; canonical T0 evidence is elsewhere. FREEZE also names three source files absent from the branch tree. | Byte-identical metadata and the four-commit patch are archived in `docs/maintenance/archives/predictive-display-5935-duplicate-preformal-20261006/` in PR #9012. Retire the source branch only after that archive merges and the exact remote tip is rechecked. |
