# 現在の整理状態と次の実行順

2026-10-18 UTC。最新確認main `f4cd5577ef57a01d7b25a389d877c9d1b3ab9d21`。
現在の一覧基準・取得条件・次の整理単位は、以下のr76以降を参照する。
それより下のmain SHAと状態記録は各時点の履歴として保持する。
目的は、多数のワーカーが研究内容を失わず、独立した仕事を選び、検証済み成果を統合できる状態にすること。
整理全体は未完了であり、全Issueを閉じることを完了条件にしない。

### r76: refresh complete Issue/PR inventory and replace stale first-batch queue (2026-10-18)

Current main at capture: `f4cd5577ef57a01d7b25a389d877c9d1b3ab9d21`.
A fresh paginated GitHub REST read at 13:50 UTC captured all 1,676 open Issues
(17 pages) and all 514 open PRs (6 pages). Compared with r6, no Issue or PR IDs
entered or left. Exact snapshots:
[Issues](open-issues-20261018-r7.csv), SHA-256
`80fda3cd11f9abeb2c72ca0aa420fe055efb928ae0b319087608c4e25691680b`; [PRs](open-prs-20261018-r7.csv),
SHA-256 `7d9dc08157e03b437b9c9f09513141c32416a07afe79891dfc3cb76ce78bd1da`.
The snapshots are metadata for discovery and do not establish semantic review,
current ownership, or a reason to close any item.

The old plan's “first batch” for model economics had already been executed:
#7521 was closed with the unresolved implementation/evaluation carried by open
draft #8772; parent #57 remains open. The active queue is therefore to select
one family from the current inventory, inspect source records and exact PR
heads, then record distinct hypotheses, evidence limits, collision boundaries,
and the next finite test. Work remains untriaged beyond previously linked
family dispositions. No blanket Issue/PR closure or branch cleanup was done in
this refresh.

### r75: retain the dirty A16 checkout after remote ref retirement (2026-10-17)

The 2026-10-16 unreferenced-branch snapshot listed
`fix/doom-terminal-health-zero-a16` at `88adef65f48874d681d5600f910ec009e6e662b1`
with a registered worktree. A fresh GitHub branch read returns 404 for the
remote name. PR #8816 is merged with that exact head, and the commit is an
ancestor of current main `1ece47014d05db898bf73afcd722a14524462e15` (370
main-only, zero branch-only commits). However, the registered local checkout
`/Users/taka/Documents/Codex/2026-10-09/agent-interface-59-live-threat-guard-a01/results-local/doom/a16-health-zero-terminal-fix`
still has uncommitted edits in `map01_overlap_controller_v39.py` and
`test_map01_overlap_controller_v39.py`, and no upstream remote-tracking ref.
Open #8842 uses a separate branch. Disposition: retain this dirty checkout;
the merged commit is redundant, but the two local edits have not been reviewed
or preserved elsewhere. Do not reset, remove, or recreate the remote ref until
their owner resolves or explicitly releases the worktree.

### r74: keep the app-server stderr family pending current-main reconstruction (2026-10-17)

The unresolved bounded-stderr-drain proposal is spread across open #7094, its
current-main rescues #8125/#8343, and stacked close-order follow-up #8357.
Current main's `codex_app_server_client_v2.py` still has only the stderr PIPE;
it has no independent stderr reader/tail or stderr-reader join. The #8357
counterexample targets a detached child holding stderr after the owned leader
exits. Its 40/40 focused normal and `-O` result and hosted checks belong to its
old tree; its own body says the native suite could not complete in the sparse
checkout and broader discovery had 22 failures / 87 errors, not fully
classified. #8357 is based on #8343 and has no review decision. Its old tree is
not current-main based (855 main-only / 6 PR-only commits); the direct source
comparison removes current bounded-write, request-retirement, WSL environment,
and other ownership code, so the old `CLEAN` status against #8343 is not a
current integration gate. #8125 and #8343 are also `DIRTY` against their
recorded bases. Keep the original evidence and all dependency refs; do not
merge or close this family based on the old focused passes. Reconstruct the
stderr drain and close-order fix on current main, restore all current client
semantics, and run the native protocol suite in a complete checkout before
fresh reviews or branch retirement.

### r73: retain #7070 until its evidence successor is refreshed and reviewed (2026-10-17)

PR #7070's eight changed files are fully accounted for, but the predecessor
cannot yet be retired. Its two three-file evidence packages are blob-identical
to the corresponding directories in open Draft PR #8335. Its remaining
`COMMANDS.txt` and `REPORT.md` have the same blobs on current main, published by
merged PR #8606. Thus the evidence is preserved across main and #8335; this
does not transfer #7070's proposal votes or satisfy #8335's review gates.
PR #8335 has no reviews and is still based on `217ae2b12378951942f56082bbd44b32171ac9e0`.
Current main is not its ancestor (499 main-only / 4 PR-only commits); a direct
tree comparison spans 8,664 paths, so its old `CLEAN` merge-state does not
qualify it against today's main. Keep #7070 and its source branch as its body
requires. Next, refresh the evidence-only successor against current main,
preserve the six exact package blobs, resolve the report from merged #8606,
then obtain its stated independent content and application reviews before
retiring #7070.

### r72: hold stale constructor-cleanup PR #7062 with current-main regressions (2026-10-17)

PR #7062 is still a draft at `6f79681e5dc5681c984543c087e0da2117872e84`,
has no review decision, and its reported checks pass only for that old head.
Its recorded base is `bfcc14e08fbfe5f2f04cd0237d13559e5d62538b`; current main
`1ece47014d05db898bf73afcd722a14524462e15` is not an ancestor (the local graph
reports 661 main-only and 4 PR-only commits). Comparing the exact PR tree to
current main shows that, alongside new constructor/thread-start cleanup and
tests, it removes current WSL `CODEX_HOME` environment forwarding, custom
process-stream ownership handling, `_closing` checks that stop request and
notification waiters during close, and existing native-suite registrations
for cancellation, caller composition, and verifier/journal failure cases.
The PR's new tests do not qualify those removed current-main behaviors.
Disposition: HOLD for a source-scoped rebase/reconstruction that preserves the
current behavior and suite coverage, followed by checks on the resulting head
and the required fresh review. Keep the unique startup-cleanup evidence and
source branch until that disposition is resolved; do not merge or delete it.

### r71: hold stale, oversized startup-cleanup PR #6944 (2026-10-17)

GitHub readback identifies #6944 as a draft authored by `Unjuno`, head
`686bb56f8e9d16aaf37f1b1b65fd177d05ab11b8`, based on main
`3dc57ecdc21938fecc94990b57a499ebd7c4bc10` rather than current main
`1ece47014d05db898bf73afcd722a14524462e15`. The files endpoint reports 327
changed paths; GitHub's diff endpoint refuses the full diff because it exceeds
its 300-file limit. Current merge state is `DIRTY`, with no checks or review
decision reported. Disposition: HOLD; do not merge, close, or delete its source
branch from this metadata-only triage. A source-level current-main comparison,
content/evidence custody review, and owner decision are still required. The
original PR body also lists unresolved retained-client pipe and later-runtime
wait-cleanup boundaries; prior proposal approvals do not establish current
integration approval.

### r70: archive merged release-composition branch (2026-10-17)

The unreferenced `research/59-release-composition-a01-20261009` tip `e20345f04edbb5bd29925ab86e73b7114ec2520b` is an ancestor of current main `1ece47014d05db898bf73afcd722a14524462e15`. All-state PR search found #8691 as its merged head and #8693 as its merged base; exact-branch Issue search found no body/comment references, and the inspected primary clone had no registered worktree. An annotated tag, `archive/recovered/59-release-composition-a01-20261017`, preserves the exact tip and was verified by remote peel before expected-tip deletion. The snapshot row records the disposition. Current remote counts after this deletion: 584 branches and 521 open PRs. No tests or experiment were rerun for the branch cleanup.

### r69: archive and remove the superseded wake-pipe rescue ref (2026-10-17)

The live branch `rescue/cancel-wake-17d0-20261004` was the head of closed, unmerged PR #7296, with no open PR head/base reference and no registration in the inspected 65-worktree primary clone. Merged PR #8764 already carries the evidence packet on main: all 15 immediate packet-tree entries and their nested tree/blob identities match; main additionally has `.gitattributes`. The exact old tip `1e933698f5d1973a5d4f8c0526f68df1c8720cd7` is preserved by annotated tag `archive/recovered/cancel-wake-17d0-source-20261017`; remote readback verified the peeled SHA and branch absence after an expected-tip deletion. Issue #672's 2026-10-09 retention note predates #7296's closure and #8764's merge, so it remains historical context. The candidate snapshot row now records the disposition. Current remote counts after deletion: 585 branches and 521 open PRs. No experiment was rerun.

### r68: refresh open-PR-unreferenced branch inventory (2026-10-17)

A direct paginated GitHub REST read returned 586 current remote branches and 521 open PRs. Sixty branches have no head or base ref in those open PRs. The dated [open-PR-unreferenced snapshot](open-pr-unreferenced-branches-20261017.csv) records exact tips and protection bits, and cross-references the 65 worktree registrations in the inspected primary clone. This is a candidate inventory only: closed-PR refs, Issue citations, ownership, content preservation and worktree state outside that clone still require review. In particular, `fix/native-handle-bridge-test-binding-revision-20261017` has a registered local worktree despite having no open PR ref. No branch was deleted.

### r67: index three uncovered research records with allocation-local limits (2026-10-17)

A bounded read of the 100 most recently updated open `research` Issues found three research records absent from `docs/IDEAS_AND_OUTCOMES.md`, now indexed: #8200 remains an unverified cue-reversal proposal after its separate #8208 T0 preflight STOP; #4255 retains its consumed 12-session `FAIL_FROZEN_AUDIT_CONTROL_GATE` and open evidence PR #8248; #4435 records the scoped lease-precision result while its archived-evidence audit/custody recovery remains open after merged PR #6092 and later attachment recovery. No allocation was run or retried. The only other unmentioned Issue in this bounded sample, #1945, is an intake/coordination log rather than a research idea and was left out of the idea index. The sample is not an all-Issue completeness claim.

### r66: index WSL readiness and the disclosed WSLc process deviation (2026-10-17)

The central idea index now links open #8685 and #8913 under the established #8677/#8619 Dockerless migration family. #8685's latest record supersedes only the earlier native-Ubuntu startup failure: native WSL startup and a small standard-library smoke succeeded, but no exact-current-main repository validation, WSLc run, or paired cost/memory measurement occurred; shared WSLc ownership remains unresolved. #8913 records three read-only WSLc info/images/container-list calls made despite the ownership gate. No container was launched or changed; this process deviation is not an allocation, lane release, or result, and the calls must not be repeated before owner confirmation. The index explicitly preserves these limits and links the primary Issues.

### r65: retain the unique Windows rescue test pending owner review (2026-10-17)

The unprotected `rescue/win32-release-retain-7772-currentmain-20261007` tip changes only `runtime/backends/win32_v1/test_integration.py`, whose blob differs from main (`cebb009c` vs `406e63dd`). The branch adds focused release-failure, input-query, session-recovery, and unverified-key-up cases. No PR refs or registered worktree were found in the audit clone. The branch name cites #7772, but current #7772 is an unrelated image-Jacobian study and its record does not establish ownership of this Windows change. Keep the unique test source until ownership/content review identifies its intended destination; do not integrate or delete based on the name alone.

