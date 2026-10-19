# Recent PR triage r01 — 2026-10-19

This bounded batch contains 15 PRs reviewed in a read-only audit and rechecked against live GitHub state at `2026-10-19T03:21Z`. It is a focused batch, not a representative sample of all 497 open PRs. The audit read exact diffs, recorded outcomes and check/review signals, and then refreshed each PR's state and head SHA. Before any merge, close, or ref cleanup, re-read the exact current diff and custody.

| PR | Current state at capture | Evidence / disposition | Next action |
|---|---|---|---|
| [#8701](https://github.com/Unjuno/agent-interface/pull/8701) | OPEN, head `44f15471` | A07 retained HOLD; report's tested-stack identity differs from the current PR head. | Reconcile exact tested commit and current stack lineage before deciding integration. |
| [#8678](https://github.com/Unjuno/agent-interface/pull/8678) | OPEN/Draft, head `75514240` | Distinct A01 STOP and A02 live outcome; cleanup failure and `formal_pass=false` are preserved. | Keep as evidence-only; retain #59 open and preserve the live-result limits. |
| [#9006](https://github.com/Unjuno/agent-interface/pull/9006) | OPEN/Draft, head `655a5bcd` | Win32 release-state tests; `native-win32` and `native-mcp` checks failed in the audited snapshot. | Author should repair/classify the release-verification fixture and distinguish unrelated native-MCP failures before readiness. |
| [#8842](https://github.com/Unjuno/agent-interface/pull/8842) | OPEN, head `80b81a53`, CONFLICTING | Broad multi-packet release/freshness/ammo/analysis change with later dated evidence than related PRs. | Reconcile stack and split/lineage before any integration. |
| [#8910](https://github.com/Unjuno/agent-interface/pull/8910) | MERGED | Bounded cover-diagnosability method result; no runtime or empirical sentinel claim. | Keep parent Issue #8909 open for its unresolved transfer question. |
| [#8906](https://github.com/Unjuno/agent-interface/pull/8906) | MERGED | WSLc host/process deviation disclosure; not a lane release or authorization for more WSLc use. | Keep Issue #8685's owner/lane gate visible; do not infer a new allocation. |
| [#8893](https://github.com/Unjuno/agent-interface/pull/8893) | MERGED | Bounded common-mode counterexample only; no real GUI/runtime claim. | Preserve Issue #8887's unresolved question. |
| [#8892](https://github.com/Unjuno/agent-interface/pull/8892) | MERGED | Preserves the original `FAIL_AUDIT_CONSTRUCTION`; not a scientific-result PASS. | Keep Issue #8879 open for the independent-oracle question. |
| [#8756](https://github.com/Unjuno/agent-interface/pull/8756) | OPEN/Draft, CONFLICTING | Scoped synthetic DIF result with postformal edit excluded and custody correction recorded. | Resolve base conflict and preserve the empirical-evidence limitation before readiness. |
| [#8853](https://github.com/Unjuno/agent-interface/pull/8853) | MERGED | A14 fake-client/source-level ammo-staleness construction; no model/game/OS input or task effect. | Keep the scoped construction boundary in the #59 family record. |
| [#8854](https://github.com/Unjuno/agent-interface/pull/8854) | MERGED | Synthetic soft-ammo boundary; no live model/input or MAP01 result. | Preserve as a separate scoped result under #59. |
| [#8855](https://github.com/Unjuno/agent-interface/pull/8855) | OPEN/Draft | Distinct soft/hard ammo construction; no task-effect claim. | Recheck exact stack and evidence, then the owner can decide whether it is ready. |
| [#8849](https://github.com/Unjuno/agent-interface/pull/8849) | OPEN/Draft | Synthetic soft-ammo feedback to fresh-action admission; no live task result. | Recheck exact stack/evidence and preserve the narrow scope before readiness. |
| [#8861](https://github.com/Unjuno/agent-interface/pull/8861) | OPEN/Draft | Prospective oracle-boundary patch; A04 remains `HOLD_UNCERTAIN`; no formal candidate/auditor run. | Keep separate from a scientific result; establish exact patch purpose and local validation before readiness. |
| [#8687](https://github.com/Unjuno/agent-interface/pull/8687) | OPEN, head `61956009` | Overlapping implementation was superseded by merged #8771, but the PR contains 47 unique A02–A05 packet files absent from current main. | `evidence-custody-hold`: preserve frozen packets and source/test provenance first; do not merge duplicate implementation or close/delete the ref yet. |

Six of these 15 PRs are merged and nine remain open. The merged PRs above resolve only their scoped implementation or evidence task; associated parent Issues remain open where noted. Open PRs have no bulk disposition: conflict, draft status, age, and missing review alone do not establish duplication or completion.

## Verified follow-up: #8687 custody

At main `3cf520498beb886750b9de8499890dfebb0ea209`, the current tree lacks all 47 A02–A05 package paths on #8687's exact head. The raw and frozen source/test hashes therefore remain recoverable from the open PR head, but are not yet in a canonical main-tree destination. The next finite step is an evidence-only preservation plan that retains each package byte-for-byte and makes every frozen source/test blob reproducible without re-running the candidate or auditor. Only after that destination is verified can #8687's overlapping implementation diff and remote branch be considered for closure/cleanup.

## Follow-up after r01 capture

Evidence-only [PR #9142](https://github.com/Unjuno/agent-interface/pull/9142) merged at main `9ad2614e8ad329e2aaa90487c28859718f84f647`, preserving all 47 package files and two frozen source/test blobs. All 51 original manifest entries matched before merge. The focused current-main cleanup identity module passed 27/27 in normal and optimized Python; its duplicate-acceptance and terminal-order tests cover the behavior in #8687's two remaining implementation/test changes. PR [#8687](https://github.com/Unjuno/agent-interface/pull/8687) was then closed as superseded, and its original remote branch was deleted after checking author, open-PR use, and registered local worktrees. The next complete inventory r63 records the one-ID PR reduction; #8838 remains distinct and open.


## Verified follow-up: #8838 evidence custody

Evidence-only PR [#9144](https://github.com/Unjuno/agent-interface/pull/9144) merged all 32 A06/A07 files byte-for-byte from #8838's exact head; 30 manifest entries and 32 source/main Git blob identities were verified. A07's WSLc pre-test failure and unconstrained native-WSL fallback remain part of the preserved outcome. After verifying main-tree readback, confirming no other open PR head/base dependency and no registered worktree, #8838 was closed as superseded and its remote branch deleted. No packet code or tests were executed. The complete r64 membership snapshot records only #8838 removed from the r63 open set. See the [custody review](pr8838-evidence-custody-20261019.md).


## Verified follow-up: #8678 A01/A02 tracked evidence

Evidence-only [PR #9146](https://github.com/Unjuno/agent-interface/pull/9146) preserved all 29 Git-tracked files from exact head `7551424026375469f609754140250f89bf09cad4`; main readback matched all 29 blobs. A01 is a prelaunch STOP. A02 retained a cleanup runtime failure; hard guard/task success were not established. The 976-entry ignored raw-output bundle was not found in the current checkout or any of 15 registered worktree roots, so its full raw custody remains unknown. After verifying author, no dependent open PRs, and no worktree, #8678 was closed and its remote branch deleted. #8701's A03–A07 packet remains distinct and open; Issue #59 remains open. See the [custody review](pr8678-evidence-custody-20261019.md) and the [MAP01 family index](../ideas/map01-live-guard-evidence-family.md).