### r64: preserve and remove the superseded #8186 review branch (2026-10-17)

The passive `review/8186-response-ownership-e0cc-20261007` branch was unprotected, had zero PR head/base refs, and had no registered worktree in the primary audit clone. Its four review blobs exactly match the packet already preserved in PR #9005; the source tip `e06245cb78059086f7f0e7179c1e8fa59ac2bd6f` is also retained by `archive/recovered/review-8186-response-ownership-e0cc-20261017`. The branch was removed after readback. The review's `REQUEST_CHANGES` remains a historical finding on the strict-integer proposal; it is distinct from the superseding merged #8298. The original #7094/#7125/#7140 source branches were not changed, and no experiment was rerun. Remote branch count after deletion: 586.

### r63: preserve the #8297 packet before deleting its source branch (2026-10-17)

The remote branch `review/8297-reversibility-e0cc-20261007` was absent on readback; its exact tip `31e1ad5d3e3d2d454f074c5d64935675bfe00172` remains reachable through `archive/recovered/review-8297-reversibility-e0cc-20261017`. The branch had zero PR head/base refs and no registered worktree in the audit clone. The four original blobs (MANIFEST, README, RESULT, and `evidence.tar.xz`) were restored unchanged into PR #9005 at commit `d342774e1222947ab6049f7cf0e310fe491c0571`; each Git blob SHA was checked against the archived source commit. The current remote branch count is 587. The deleted ref is recorded in both branch ledgers. No packet code or experiment was run.

### r62: flag the #59 owner-integration branch's missing main record (2026-10-17)

The 300-file `research/59-v15-owner-integration-20261012` tip records A33/A34 STOPs and prior owner-integration work. Its `research/doom/V15_OWNER_RECOVERY_INTEGRATION_A02_A32_20261012.md` summary is absent from current main. The branch has no PR head/base reference or registered worktree in the primary checkout. The ledger now requires owner, raw, and content review before any deletion; no branch was removed.

### r61: retain the Issue #6957 Xvfb A02 source with unresolved raw custody (2026-10-17)

Issue #6957 records that `research/59-xvfb-audit-v3-a02-20261005` has the frozen source and inputs but lacks the declared original run outputs and independent audit streams. Its result is unresolved; the issue explicitly says preserve the branch/freeze and do not infer a disposition or rerun. The branch ledger now records that custody boundary.

### r60: preserve the separate Issue #8592 A01/A02 STOP branches (2026-10-17)

Issue #8592's final comment confirms A01 and A02 each stopped before candidate code loaded, were not retried, and remain preserved in immutable branch history; the merged A03 result is a separate method-scoped outcome. The branch inventory now marks both refs as `RETAIN_ISSUE_CITED_SOURCE`. No result was pooled and no allocation was repeated.

### r59: preserve the distinct Issue #8553 A02 freeze (2026-10-17)

The exact #8553 A02 branch contains the freeze held before formal execution when main advanced (`HOLD_MAIN_ADVANCED_PRE_RUN`, formal counts 0/0/0). The current-main A03 audit reported in open PR #8824 is a separate allocation. The branch ledger now records A02 as `RETAIN_ISSUE_CITED_SOURCE`; no A02 retry or result pooling occurred.

### r58: classify Issue #8581's frozen branch as cited source (2026-10-17)

Issue #8581 remains open and its preregistration comment identifies `research/8581-feedback-artifact-bypass-t0-20261009` and freeze `5c80abe8dc51e7a8ab5e42384fdce0066aca12a0`; formal candidate/auditor counts are 0/0. The branch inventory now marks it `RETAIN_ISSUE_CITED_SOURCE`. This preserves the frozen source while successor evidence and custody are reconciled; nothing was rerun.

### r57: index Issue #8252 and retain its incomplete evidence source (2026-10-17)

Issue #8252 explicitly owns `research/held-chord-h7k3-20261007`. Its comments report a scoped 12-cell backend-method result but state that the matrix raw/audit package is missing from the branch and workspace; the allocation must not be rerun. The branch's source/freeze package remains preserved pending raw delivery or custody resolution. `docs/IDEAS_AND_OUTCOMES.md` now summarizes the reported result, evidence gap, and separate closed PR #8308 boundary without promoting it to production integration.

### r56: repair branch inventory and identify unique A01 evidence (2026-10-17)

The branch review CSV had three rows whose unquoted commas shifted fields. All 32 records are now serialized as valid 15-column CSV and verified by readback. The seven files on `research/59-v39-main-source-identity-a01-20261009` are all absent from current main; its A01 `HOLD_AUDIT_INPUT` freeze, failure and raw are unique. The branch is classified `RETAIN_UNIQUE_A01_SOURCE`; no run was repeated and the ref remains preserved.

### r55: live checkout worktree references for orphan branches (2026-10-17)

The registered worktree metadata in the primary checkout at `/Users/taka/Documents/Codex/2026-10-05/agent-interface-8061-sparse` was compared with the 32 candidate branch names. Six of the 28 remote branches still present have registered worktrees, and all six worktree paths exist: A12 source, A16/A17 source, and the three #8406 T1 checkouts. The [dated worktree readback](unlinked-branch-worktree-readback-20261017.csv) records all candidates and paths. The other 22 present branches have no matching registration in this checkout; that does not prove no worktree exists in another clone. Worktree contents, dirty state, owners, and remaining checkout custody are still unreviewed. No additional branch was deleted.

### r54：未索引の評価・観測Issueを中央索引へ接続（2026-10-17）

Issue #8586/#8587/#8631/#8885の本文・結果コメントと関連PRを再照合した。
`docs/IDEAS_AND_OUTCOMES.md`に結果と適用範囲を追加し、既存の専用ページへ接続した。
新しい#8885ページはanchor-invariance/overlapを満たす場合に限るwave比較提案を記録し、同一taskのpaired比較優先を保持する。
#8587の証拠協調agendaには15-case有限結果、5/5 mutation reject、比較器別検出数と非比較可能なGUI境界を追加した。
#8586のA01/A02は別割当として記載し、#8631はA01 STOP/A02 construction-only/A03 scoped PASSを区別した。
確認時点で関連PRは#8734 OPEN/DIRTY、#8738 OPEN/UNSTABLE、#8747 OPEN/DIRTY、#8633 MERGED。
PR #9005はこの更新前のhead `62b1c91ec09c4d9c7b9b73561016b77188e86812`でOPEN/CLEAN、必須checks成功、レビューなし。
新規実験、Issue投稿、PR merge、関連成果の再実行は行っていない。

### r53：#8914 open PR worktreeのignored状態を記録（2026-10-17）

登録worktree `/private/tmp/agent-interface-8914-a01` はbranch
`research/8914-budgeted-discovery-t0-a01-20261016`、HEAD `b322368ba0da7116bde171de47dee70d2a938ee3`。
PR #9007は同じheadでOPEN/CLEAN。tracked treeに変更はなく、ignored項目はA01/A02各packageの
`__pycache__/`だけだった。open PRのworktreeは保持し、ignored内容も削除せず、現状を
`dirty-worktree-review-20261016.csv`へ追記した。

### r52：#5935のallocation-localなC01重複記録へ修正（2026-10-17）

Issue #5935 comment [#6015047863](https://github.com/Unjuno/agent-interface/issues/5935#issuecomment-6015047863)を編集し、
既存の2026-10-01 T0結果が正本、後続確認はformal rows 0件、枝はpreformal metadataのみ、という事実を保持した。
誤解を招く停止ラベルは除き、当該コメントがC01の重複確認だけを記録し、他allocation/workを停止させないことを明記した。
再取得で旧ラベルがコメントに残らないことを確認した。

`research/predictive-display-t0-5935-20261006-v1`はIssue #5935から参照される4-file sourceであり、
no PR refs・unprotected・登録worktreeなしだが、既存T0の重複確認に使ったfreeze metadataの来歴である。
`unlinked-branch-review-20261016.csv`で汎用の未判定を`RETAIN_ISSUE_CITED_SOURCE`へ変更し、枝自体は削除していない。

### r51：#8648 C01のIssue引用sourceをbranch台帳で識別（2026-10-17）

remoteに残る`research/8648-hysteresis-c01-20261009`のtip `4ce63dfedcdef07d1763147dfc2575fc46077aa1`を
Issue #8648の本文/コメントと照合した。Issueコメントはこのbranch名とtipを修正版C01 candidate/auditor sourceとして
引用し、両者の起動数は0/0、raw resultは存在しないと記録している。C02の別allocationと証拠はopen PR #8827にあり、
C01のpre-execution source custodyとは区別する。CSVの`RETAIN_DIVERGED_TIP`を`RETAIN_ISSUE_CITED_SOURCE`へ訂正した。
branchはunprotected、head/base PR参照0、登録worktreeなし。sourceをmainへコピーしたりremote refを削除したりせず、
Issue引用と履歴を保持する。remote 588本、候補台帳32件のうち4件不在・28件現存で、他の現存tipも一致する。

### r50：#8668のA03–A05結果をテーマ索引へ接続（2026-10-17）

Issue #8668の最新コメントと関連PR #8698/#8745/#8751/#8761/#8796を読み直し、
`docs/ideas/control-dynamics-agenda.md`のA01/A02だけだった記録へ、A02のstale-ACK監査境界と
A03 operation/attempt binding、A04 request-bound ACK、A05 emitted-frontierの別々の有限結果を追記した。
`docs/IDEAS_AND_OUTCOMES.md`にもIssue行を追加した。関連する5 PRはいずれもOPENで未merge。
PR #9005のhead `c91199fe385fd995135e77d3164cff6e2221d249`でreplay-gate、Research Workspace Index、
Public Navigationが成功。作業treeはclean。今回Issueへの投稿、実験、branch削除は行っていない。

現行のbranch API snapshotは588 remote refs。台帳32候補のうち4 refはremoteに存在せず、残る28 refは
記録済みtipと一致した。4件中3件は過去の記録で削除済みだった。4件目のCLI report branchもr40で削除済みだが、
CSV dispositionだけが古い保持判定だったため、確認済みtag peelを照合して削除済みへ訂正した。
ローカルrepoの登録worktreeは2件。
ローカル4 ref中、mainは基準ref、整理PR枝はPR #9005、#8914枝は専用worktree、
残るWin32 test枝はopen Draft PR #9006 (UNSTABLE)のheadに一致する。安全に回収できる枝はこの確認では見つからず、
残る28 refの所有・内容照合は未完了。次はPR #9005の未レビュー状態を保ちつつ、
未参照/closed-head branchの残存候補を一件ずつowner・依存・raw保全と照合する。

### r47：#9004の有限T0結果を索引化し、#8867旧refを回収（2026-10-17）

Issue #9004の未検証案をcurrent-main `1ece47014d05db898bf73afcd722a14524462e15`から凍結し、合成10ケース×4 armを一度だけ実行した。独立raw-only auditは40/40行を再構成して`PASS_METHOD_SCOPED`、通常・optimizedの5 mutation testsがPASSした。結果は`NO_INCREMENTAL_AGREEMENT_VALUE`で、agreement leaseはSystem-1-onlyと同数の作用、always-waitと同じ1 tickの合成中央値となり、事前20%基準を満たさない。`formal_pass=false`、実時間/実アプリ/モデル/GUIの主張なし。PR #9009へraw・監査・報告を保存し、Issueと`IDEAS_AND_OUTCOMES.md`/`RESEARCH.md`/research索引を更新した。PRはOPEN、必須check全てPASS、未レビュー・未merge。

計画記載の#8874は#9000経由で証拠専用として閉鎖済み。元head `6d008b53…`の29ファイルはmainの保存パケットに保持され、RUNNER/BUILD.log欠落は未解決として明記。#8867は#9001経由で現行sourceへ採用済み。旧head `598109fd6329ef88ec469557ae4beae2a2ef3002`の6変更blobすべてがmain上の`original-candidate/`内のbytesとindex SHAに一致した。全PRページでhead/base参照を確認し、#8867 CLOSEDのみ（base依存なし）、branch unprotected、登録worktree/Issue本文・コメントの明示参照なし。期待tipをlease条件にremote refを削除し、remote不在を確認した。元PR本文と#9001保存記録は残し、現行研究の未達は変更していない。

### r48：#9006/#9007のCI境界を分類（2026-10-17）

PR #9006の75行はWin32 `release_all` helper用のtest-only追加で、同suite内の新規caseはpass。`native-mcp`全体は既存`test_native_handle_bridge_v1` 2件がfixtureの`binding_revision`欠落でerror、`native-win32`は既存の`test_valid_program_has_independent_effect_capture_and_release`が`release_unverified`を返してexpected `completed`と不一致でfailした。PR本文もこのverification境界を未解決としdraft/未レビューのまま保持している。今回追加caseが通ることを理由にproduction contractを弱めたり、統合済みと扱わない。

PR #9007のA01/A02 method-contract初回workflowは、GitHub Actions checkout中のfetchが開始から10分でcancelされ、method-contractコードや実験候補/auditorは実行されていない。現時点で同workflowのattempt 2をrerun中。analysis-index PASSは独立に確認した。結果確定前にpass/failへ分類せず、正式allocationも再実行しない。

### r49：#9007 CI再実行とNativeHandleBridge fixture修理PR（2026-10-17）

#9007 attempt 2のmethod-contractはcheckout後18秒でPASS、analysis-index/replay-gate/public-navigationもPASS。PRはOPEN/CLEANで、A01/A02の`HOLD_AUDITOR_METHOD_FAILURE`と非科学的範囲を維持する。

#9006の`native-mcp` failureをcurrent mainで限定再現した。`review_bridge()`がproduction constructorの`binding_revision=0`初期化を欠いていたため、fixtureだけを一致させる一行修理をPR #9010へ分離した。対象2テストと`test_native_handle_bridge_v1`全31件はPASS。PR CIでfixture errorsは解消したが、同じjobは別の既存relay-discovery/closeとguarded-source dependency inventoryの2件でfailure。replay/workspace/X11 checksはPASS、production code不変更。#9006の別`native-win32`失敗（`release_unverified`対`completed`）はこの修理で隠さず、未解決のまま残す。

### r44：#8678をcurrent-main基準へ整列（2026-10-17）

PR #8678は旧`docs/CURRENT_GOAL.md`全体を差分に含み、base衝突で`DIRTY`だった。branch `research/59-live-threat-guard-a01-20261009`をcurrent main `1ece47014d05db898bf73afcd722a14524462e15`へrebaseし、履歴的な長文方向は採用せずcurrent mainの短いgoal entryを維持した。実験記録29ファイル/8,946行追加は保持され、head `7551424026375469f609754140250f89bf09cad4`でPRは`CLEAN`、必須replay-gate PASS。A02のruntime failureと`formal_pass: false`は未変更で、merge・再実験は行っていない。独立レビュー待ち。

### r45：#8701のA09記述を割当スコープに限定（2026-10-17）

GitHub上のPR #8701 head `c0171c688906c86a30a0d36fcbb7f676ad5e8f65`はmainの短い`CURRENT_GOAL.md`にA09更新11行を足したものだった。ローカル`a03-source`の別head `5b9905535b81aac42efde6f58670246c1b7524a4`（旧2,215行CURRENT_GOAL）は未コミットのA08変更7件を持つ作業コピーで、PR headと取り違えない。PRのA09 blockから旧snapshotの「live未許可」引用を除き、A09結果・未retry・scopeだけを保持するcommit `6e308de606ef684ee07406b40958c3275c0bc7aa`をpushした。PRは`CLEAN`、未レビューでchecksは未報告。dirty A08 worktreeとA07/A08 rawは触らず、実行・再監査していない。

### r46：A07保存rawのv3差分をowner-release receiptで照合（2026-10-17）

`a03-source`のignored A07 outputを変更せず`SHA256SUMS.json`の2,358 entries全件をbytes/hash一致確認した。PR #8701のv3監査器を一時ディレクトリで実行すると、10 unique/matched cancellation、post-cancel admission 0、4 no-input cases、5/6 admitted casesで一件不足する明示release transitionを報告し、`status=FAIL`, `formal_pass=false`を返した。別のowner-event reconciliationでは、admissionごとに`keys_held` ackがあり、明示transition/owner keyupは一致し、5件の不足分はterminal `owner_release`のkeycode別verified KeyRelease/XSyncと一件ずつ一致、全final key stateはemptyだった。独立のreconciliationは10/10 PASS、`PASS_CUSTODY_RECONCILED_SCOPED` / `formal_pass=false`。通常・optimized Pythonの5 mutation testsがPASS。v3の元FAILを保持しつつ、server-side custodyだけを別経路で説明する。物理key状態・game消費・task effectは未証明で、A07全体HOLDは変更しない。元v1/v2とrawは変更せず、source/test/JSON/説明をPR #8701 head `44f15471bd07705f1bbe565c017b6f9df29e87ec`へ追加した。PRはOPEN/CLEAN、replay-gateとpublic-navigationがPASS、レビュー未実施・未merge。

### r43：#8648 C01/C02の別々の結果とsource branchを記録（2026-10-17）

Issue #8648と最新コメント、PR #8827を再照合した。C01はWSLc初期化時に止まりcandidate/auditor 0/0で、A01 raw欠落を理由に再実行していない。C02は別のcurrent-main freezeとhost CPython allocationで、288 profiles / 6,048 endpointsの監査、5/5 mutation reject、3つのcoupled held-out settingsで`PASS_METHOD_SCOPED` / `H_PASS_SCOPED`を記録する。PR #8827はOPEN、全必須check success、未merge。`research/8638-split-control-voi-a01-20261008`のtip `16d846740645a338ea11ac70c8e4e931b71f1408`を再確認。unprotected、PR参照0、checkoutなしで、C01 candidate/auditorの唯一のsourceがmainにない。これはC02で代替されず、Issueのraw-custody境界も未解決のためsource branchは保持する。C01 source、候補、監査器は実行していない。

### r42：#8297のreversibility review packetを保全（2026-10-17）

`review/8297-reversibility-e0cc-20261007`のtip `31e1ad5d3e3d2d454f074c5d64935675bfe00172`はunprotectedで、PR head/base参照なし、ローカルworktreeなし。closed PR #8297に対する受動的な4-file review packetである。`evidence.tar.xz`の125,556 bytes / SHA-256 `e0e1ccb1f3ad29331e050315b9348afacc5b7294467b871e74d46caca26f5778`と72 member hashesを検証した。A03のraw-digest discrepancyは元証拠の来歴不明として保持し、A05の保存済み3-case整合とfrozen auditorの既知欠陥を分離する。packetを元のGit blobどおり`research/live_control/review_reversibility_8297_e0cc_20261007/`へ保全し、#8300/#7949の索引と研究indexを追加した。コードやreview packet中のprogramは実行していない。2026-10-17、元tipを指す保全tag作成と4 blobのPR内readback後にremote branchを削除した。

### r41：#8186の未リンクreview証拠を索引・保全（2026-10-17）

Historical snapshot: branch tip `e06245cb78059086f7f0e7179c1e8fa59ac2bd6f` was unprotected with zero PR refs and no local worktree in the audit clone. Its four-file independent review packet records `REQUEST_CHANGES` for numeric reply compatibility and pre-send ownership. The packet was kept byte-identical and the branch was later removed after the source tip was tagged; see r64. #8186 was closed unmerged and superseded by merged #8298; the original #7094/#7125/#7140 source branches remain unchanged.

### r40：p4n7の未参照hash-manifest branchをmainへ保全しref整理（2026-10-17）

`research/cli-report-persistence-retained-p4n7-20261006`のtip `628b90360b4bd5bfc256159ce04300b60c064ae1`を現行API/PR/worktreeと照合した。branchはunprotected、全PR head/base参照0、ローカルworktreeなし、唯一の差分は4つのconversation-local delivery artifactを指す`SHA256SUMS`だった。current mainの`REPORT.md`だけは記載SHAと一致し、`DELIVERY_VALIDATION.json`は別hash、original ZIP/patchはtracked fileとして存在しない。manifestを[研究package内へ原文のまま保全](../../research/integration/cli_report_persistence_p4n7_v1/SHA256SUMS_EXTERNAL_20261006)し、外部artifactの存在/復元証明ではない境界を併記した。unprotected・PR head/base参照0・local worktreeなしを再確認し、tipを`archive/recovered/cli-report-persistence-retained-p4n7-original-20261017`へ注釈tagで保存後、期待tip指定のlease pushでremote branchを削除した。readbackでbranch不在とtag peel=`628b90360b4bd5bfc256159ce04300b60c064ae1`を確認。現在586 remote branches、29 unlinked refs（27 diverged、1 Issue-cited、1 unique A01 source）。#3711およびopen #8239/#8246の状態・evidenceは変更していない。

### r39：GTK relevance/transfer系4 Issueの現状と完了境界を整理（2026-10-17）

#2188のsynthetic distribution-shift誤受理、#2492/#2606の未完の8-case transferと#2606 verifierのmissing raw receipts、#2577のmerged scorer-contract修理を区別した。#2577はPR #2581のbounded preflight・7 focused tests・source-only gateが完了しているため、契約修理だけを明記してIssueを閉じた。#2492/#2606はOPENのまま。#2606のallocationを再実行せず、full GTK acceptanceへ昇格していない。

### r38：MAP01 import-gate系4 Issueの結果境界を索引化（2026-10-17）

#1963/#1967/#2005/#2008のIssue本文、PR状態、workflowコメントを照合した。#1970のsource-only import reproductionは未マージ、#1993はdependency repairの統合後もimport/argv STOPが続き、#2181のbounded gateはlauncher side effectを検出した。後続#2049はlive_control module originとfrozen preflightまでPASSしたが、construction/formalは0。Physical occupancyのPASSは別identityの#1928とfresh replication #2105だけに帰属させ、import-gate修理へ転記していない。4件の記録を`docs/IDEAS_AND_OUTCOMES.md`へ追加し、いずれのallocationも再実行していない。

### r37：#1946 attention package lineageを再照合（2026-10-17）

#1946と未マージ閉鎖PR #1947/#1951、マージ済みPR #1981/#1983、後続Issue #1968/#2031の状態・差分・結果記録を確認した。#1951の元PASS表現にはserialized-sizeとduplicate-labelのレビュー欠陥があり、別表現の並行結果は`HOLD_NO_SIZE_GAIN`。修正版#1968は、PR #1981の3-case formal/audit scoped PASSと、PR #1983の24-row local-only `HOLD_NO_FORMAL_CONTAINER`を別結果として保存している。#1946はOPENのまま、モデル有用性は#2031が継続所有する。`docs/IDEAS_AND_OUTCOMES.md`に証拠系譜と限界を追記。Formal allocationは再実行していない。

### r36：4件の未索引Issueを既存証拠に沿って整理（2026-10-17）

#5360のtoy counterexampleとhost-only opacity evidence、#5296のmapped-geometry constructionと未承認の後続案、#5254の未実行formal LRU allocationとsource/receipt HOLD、#5205のaudit receipt STOPとunsafe-metric欠落を区別して`docs/IDEAS_AND_OUTCOMES.md`へ追加した。関連PR/Issueを再確認し、科学的結果の昇格やallocationの再実行はしていない。#5205のSTOPはその監査allocationだけに限定し、全体停止とは記述していない。

### r35：4件の配分・復帰・学習・失効研究を結果列ごとに索引化（2026-10-17）

#5407の安全性/不足量と公平性のトレードオフ、scarcity-firstの有限FAIL、base-drift STOP、未検証joint-feasibility案を分離。#5404のtyped resumption PASSと未検証cue/overlap課題、#5385のcanonical T0 PASSと未評価T1 STOP、#5361のT0 PASS/T1 gate FAIL/T2 PASSを連続結果として記録した。branch参照も再照合し、remoteに#5407/#5385名の枝はなく、#5407の3 archive tagと#5385の3 archive tagは確認済みtipを指す。実験・runtimeは実行していない。

### r34：4件のプライバシー・制御・通信研究を整理（2026-10-17）

#5413の3つのfinite construction結果と未解決のruntime-enforcer仮説、#5420のrandomized-response T1とconditional-kernel T0、#5433のconstruction-only/正式未実行、#5907のarchive-level source-eligibility HOLDを区別して索引化した。特に#5907は調査した2 archiveに限る結論とし、全archiveへの一般化を避けた。candidate/model/provider/GUIの新規実行なし。

### r33：3件の監査後続結果と2本の枝の保全を索引化（2026-10-17）

#6311/#6306は原T5 HOLD・#6306 parser STOPと、#6311 audit-only PASSを別々に記録した。#6169は#6164のFAIL_AUDITを保った上で、merged #6171のraw-only count reconstructionを限定範囲で追記した。#5911の二つのfinite route-selector結果は分離して記録。併せてGitHub上の旧branch ref二本の不在と、archive tagが各元tip SHAを指すことを確認した。candidateやauditorの再実行はしていない。

### r32：Dockerless移行Issueの実装と実行証拠を分離（2026-10-17）

#8677/#8619と関連コメントを再確認した。現行mainの方針はnative WSL（OCI境界不要）とWSLc（適格なimage境界あり）を分けて既に統合済み。#8677の323+205件はmainより41 commits古いcheckoutでの実行、current-main checkoutでの再検証は未完了。#8619のdigest-pinned smokeはread-only source read/EROFSを確認したが、exact-ID cleanup receiptやhard memory-capの証拠はない。速度・memory・Docker parityの主張を付けず、同Issue群のアドホックhello-world/list記録もacceptance証拠へ昇格させていない。新規のruntime操作は行っていない。branch refも再照合し、remote 587 refs、diverged候補28本は記録済みtipと一致し、候補間の同一tipは0件、先行削除2本は引き続き不在だった。追加削除に足る証拠は得られていない。

### r31：2件の探索Issueの実結果と限界を索引化（2026-10-17）

#5908のmerged PR #6139を確認し、合成T1で3方式すべてが同じ2機序を回収し、descriptor方式のpairwise超過がなかった結果を記載した。#6278のIssue/merged PR #6283では、境界T0、欠落negative controlによるportfolio allocation STOP、qualification-filter constructionと資源/優先順位STOPを分離した。形式candidate/auditorは0/0で、portfolio効果を主張しない。両STOPは各allocationに限定され、他作業を止めない。実験・model・GUIは実行していない。

### r18：4件の既存研究結果を索引化（2026-10-16）

Issue #6640/#6624/#6615/#6611と関連PR・後続Issueを確認し、`docs/IDEAS_AND_OUTCOMES.md`へ結果と境界を追記した。
#6640の失敗判定と#6668の追加baseline再構成、#6624のmerged methodラベルと別途記録されたprotocol逸脱、
#6615のT0/T0B失敗とT0C合成結果、#6611の合成future-reader scorer結果をそれぞれ分離した。
新たなcandidate、model、GUI、game実行は行っていない。

### r19：4件の既存案・後続結果を索引化（2026-10-16）

Issue #8604/#8598/#8589/#8583と関連PRを確認した。#8604 A03はA02と同一rawのWSLc transferであり、別途ownership-gate逸脱が記録されている。
#8598は未実行のcensoring/tail-bound案、#8589は当初method label・後続gate discrepancy・audit-only補足・レビュー時の追加実行逸脱を区別し、
#8583は有限synthetic principal-stratumのmethod結果として記載した。いずれも実GUIや人間研究への外挿をしていない。

### r20：4件の研究Issueと証拠列を整理（2026-10-16）

Issue #8576/#8571/#8569/#8473と各PRを再確認した。#8576は12件の再構成と監査器のhardcoded mutation gateを分離し、
#8571はcustody HOLD下の記述的raw、#8569は合成conditional-recovery method結果として記載した。
#8473はmerged A02と、閉鎖・未統合の別PR #8475を独立した証拠列として整理した。

### r21：4件の制御・推定Issueを結果範囲つきで索引化（2026-10-16）

Issue #8471/#8470/#8466/#8434とmerged PRを確認した。有限列挙のswitched-mode結果、coupled-loop gain screen、
source-time expiry、equal-marginal disturbance-orderの各結果を分け、いずれも合成または有限methodの範囲に限定した。
runtime controller、GUI安全性、実環境の効果を主張していない。

### r22：現行のunlinked branch inventoryを再照合（2026-10-16）

GitHub APIの全ページから587 remote branch refsと全PRのhead/base refsを照合した。現在のunlinked refは30件で、
すべて既存CSVに記録済み。CSVにある削除済み2 refは現行一覧にも存在しない。残る30件は28件のdiverged tip、
1件のIssue引用source、1件の固有A01 sourceとして保持中。新たな削除候補は生じていないため、branch削除は行っていない。

### r23：4件のIssue結果列を実記録に合わせて訂正・追加（2026-10-16）

Issue #8406/#8397/#8313/#8135の全コメントと関連PRを読み直し、古いproposal-only表現を修正した。
#8406はT1の失敗・A16限定pass・A18 incomplete・A19未実行とcalibrationを分け、#8397はA01 STOPとA02 method resultを分離した。
#8313のauditor coverage HOLDとduplicate STOP、#8135のA01 schema failure・A02 scoped result・未着手T1を明記した。

### r24：4件の学習・スケジューリングIssueを索引化（2026-10-16）

Issue #8084/#8080/#8061/#8057と関連merged PRを確認した。#8084のA03 STOP・A04 HOLDとA05低分散false activation、
#8080の合成method readiness、#8061の7-row class boundary、#8057の96-row情報配置fixtureを証拠範囲とともに追加した。
人間研究や実GUIへの外挿は記載していない。

### r25：4件の権限露出・資源・MRT Issueを索引化（2026-10-16）

Issue #7986/#7979/#7834/#7831と関連PR・全コメントを確認した。#7986/#7979は有限method PASSとその反例境界、
#7834はA01/A04/A05/A06の独立結果、#7831は未完のWSLc readiness観測のみを記録した。
いずれもruntime/製品・安全効果へ一般化していない。

### r26：4件の探索・耐久・スケジューリングIssueを索引化（2026-10-16）

Issue #7804/#7802/#7794/#7748のIssue記録と関連PRを照合した。#7804はcandidateのみの未監査STOP、#7802は状態機械のmethod結果、
#7794はA02/A03/A04の独立判定と未達のoperational accounting、#7748は基本scheduler witness・A01停止・別A02 duplicate-ID結果として整理した。
実機耐久性、排出量、ホストscheduler性能に外挿していない。

### r27：4件の評価・隔離Issueを結果列つきで索引化（2026-10-16）

Issue #7678/#7650/#7470/#7459と関連PR・監査訂正を確認した。#7678の三/四-route結果と各HOLD、#7650のA01 row-binding欠陥とA02監査、
#7470のA02-A05設計差分、#7459の正式audit FAILと未解決oracle境界を区別した。いずれも評価/隔離の方法結果に限定して記録した。

### r28：4件のcontext・記憶Issueをcanonical結果で索引化（2026-10-16）

Issue #7387/#7367/#7162/#7161のcanonical packageとfollow-up auditを確認した。#7387のA01 STOP/A02 method resultと追加false-accept検出、
#7367のA01 workload-binding gap/A02 audit-only再検証、#7162のcanonical T0とduplicate #7679、#7161のcorrective audit-v2を区別した。
model-facing・real GUIの効果や認証されていないevent historyを主張していない。

### r29：4件のlayer-identity・prefix-certificate結果を索引化（2026-10-16）

Issue #6843/#6841/#6838/#6809と正式結果を確認した。#6838 A01のrecursive auditor failure、#6841 A02のmutation HOLD、
#6843 A03のcorrected audit-only reconciliationを連結しつつ、過去allocationの disposition は維持した。
#6809 A04のordered-prefix method PASSは#6689系の旧FAIL/STOPと分けて記載した。

### r30：4件のvisual residual・human reliance・fairness・artifact Issueを索引化（2026-10-16）

Issue #6619/#6616/#6613/#6610の正式結果とPRを照合した。#6619 V3 method audit、#6616のconstruction-only HOLD、
#6613の provenance STOP と別個の二つの有限仮説FAIL、#6610のsynthetic artifact-changeability結果を区別して記録した。
実利用者、実GUI、live fairness・safetyの証拠には外挿していない。

### r17：4件のオブジェクト記憶・復旧Issueを索引化（2026-10-16）

Issue #7164/#7163/#7160/#7042を、正式コメントと現行PR状態で照合した。#7164はopen Draft #8216の
合成A02結果、#7163はC01 no-gainとC02の選択的再試行失敗を別PR #7215/#7226に保持、#7160はmerged #7523の
18行identity-bound capsule fixture、#7042はmerged #7359のsource-based release/history-clear範囲として追加した。
新しいGUI・モデル・復旧操作は実行しておらず、memory utilityやfault cureの実証とは記していない。

### r16：4件の結果を再照合し証拠範囲を反映（2026-10-16）

Issue #7430/#7379/#7166/#7165の本文、正式コメント、関連PRを再読した。#7430のメモリ比較は未実行で、
PR #7428は経路ガイダンスのみ。#7379はmerged #7390の有限estimability証明、#7166はmerged #7445の
A03/A04/A05結果列、#7165はmerged #7193のA01安全失敗とopen Draft #8785のA02監査エラー・別read-only
再構成として区別した。いずれも自然タスクutility、memory savings、GUIへの外挿は記載していない。

### r15：4件の既存成果を確認して索引の未確定表現を修正（2026-10-16）

Issue #7475/#7462/#7458/#7436の全コメントと関連PRを再照合した。#7475は未統合Draft PR #7480の
合成カード整合性のみ、#7462はmerged PR #7523の有限DSL比較結果、#7458はDraft PR #7464の
`FAIL_REDUNDANT`、#7436はA01 setup failureとmerged PR #7460の別A02 method PASSとして索引化した。
人間の解釈・承認やGUI/controllerの効果へ外挿していない。関連PR状態も再読時点で明記した。

### r14：#8638の統合結果を反映し、A01証拠refは保全（2026-10-16）

索引の#8638は以前「未検証案」のみとしていたため、IssueのA02結果と関連PRを再読して訂正した。
PR #8740はOPEN / DIRTYで、12 synthetic profiles・192 rows、3組すべての順位反転を独立監査した
`PASS_METHOD_SCOPED`を記録している。コンテナを使わないmacOS network-deny実行であり、GUI/製品の
情報価値や実運用への外挿はない。Issue #8638 A01のmissing-raw custody問題はA02と別の結果として残る。

未参照branch `research/8638-split-control-voi-a01-20261008`を再取得すると、mainにない唯一の差分は
A01 candidate/auditor sourceを含む`experiment.mjs`だった。A01 raw custody問題の再構成に必要なsourceで、
A02 PR #8740では代替されないため削除せず、監査CSVで固有証拠refとして保持理由を明記した。

### r13：4件の研究Issueを証拠範囲つきで索引化（2026-10-16）

Issue #7970/#7732/#7707/#7487の本文・全コメントを照合し、関連するPR #8123/#7744/#7507の現状態と
記録範囲を確認した。#7970はplacement仮説の測定なしと共有WSLc運用逸脱、#7732は未検証の最小証拠束提案と
#6774のcustody不確実性、#7707は候補rawなし・監査未実施の一回限りの実行記録、#7487は20件のsynthetic
provenance判定に限定した方法結果として索引に加えた。人間・実GUI・本番・速度・移行への主張は加えていない。
四つともIssueはOPEN。今回、新しい候補、コンテナ、モデル、GUIを起動していない。

### r12：superseded design-only refを回収（2026-10-16）

`research/8185-transform-graph-a02-20261005`をliveで再照合した。Tipは
`c0f8e1b690d86a7ff10cecf47d9bb16fcd79d053`で、唯一の未統合差分は
`research/analysis/epoch_transform_chain_8185_a02_20261005/DESIGN.md`（blob
`84a151d3d5e495fdb3c7cc9d2cca5860fe8c1df5`）。ファイル自身が未凍結の設計記録と明示し、
同じIssueの後継A02実験と最終プロトコルはmerged PR #8211でmainに存在する。
全状態のPR head/baseを照会して参照0、branch protectionなし、全worktree一覧でcheckoutなしを確認した。
このため、tip固定の`--force-with-lease`でremote refのみ削除し、remote readbackで不在を確認した。
履歴SHA・唯一のパス・削除理由は`unlinked-branch-review-20261016.csv`に保持した。
削除後のlive readbackはremote branch 587本、open PR 518件。直前の監査でPR参照なしだった31本から
この1本を除いた30本が残る見込みで、各refの内容・所有・worktreeを引き続き個別照合する。

### r11：次の4件のIssue証拠を分類して索引化（2026-10-16）

Issue #7955/#7790/#7773/#7741をGitHubから再読し、既存の先行・後続Issue、正式コメント、関連PRを照合した。
#7955の合成rank-uncertaintyとminimax fallback、および未検出のoutside-set miss、#7790のchoice-opportunityとscope条件を
満たす行動由来preference evidence、#7773のmodel-visible candidate-list consumer未発見、#7741の複数allocationを
分けて`docs/IDEAS_AND_OUTCOMES.md`に記載した。#7741のT0dは32/32のsynthetic seed cellsを通過したが、
過去T0群の結果も別に残し、現実のadoption/production/user結果へ広げていない。Issue状態はいずれもOPEN。
本ターンは索引・状態の読み取りのみで、候補やモデル、GUIを実行していない。

### r10：4件の過去Issueを成果境界つきで索引化（2026-10-16）

Issue #8421/#8341/#8185/#8032の本文・コメントと関連PRをGitHubから再読し、
`docs/IDEAS_AND_OUTCOMES.md`へ追加した。#8421はmerged #8430の三つの合成会計ケースに限定したPASS、
#8341は50行の形式上のPASS記録を保ちつつ、position-control cue長不一致とpost-formal auditor importの
逸脱により受入条件が未確立である状態、#8185は不成立のA01証拠と後継#8201の別A02合成結果、
#8032は参加者なしの方法・検出力パケットとして区別した。各IssueはOPENで、関連PR状態は索引に記した。
新しい割当、候補、GUI、モデルは実行していない。

共有インデックスの状態凡例も、記録されたhold/failureラベルがその証拠の説明に限られ、
無関係な作業の割当・停止を意味しないと明確化した。これは過去の結果ラベルを変更するものではない。
Public Navigationは26文書 / 2,140 repository-relative linksで成功。現在の部分チェックアウトには
Research Workspace Index checkerとreplay-gate対象が存在せず、両者はローカル実行できなかった。

### r9：実験ランタイム喪失時のclaim保全案を索引化（2026-10-16）

Issue #8905の本文と関連Issueを確認し、hash/fixity、解釈可能性、raw-only監査、再実行、独立再現を
別レベルに分ける提案として `docs/ideas/claim-preservation.md` に整理した。3種のanalysis-only packageを
offline copyで分類する提案は未実行であり、IssueもOPENのまま。別のホスト監査追試として、保存済みrawに対し
各監査器を1回ずつ実行した。#5749は78行で`PASS_METHOD_SCOPED`、7/7改変拒否、#6530は8行で`PASS`、
#6590は10件の決定論的CPU再フィットと30,720行を確認した後、hash/refit/prediction不一致で
`HOLD_AUDIT_INTEGRITY`となった。#6590はPython 3.14.5 / NumPy 2.5.2上で、packageのNumPy 1.26.4 pinとは
異なる。候補起動や外部モデル実行はしておらず、ネットワーク遮断・入力コピー・5段階分類・fallback評価も
していない。この結果は#8905の当該監査器に限り、他のIssueや実験の割当状態を変更しない。
ページを`docs/ideas/README.md`と`docs/IDEAS_AND_OUTCOMES.md`へ接続した。後続のIssue本文確認で#8846/#8856/#8870/#8872の
4件が既存Markdown未掲載のopen research ideaと分かり、仮説と評価境界を`docs/IDEAS_AND_OUTCOMES.md`へ追加した。
続く本文確認で#8886/#8889/#8898/#8901も未掲載のopen research ideaと確認し、先行・類似案との違いと検証限界を
同じ索引へ追加した。さらに#8902/#8903/#8904の本文を確認し、それぞれの推定対象、比較方法、前提を索引へ加えた。
その後#8638/#8641/#8648/#8651の本文を読み、観測情報の制御分離、feedback、uncertainty source、path dependenceという
別々の問いとして索引へ加えた。
続けて#8596/#8597/#8613/#8614を本文から確認し、確率的進捗境界、decision-opportunity tail、predicate membership、
adaptive cohort reuseを別の研究対象として索引化した。
さらに#8549/#8574/#8577/#8582を本文確認し、人間アラート検出、構造化レビュー、GUI lens-law転送、
human-agent item functioningの4件を別の未検証案として記録した。
次に#8527/#8532/#8533/#8544を確認し、期限内reachability、条件統一したrejection memory、success-cue inoculation、
target–flanker bindingの仮説を各先行Issueと分けて索引化した。
#8498/#8518/#8522/#8526も本文を照合し、retrieval practice、WSLc session reuse、vignette仮定の検証、
path-conditioned read-setという別の問いを追加した。
その後#8618/#8620/#8636/#8675の本文を確認し、cross-task disclosure、execution information、
rotation-invariant visual feature、version-crossing target continuityを分離して索引に載せた。
さらに#8493/#8494/#8594/#8595を確認し、temporal drift、shared-queue synchronization、reverse-stress synthesis、
mediation identifiabilityをそれぞれ別の未検証課題として記録した。
今回#8073/#8166/#8300/#8319も本文から整理し、analogy retrieval、screen-reader handback、external-write journaling、
feedback/update-rule交互作用の違いを追記した。
これで全Issueの分類が済んだわけではない。監査追試の詳細と未実施境界も同ページに記録した。
Public Navigationは26 documents / 2,140 repository-relative linksで成功。PR #9005ではhead
`1313fc6185b4e9ae8af37dc6483cc6da7d50c413`と、4件のIssue索引を含むhead
`7ba4191dd48d4a02f445f33cc9759b0237fb4423`の両方でPublic Navigation、Research Workspace Index、replay-gateが成功した。
変更は既存の [PR #9005](https://github.com/Unjuno/agent-interface/pull/9005) にあり、未マージ。
これは研究ラベル全体の整理完了ではない。次は未整理Issueと未参照branchの実内容・既存証拠・所有を個別に
照合し、意味のない重複記録や安全に回収できるrefだけを特定する。

### r8：アイデア索引と重複branch refの更新（2026-10-16）

基準mainは `1ece47014d05db898bf73afcd722a14524462e15`。全Issueを `research-idea` labelで照合し、
未掲載の #8022/#8024 を `docs/ideas/` と `docs/IDEAS_AND_OUTCOMES.md` に記録した。
#8022は no-human protocol audit のHOLDと倫理条件、#8024は authored fixtureのMETHOD_PASS_SCOPEDと
固定timeoutを上回る価値が未実証である境界を残す。Issueは開いたまま。変更は
[PR #9005](https://github.com/Unjuno/agent-interface/pull/9005) にあり、先行headではPublic Navigation、
Research Workspace Index、replay-gateのCIが成功。今回追記後のheadは別途CI確認する。未マージ。

未参照branch `research/8654-c03-support-sufficiency-20261009` (`e4061a6f0fc9863ed2dbec7e09d3a99b4972685`)は、
無保護、全PR head/base未参照、登録worktreeなし。mainとの差分16ファイルすべてのblob SHAがmainおよび
merged PR #8664と一致し、#8664のC04がC03のpre-candidate STOP履歴を明記していたため、remote refだけを削除し
GitHubで不在を確認した。Issue #8654とmainの証拠ファイルは変更していない。

`fix/8243-verifier-r2p6-20261006` は別途再照合した。8ファイルすべてがopen rescue PR
[#8375](https://github.com/Unjuno/agent-interface/pull/8375) と同一blobだが、merged Issue #8243の公開freeze
コメントが元branch名とtipを引用しているため、このrefは保持する。PR #8375の統合後、または引用を安全に
置き換えた公開記録が確認できた時点で再評価する。

削除後のlive snapshotはremote branch 588本、全PR 6,102件、open PR 518件、PR head/baseに未参照31本。
未参照31本の個別内容・所有確認は継続中。削除は確認できた重複ref一件に限定し、worktreeや固有rawは
対象にしていない。

## 後続の現在地

### r7：マージ済みremote branchの再照合・回収

同日取得した全6,100件のPR記録とremote branch 618本を照合した。#8862のmerged branch
`fix/pr8857-deadline-type-fix`は、main包含、無保護、依存PRなし、worktree未使用を
確認して個別に回収した。618本の一覧では、さらに19本がmerged PR headとtip完全一致、
main祖先、無保護、全PRのhead/base依存なし、確認したlocal worktree未登録の条件を
満たしたため、tip固定`--force-with-lease`で削除した。これら20本はmainから到達できる。

| PR | 削除したremote branch | tip |
|---|---|---|
| #8862 | `fix/pr8857-deadline-type-fix` | `37d6fca43c927de8acc1cbfc3d1a30808377a229` |
| #8821 | `fix/doom-passive-refresh-empty-release-token` | `30ba3a90be112fe6bbcb0ed52e43a4041bea5b6e` |
| #8829 | `fix/issue59-v10-release-rpc-failure-20261009-a01` | `a197e6a87132be5fd29a5a0656edb5b309a2a7b2` |
| #8837 | `fix/v39-windows-appserver-executable` | `7adc0fdc8b191cc139baa30fe7c3bb605c2dab03` |
| #8693 | `fix/59-release-cleanup-lease-identity-a01-20261009` | `cb47c43c97258cd92f3059c22e49eb181dbf2435` |
| #8835 | `fix/59-terminal-release-completeness-20261009` | `c024b41a0aac62a6b3d466e935d77edf477bb3fa` |
| #8813 | `rescue/7321-evidence-only-20261009` | `84d92821780b69f14625542b27725965b2519e50` |
| #8820 | `rescue/8686-currentmain-20261009` | `8bd299a5bc86cf3711ca51fc36a974f433761842` |
| #8815 | `research/a16-result-evidence-20261009` | `2d777d5290a6fded898ca8977ce04f0838ffc55d` |
| #8871 | `research/health-typed-release-delay-a01-20261012` | `18d1fadea3dcad4cffaa743d3480fa309edcf643` |
| #8923 | `research/v10-wslc-app-effect-a35-a36-20261015` | `7f7065a050ad4d9b5dfd89cf2b324ba95309a1cf` |
| #8922 | `research/v39-wslc-app-effect-a34-20261014` | `b1983742ed7e73a5f62e08f8b271d927c0eeb060` |
| #8918 | `research/wslc-typed-guard-replay-a03-20261013` | `580c452ddd0fea55be817f138ad225d2f44de4e6` |
| #8771 | `research/59-cleanup-unknown-key-failclosed-20261009` | `8af95598a2517088203be2696b043ef329ba5b5c` |
| #8690 | `research/59-global-live-gate-scope-20261009` | `7de1969eebef154108d4349d2ba8f9ab00e8f3b0` |
| #8866 | `research/59-health-only-typed-monitor-a01-20261012` | `eb1367cc3ac1184862c454440a418dcf1add9267` |
| #8699 | `research/59-invalidation-recovery-a01-20261009` | `94c3f4c7299c3e5e8c50890071bfcb96a4ae7193` |
| #8696 | `research/59-terminal-custody-order-a01-20261009` | `e991aa78c28b4bbbb55de5599248b26a9e16db8f` |
| #8742 | `research/59-v39-regression-a03-currentmain-ffe5292-20261009` | `fd0f79e1ad36e39fb8e4a435fc0a63650b942170` |
| #8822 | `research/6018-importance-sampling-t0-a01-20261009` | `e3e025c37701717ecfb5263b9ee45bc5051de6a5` |
| #8705 | `rescue/5749-action-only-currentmain-20261009` | `1b438270124f1647e950fd320067a1a078e80e40` |
| #8709 | `rescue/6576-a04-archive-currentmain-20261009` | `7f25e16a6d9356c7dcac49033758433dfb46cb89` |
| #8710 | `rescue/7386-7414-currentmain-20261009` | `0c4dabaaa40d0c681eaa01dc776879e725cc2441` |
| #8884 | `research/wsl3-residual-docker-inventory-20261012` | `d4c726cd7dbb84c2cd7eacd01aef897407ae8c67` |
| #7109 | `research/17-gil-cancel-c01-70ab-20261003` | `8394ab7f4a82cafc29a851c28afd56d7a1c8f804` |
| #8384 | `research/59-interrupt-cancel-compose-a03-20261008` | `fd52341c4686893ff3de8795c9a5b671c7d20f9c` |
| #8874 | `research/59-v39-owner-close-currentmain-a09-20261012` | `6d008b53e23fda4703c8f56c4ea1bd762e5d147b` |
| #8662 | `research/8654-c02-raw-custody-20261009` | `60a726cf744cab1044083ce0af61d7d4acf43adc` |
| #8786 | `test/exchange-presentation-failure-20261009` | `5f8fdedaac8fbdaf820ca26dd7ebc7985dc2305a` |
| #7264 | `feat/finite-role-recovery-2d0b-20261004` | `8fe7c2b7a955187939014aff33cf61ed01ea90e9` |
| #8370 | `rescue/finite-role-recovery-currentmain-20261008` | `9fb4a64d6a86fc2eb01b4e984508e8f320bb3e31` |

The four #8705/#8709/#8710/#8884 tips were not ancestors of main, so their changed files were
compared blob by blob. Every evidence file was already identical in main; branch differences were
stale index deletions or, for #8709, an older archival qualification missing provenance detail
that main already preserves. The closed, unmerged PR heads #7109/#8384/#8874/#8662/#8786 had no
base dependents or local worktrees, and every changed file was byte-identical to main. Their PR
records remain available. The #7264/#8370 finite-role prototype and tests are also byte-identical to main;
their only unique README row is superseded by the current main convergence link. The remaining
branch `research/59-a07-cancel-admission-order-a01-20261009` has 36 A03–A07 files absent from main
and is retained for evidence preservation/integration review. After all 31 ref deletions, the live
remote count is 588 and every deleted ref was verified absent. PR-linkage classification of the
remaining refs is 516 open-PR heads, 10 base dependencies, 29 closed-PR heads, and 33 with no PR
head/base reference in the complete 6,100-PR snapshot. The closed-head and unreferenced groups
still require content/owner review; they are not assumed disposable. The [unreferenced-branch
comparison](unlinked-branch-review-20261016.csv) records exact tips, ancestry, current-main blob
matches, and local-checkout coverage. All 33 are unprotected but diverged, with one or more commits
ahead of main; 32 contain paths absent or different in main. The remaining blob-identical branch
is associated by name with open Issue #8654. No matching checkout was found in the 38 local Git
checkouts scanned. Issue/owner association remains incomplete, so these 33 refs are preserved.

After that snapshot, `research/wsl3-dockerless-doc-inventory-8882` was reviewed separately.
Issue #8882 is closed with an explicit completion record pointing to the superseding inventory
merged by PR #8884; the branch had no current PR head/base reference or matching local checkout.
Its exact tip `76f33cc4b6c7af55074030ddc85857b73aec3117` was deleted with a tip-fixed lease and
verified absent. The current remote branch count was 587 and the no-PR-reference group was 32
at that intermediate capture. The comparison artifact was absent from main; the current census
below replaces it.
Subsequent creation of the current-main Win32 release-test PR #9006 added one open PR head; the
following readback found 588 branches and 517 open PRs, with 32 no-PR-reference branches.
2026-10-17 readback through the GitHub API reports 588 remote branches and 521 open PRs. Comparing
the complete paginated branch list against the 32 names in the saved no-reference review finds 28
still present and four absent: `rescue/59-paired-epoch-a03-precursor-20261007`,
`research/8185-transform-graph-a02-20261005`,
`research/8654-c03-support-sufficiency-20261009`, and
`research/cli-report-persistence-retained-p4n7-20261006`. GitHub branch search confirms each is
absent. The [dated readback](remote-branch-presence-readback-20261017.csv) records all 32 candidate
names against the 588-branch snapshot and the current PR-reference queries. Exact GitHub searches
for each name as `is:pr head:<branch>` and `is:pr base:<branch>` returned zero across open and closed
PRs for all 32. The newly opened PRs #9007, #9008, #9009 and #9011 target `main`. All 28 remaining
branches are still preserved pending owner/content and local-worktree review; zero PR references
alone does not establish that their unique evidence is disposable.
The closed #8592 transfer is not a deletion signal for every associated ref: its final comment
explicitly keeps A01/A02 execution STOPs and the superseded A03 freeze in immutable branch history.
Accordingly, `research/8592-dpor-t0-a01-20261008` (`b0951ae1…`) and
`research/8592-dpor-t0-a02-20261008-r1` (`bb195877…`) remain retained as evidence custody.

The separate no-PR rescue branch `rescue/win32-release-retain-7772-currentmain-20261007` also
contains release-custody tests absent from current main, so it is not disposable. Current-main
adaptations are in draft [PR #9006](https://github.com/Unjuno/agent-interface/pull/9006): its five
new pure release tests pass locally and in the native-mcp Win32 module, but CI remains red. The
unchanged native Win32 fixture test returns `release_unverified` when `GetAsyncKeyState` reports
zero; the native-mcp job also has four failures in other test modules. This is an unresolved
release-verification contract and CI baseline, not evidence that the new tests failed. No runtime
code or original rescue ref was changed.

### r6：モデル連携・比較評価アイデアを一族ごとに整理

基準main `1ece47014d05db898bf73afcd722a14524462e15`（2026-10-16）。
[モデル連携・評価agenda](../ideas/model-coupling-and-evaluation-agenda.md)と
[Issue中心の一覧](../IDEAS_AND_OUTCOMES.md)へ、#6001/#6035/#9004を追加した。
これらは同じ結論へまとめない。#6001の合成canary/interference T0とWSLc replay、
#6035の64行合成cross-model method T0は、それぞれの限定根拠と過去のSTOPを分けて記載。
#9004は未検証のまま、Issue本文のfinite CPU-only T0条件と比較対象を整理した。
Issueの状態変更、外部provider/model呼出し、GUI実行は行っていない。

運用記録Issue [#8913](https://github.com/Unjuno/agent-interface/issues/8913)は、2026-10-12の
WSLc read-only事前確認と、#8685のclient/container lane条件を読んだ後に認識した手順逸脱を記録する。
実験・移行結果ではなく、既存allocationも消費していない。この記録が限定するのは当該WSLc
操作だけであり、独立した作業や他の実験レーンの停止条件ではない。

2026-10-16にIssue #8914のオフライン候補を実行したところ、A01/A02とも候補後の独立監査が
sentinel再構成で止まったため、科学的判定なしのraw保全PR
[#9007](https://github.com/Unjuno/agent-interface/pull/9007)を作成した。
branch `research/8914-budgeted-discovery-t0-a01-20261016` はこの未統合PRのheadとして保持中。
同日時点のremote refs 589本・open PR 518件にはこれを含み、削除済み・main統合済みとは数えない。
この保全用branchは独立したWSLc・GUI・ゲーム・model作業を制限しない。

同日にbranch/PR参照を再取得して比較表を[再生成](unlinked-branch-review-20261016.csv)した。
589 remote branch、6,102件のPR参照record、PR head/base未参照32 branchを照合し、32本すべて
unprotectedかつmainとdiverged、合計106 commit aheadで、比較APIが各branchの変更pathを報告した。
32本中6本は監査cloneの登録worktreeにも存在する。各tip・merge base・ahead/behind・変更path・
worktree対応をCSVへ記録した。32本は固有内容と所有者の確認が残るため削除していない。

同じroot cloneのworktree台帳は92件中33件がprunableで、その33パスが実在しないことを確認した。
dry-runが示した欠損metadata 33件だけを`git worktree prune`で除去し、branch refや作業ファイルは削除していない。
59登録worktreeが残り、prunableは0件。read-only statusでは52件clean、7件dirtyだった。
変更path・branch・remote/PR参照の[一覧](dirty-worktree-review-20261016.csv)を保存し、いずれもreset・削除していない。
dirtyなA16 health-zero worktreeの2 tracked変更を含み、raw/evidenceのuntracked項目も現存を再確認して保全した。

同じバッチで、統合済みPR [#8791](https://github.com/Unjuno/agent-interface/pull/8791)
のremote branch `fix/primary-release-array-shape-20261009` を回収した。記録tip
`3884c929435db18855b5ca62e95ca90ceadb52ed` は現行mainの祖先、branchはunprotectedで、
open/closed PRのhead/base依存はなく、確認した69件のlocal checkoutでも未使用だった。
正確なtipへの`--force-with-lease`削除後、remote refの不在を確認した。変更内容は
merge commit `761a26e2cfae611efe97a426ed2555063928b177` とmainに残る。

続けて、merge済みPR [#8784](https://github.com/Unjuno/agent-interface/pull/8784)の
`fix/kernel-stop-release-evidence-20261009`も、tip
`08dd5be82cf9750faca9f9d9d5ba81aaf446bea0`がmainの祖先であること、unprotected、
head/baseとも依存PRなし、確認範囲にlocal checkoutなしを確認して、tip固定で削除した。
PRのmerge commit `b8ab890b03289f9a1303377c26b3cbb41ce7231e`もmainの祖先である。
branch削除後にremote refがないことを再確認した。関連する古いlocal cloneでは、dry-runが
存在しないdirectoryを指すと確認した3件のstale worktree metadataをpruneした。

#8816と#8763は、closed PR #8823/#8787のbaseに使われていたため、今回の削除対象から除外した。

次は#9004の有限合成T0を独立したsource freeze・candidate・raw-only auditとして実行するか、
先にIssue群の依存・実行優先を更新して実行先を確定する。#57の統合効率ゲートを押しのけず、
実モデルT1やremote-model budgetを使わない。並行してPR/branch inventoryを現行状態で再取得し、
完了・後継移管・保全のみ・未判定を判別する。全件の内容精査やref削除はまだ完了していない。

## 前段の進捗履歴

### r5：保全していたV15選択変更を現行mainへ結合

基準main `7aeb6f933c67384ad0e8d3b25e1d68a44ec341a8`。#9001は統合済み、
#8867は[採用先付きで終了](https://github.com/Unjuno/agent-interface/pull/8867#issuecomment-6207033828)。
[V15選択の結合記録](../../research/integration/owned_service_session_20261016/README.md)では、
旧`8a252071...`の変更を現行の計測・プロトコルguardと結合し、原履歴もtreeを変えず保持した。
旧149件の結果を転用せず、通常・最適化各208メソッド/27モジュールを実行、skipなし。
各10 session行、96 parent source pin、99 sourceのraw/LF別凍結を保存した。
別読取は両modeで通り、各reportの15改変を拒否。所有子56 PIDは確認時点ですべて不在だった。

起動/終了の原本・失敗・出版衝突・初回の解放失敗を残し、後のcleanup成功で昇格させない。
V15オプション試験のbase.mainはスタブで、実wrapper/backend試験はFake Xと所有Python子による。
実session/controller死亡、native解放、環境応答、task effect、matched economicsは未達。
この結合後は旧選択branchを新しい未着手仕事として案内しない。次の整理はモデル/比較評価一族。

### r4（履歴）：#8867の計測変更を現行経路へ収束

基準main `5abbc37e7674d52ef452f08f64bce3b8cb82fd0b`。
#9000はこのmainへ統合済み。#8874は原29ファイルの保全先とログ欠落を示して
[終了](https://github.com/Unjuno/agent-interface/pull/8874#issuecomment-6206880752)した。
元PRを直接mergeした扱いや、#59の研究完了にはしない。r3の517件は処理前の一覧。

#8867の[計測収束記録](../../research/integration/v39_event_timing_convergence_20261016/README.md)では、
ログ開始とstdout受渡しを区別し、controllerのparse/queue/monitor時刻を現行経路へ接続した。
移植時のreader衝突は、現行の重複JSON拒否とcontrol-boundary失敗拒否を残して解消した。
通常・最適化Python各70メソッド/10モジュール、各7保存行、59凍結sourceを確認。
別読取処理も両modeで通り、各reportの11改変を拒否した。実ゲーム/GUI/providerの時間測定ではない。
旧PRの6ファイルは原バイトで残し、追加テスト・現行guard・採用sourceとは区別する。

V15選択branch `8a252071ea7fb5281b9ecc154fa1640136d5345c` は引き続き未統合。
session/controllerの同じファイルが今回変わるため、以前の149件の結果を新mainへ自動転用しない。
取り込み時に正確な差分を結合し、影響する検証と証拠読戻しを行う。
次の整理対象はモデル連携/比較評価のアイデア一族。実制御ではV15選択と実session/controller死亡、
環境応答・タスク効果・matched economicsの不足を残す。

### r3（履歴）：全体整理を優先

基準main `4c63725565f4dea433c49213b8d068c4c762f9bf`。
[r3取得条件](inventory-20261016-r3.json)、[open Issue 1,678件](open-issues-20261016-r3.csv)、
[open PR 517件](open-prs-20261016-r3.csv)。r2から#8876がopen一覧を離れた。
これは全件精査済みという意味ではない。#8876の公開候補と古いRPC境界は
[既存の収束記録](../../research/integration/crash_owner_convergence_20261016/README.md)へ接続する。
一覧は本バッチ公開前の非原子的スナップショット。

[全体計画](../REPOSITORY_CONSOLIDATION.md)に、入口・アイデア/Issue・PR・branch/worktree・
採用実装のそれぞれの完了条件と実行順を追記した。次はモデル連携/比較評価のアイデア一族と
#8867の計測差分を別々の有限なバッチとして読む。Issue数ゼロを完了条件にしない。

#8998/#8999で独立cancel laneと選択backend/Executor custodyはmain統合済み。
[現行adapter証拠](../../research/integration/owned_backend_adapter_20261016/README.md)へwork mapを更新した。
V15/controllerの選択経路はローカルbranch
`work/owned-service-session-selection-20261016`、commit
`8a252071ea7fb5281b9ecc154fa1640136d5345c`に保全してあり、このmainには未統合。
149メソッドの再検証と原rawはローカル専用出力
`new-chat-2/outputs/repository-consolidation-20261015/owned-service-session-final-r2-*`に保持。
単独実行でのimport復元問題を修理したが、正式証拠パケットの読戻しと統合は残る。
このbranchを不要物として削除しない。

#8874の[保存専用照合](../../research/integration/owner_close_a09_preservation_20261016/README.md)では、
公開headの29原ファイルを同一バイトで保全し、元manifestが要求する
`RUNNER/BUILD.log`の欠落を記録する。当時のraw限定監査と、証拠パケットの完全性は別判断。
WSLc/producerは再実行せず、現在source・実機・task effectの成功へ読み替えない。
元の科学的問いと不足は#59で継続する。

以下r2以前の件数と「次」は各時点の履歴として読む。

### r2（履歴）

基準main `8a70a77fc6542d49b03de2f1403b3fd8bcd00397`、取得時刻は
[inventory r2](inventory-20261016-r2.json)。[Issue 1,678件](open-issues-20261016-r2.csv)、
[open PR 518件](open-prs-20261016-r2.csv)を取得した。明示上限未到達・番号重複なし。
非原子的な案内用スナップショットであり、全件の内容・担当・採否を確認した件数ではない。
以前の524件から除かれた6件を[APIで照合](pr-convergence-20261016-r2.csv)した。
6件とも元PR自体はmergedではなく、次の保全・採用先へ収束した。
APIのmerge_commit欄が非nullであってもmerged=falseを覆さない。

| 元PR | main上の実行・保全先と残る問い |
|---|---|
| #7264 / #8370 | #8986、[finite role convergence](../../research/integration/finite_role_recovery_convergence_20261016/README.md)。同一prototypeと独自README文脈を保持。実callerの文書効果adapterは未達。 |
| #7954 | #8985、[callback convergence](../../research/integration/compiled_callback_convergence_20261016/README.md)。post-input verifier/journal例外のprefix・解放・原因保全を修理。耐久的な公開保証とは別。 |
| #8786 | #8987、[presentation convergence](../../research/integration/primary_presentation_convergence_20261016/README.md)。効果後のreply失敗で再送を拒否。実アプリの成功判定は未達。 |
| #8792 | #8988、[saved recovery correction](../../research/integration/v39_hard_recovery_convergence_20261016/README.md)。初期normal/-O記録の回復source不足とv1 false passを保持・訂正。 |
| #8812 | #8967、[saved regression convergence](../../research/doom/v39_saved_regression_convergence_20261016/README.md)。初回FAILと後続CPU結果を原本のまま保全。現行ライブ検証ではない。 |

続く#8989/#8990/#8991/#8992は現在V39 helper→Executor pipe→選択backend/ownerへ
構成確認を接続した。最新の[結合記録](../../research/integration/v39_selected_backend_recovery_20261016/README.md)は
15メソッドを通常/-Oで確認したが、Fake X・注入HUD・制御されたterminal待機に限定される。
次は実session/controllerの死亡時に入力責任が残る境界と、独立したtask effectの検証である。
#8876の保存済みcrash recovery候補を照合する際、古いheadと新mainの全体差分をそのまま採用しない。

[worker work map](../WORKER_WORK_MAP.md)は7つの独立した選択範囲と次の有限な成果へ短縮した。
従来本文は[Git原文のまま保存](../WORKER_WORK_MAP_HISTORY_20261016.md)。
ROADMAPの古いexperiment-first優先指定も現行ゴールの整理・統合優先へ揃えた。
既存の研究Issueの問いは残し、今回新たなIssue closureや実機操作は行っていない。

以下の棚卸し・終了先は先行する時点の履歴である。上のr2を最新の一覧入口として使う。

## 今回確認・訂正したもの

- [全open Issue](open-issues-20261016.csv)：1,678件。番号の重複なし。
- [全open PR](open-prs-20261016.csv)：524件。head SHAとbase branchを保持。
- [前回openだったPRの終了先](pr-convergence-20261016.csv)：14件。APIで直接merge 7件、mergeせず終了7件を確認。
- [取得条件と原export hash](inventory-20261016.json)：Issue取得上限5,000件、PR上限1,000件に達していない。
  最初のIssue exportは1,677件。下記の#5訂正後に1件をAPIから追加し、GitHub検索の1,678件と照合した。
  取得は非原子的。CSVは入口であり、本文・全コメント・担当確認の代用ではない。

[#5](https://github.com/Unjuno/agent-interface/issues/5)は未完了とする最新コメント・agendaに反して
completedで閉じられていたため再オープンした。#8937はFake Xのprocess identity接続の一部を検証した成果であり、
visual addressing/feedback全体の完了ではない。原議論と既存agendaを継続先として維持する。

## 終了したPRの移管先

| 対象 | 処理・現在の実行先 |
|---|---|
| #6934 | #8965で固有のWin32 custody修理と184原証拠ファイルの保全を照合。旧PRは後継へ収束。native操作の合格ではない。 |
| #7109 | #8953へ証拠を収束。過去のblocked-I/O/GIL境界の結果を現行の物理解放保証へ読み替えない。 |
| #7296 / #8764 | #8764をmainへ統合し、#7296を終了。wake-pipe証拠と独自差分を保持。 |
| #7981 | mainへ統合。FAIL_CROSS_CLIENT_ISOLATIONを維持。 |
| #8384 | #8956へ15原ファイルと監査修理を収束。構成PASSをライブPASSにしない。 |
| #8723 / #8707 | #8701のstackへmerge。**#8701はopenでmain未統合**。A07原rawの保管元監査が残る。 |
| #8801 / #8814 | #8933で共有rawと各独自追試を保全して終了。 |
| #8834 | Windows匿名pipeの修理をmainへ統合。GUI実行ではない。 |
| #8839 | #8946で現行launcherへ収束。古い実装で後続修理を上書きしない。 |
| #8866 / #8871 | mainへ統合。typed healthの早期検出・解放の条件と限界は各packetに保持。 |

個別merge/終了時刻・元headはCSVから辿る。終了件数だけを採用成果やmain反映件数に換算しない。

後続の[#8812収束記録](../../research/doom/v39_saved_regression_convergence_20261016/README.md)では、
A11の初回FAILとA12の保存済みCPU結果を原48ファイルのまま保全した。
当時のsource 34件中11件は現在の基準mainから変わっており、現行制御の検証として再利用しない。
保存結果の別監査と改変拒否を使い、消費済みのproducerは再実行しない。

## 実行する整理バッチ

### 後続の統合・証拠所在の照合

後続のmain `de7bcbf86316b312e3a34c9b15b07336caaa14ff`では、#8971の保存専用X11候補保全、
#8972の割込み時cleanup、#8973のMCP割込み証拠、#8974の同一backend内session回復custodyを統合済み。
各packetのFake X・単一process等の限定を維持し、実機の有限解放やtask effectの達成とはしない。
このmainで14作業ツリーの追跡変更・未追跡ファイルがゼロであることを確認したが、
無視対象・他者の所有権・リポジトリ全体の整理完了を証明するものではない。

[caller一族の現行照合](../../research/integration/caller_current_main_convergence_20261016/README.md)では、
#7289/#7310はclosedで、両headと合成commitがこのmainの祖先であることを確認した。
PR自体のmergeとは区別し、現行callerで19モジュール・76テストを通常/-Oで実行、
各221保存行の会計・完了prefix・未検証効果の整合を別読取処理で確認した。
古いcaller合成待ちやレビュー人数待ちは現在の不足ではない。#57はアプリ効果・実provider会計・
同条件比較と移植の未達を維持し、新たなIssue closureは行わない。

main `2b9df51535c7662d76ac29477bb14e2219eb9865`までに、次の有限な整理を進めた。

| 対象 | 現在の処理と残差 |
|---|---|
| #8812 / #8967 | 保存済みA11初回FAILとA12 CPU結果を原48ファイルのまま収束し、#8812を後継付きで終了。現在sourceで当時の結果を更新しない。 |
| #8968 / #8969 | 公開guarded MCPと選択MAP01/V12のwindow lifecycle経路を別々に構成検証してmainへ統合。#8969の保存済み通常・最適化各58モジュール/427メソッドには各12 skipがある。実機・task effectの合格ではない。 |
| #4008 | 本文と全3コメントを照合。36ケースの結果報告と217ファイルのローカルpackage検証はあるが、予定packetはこのmainにない。元branchの現remote refも取得されず、Issue番号検索で出版PRを特定できなかった。別名・未公開原本の不在は証明していない。公開・読み戻しが未完了なのでopenを維持する。 |
| #8701 | source head `ce6724b870696916d8d421e20d9bcd18362af88c`のopen PRを再確認。v2/v3はstackに保存済みだが、元A07の2,358ファイルと保存済みepisode監査の照合が残る。synthetic結果だけでmainへ統合しない。 |

#8969統合後のprimary mainは上記SHAへfast-forwardし、14作業ツリーは追跡変更・未追跡ファイルともゼロだった。
この整理作業自身の統合済みfeature/integration refだけを、tip・main包含・open head/base依存・作業ツリーを確認して除去した。
他者のbranch・無視対象・保全候補は保持する。以下の全件CSVは取得当時の履歴であり、上記変更後のlive件数ではない。

既存の[作業マップ](../WORKER_WORK_MAP.md)のテーマを使う。新しい調整Issueやサービスは作らない。
各バッチは「対象を読む → 固有の残差を抽出 → 必要なローカル検証 → 統合/終了 → 参照を戻す」で一巡する。

| 順 | 対象・編集先 | 終了条件と次の作業 |
|---|---|---|
| 1 | 未統合PRの一族、上記PR CSV | 元head・固有差分・原証拠・依存を照合し、現在mainへ採用する部分を局所検証して統合。重複は保存先と残る実行先を示して終了。まず#8701の保管元raw、既存保全commitの世代/scorer差分を照合。 |
| 2 | #3/#5/#8、`docs/ideas/visual-interface-agenda.md` | 仮説ごとに既存結果・残差・次の判別を更新。次は同processでのwindow再利用とsubscription coverageの境界。Fake X構成とライブ資格を区別。 |
| 3 | #2/#10/#14/#15/#16/#17、`docs/ideas/safety-control-agenda.md` | process/backend間の未解放入力custodyとblocked native I/Oを既存の修理・反例へ接続。有限回復や物理解放時間を未測定のまま完了扱いにしない。 |
| 4 | #57/#59/#2789とドメイン別の関連Issue | 観測・環境応答・task effect・回復・比較会計を分け、同じ問いの実行記録は親へリンク。Calcの保存済み4ケースとmatched economicsの不足を区別。 |
| 5 | 残りのIssue、`docs/ideas/`と研究map | 一つのテーマずつ本文/コメント/関連PRを読み、固有仮説・結果・依存・次の検証を整理。タイトル分類だけでcloseしない。 |
| 6 | branch/worktree、既存custody記録 | 最新tip・固有commit・dirty/ignored/raw・利用者・head/base依存を確認。保全済みかつ不要と確定したものだけ削除し、読み戻しとmainの状態を再確認。 |

バッチ1と2〜5は独立したファイル・問いを選べる。同じ索引や共通runtimeを編集する場合だけ重複を調整する。
文書の共有ファイルを全員で変更することや、全体整理完了を各ワーカーの着手条件にしない。

## 「クリーン」の完了確認

- [ ] 現在の入口から、各研究テーマの仮説・採用実装・保存結果・未解決点・次の実行先へ辿れる。
- [ ] open Issueごとに、未完了の問いか具体的作業がある。完了/重複/移管済みは根拠と継続先を残して閉じる。
- [ ] open PRごとに、固有差分・統合先・必要な局所検証・残る阻害条件を判定済み。古いbaseから新実装を消す統合がない。
- [ ] 不要なreview人数や全員待機を要求する現行案内がない。実際の権限・protectionと変更に必要な確認を使う。
- [ ] 未保存変更や唯一のrawがなく、削除したref/worktreeには保全・未使用・依存確認の記録がある。
- [ ] primary mainと作業終了ツリーがクリーン。統合内容に応じたローカル検証が成功し、未検証境界を明記している。

「作業ツリーの変更ゼロ」「全成果の整理完了」「コンピューター制御の研究達成」は別々の状態として報告する。
新規allocationや実GUI操作は今回の整理では実行していない。

## #8876 crash-owner candidate convergence

[The preserved candidate and counterexamples](../../research/integration/crash_owner_convergence_20261016/README.md)
retain all614 published changed-path head blobs plus seven dependencies without
adopting the old runtime. Exact codec/client AST drops current process/window
sources and permits a new down send after timeout, wrong-ID reply or malformed
record failure. The selected current Fake X owner refuses the decoded lease;
original bound-lease admission/release is the positive control. Three methods /
seven rows per normal/-O mode and saved readback are local construction only.
A35 identity/hashes match; A36/A37 keep their allocation-ID STOP. Continue current
service authority/quarantine and session-death integration under#59; no old
allocation was replayed, and native/game/task-effect qualification remains open.

## Current-owner RPC v2 repair boundary

[Real private sockets plus current strict owner on Fake X](../../research/integration/current_owner_rpc_v2_20261016/README.md)
now preserve source binding and permanently refuse new sends after unknown
replies. Normal/-O each41 methods across5 modules retain26 rows and46 source pins;
blocked release stays unverified. This is an explicit library, not the default
MAP01 owner: external service process/durable receipt, backend custody adapter,
parent cancellation/telemetry and actual session/controller death remain under#59.
The unsupported window observer transfer is refused rather than downgraded.

## Owned process continuation

[Owned service v3](../../research/integration/owned_owner_process_v3_20261016/README.md)
adds the explicit spawned service and exclusive file-fsynced recovery/finish
receipts. Normal/-O each55 methods preserve13 process/inert rows and26 RPC rows.
Client death releases through EOF; unresolved release retains the service even
on publication failure; file success alone never replaces owned-process exit.
The preceding RPC paragraph records its earlier boundary. The remaining#59 work
is selected backend/Executor custody, cancellation/telemetry and actual session
death. This is Fake X construction, with no native/task-effect qualification.

[The actual selected backend/Executor comparison](../../research/integration/owned_owner_executor_boundary_20261016/README.md)
now rejects metadata-only RPC substitution: parent cancellation releases the
local owner during a paused worker, but remote input remains pressed in the fixed
diagnostic window until the worker sends again. Both final cleanup and ordinary
remote completion succeed, which does not repair independent cancellation.
Three cells normal/-O,49 source pins and nine saved-record negatives per mode
preserve this distinction. Next implement the independently serviced intent-bound
cancellation/cause relay, then explicit backend selection under#59.

[The independent cancellation lane](../../research/integration/owner_cancel_relay_20261016/README.md)
now repairs that explicit relay boundary: actual backend/Executor receives the
matching parent-lease release cause while the worker is paused or an ordinary
reply is in flight. Normal/-O each70 methods retain the original counterexamples,
11 new cancellation rows,51 parent pins and frozen loaded sources. First failed
release outcomes remain unverified after late cleanup; wrong generation/control
loss retires admission. Default backend selection is unchanged. Next connect the
production backend custody adapter, preserving first control failure and original
source/cause, then qualify controller/session death and native/task effects.

[The selected-backend owner adapter](../../research/integration/owned_backend_adapter_20261016/README.md)
now connects explicit owned service selection to the actual process-identity
Backend/Executor. Inherited binding reads validated remote geometry, source is
frozen before sends, and whole-program capability checks precede input. A first
unverified control result remains failed through late successful service exit;
the original Executor and a replacement Executor both refuse new authority.
Normal/-O each106 methods across13 modules pass. Parent capture PNG/.ait and child
raw are retained, with independent PNG reconstruction/source/custody readback.
Default V15/controller selection and controller/session death cleanup remain the
next#59 integration; no native input/task/economics qualification is implied.
