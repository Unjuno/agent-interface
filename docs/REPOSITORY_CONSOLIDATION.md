# リポジトリ全体の整理計画

**2026-10-18 r18 — current-main count recheck:** At 14:52 UTC, fetched
`origin/main` was `e5c5448f9ad035657f212135fa4e95d189acda95`. GitHub's paginated
Issues endpoint returned 2,190 issue-like records, including 514 pull requests;
the separately paginated pulls endpoint returned 514 open PRs, leaving 1,676
open Issues. This was a count-only refresh, not an ID-set comparison, semantic
review, ownership check, or closure decision. The latest full open-item metadata
snapshot remains r8 at 14:25 UTC against
`9ff8ab4df85c2359cf5d2055f54586c7e4fe816e`; it is now historical discovery
metadata. Updated the [worker map](WORKER_WORK_MAP.md) and [current objective
entry](CURRENT_GOAL.md) so navigation no longer labels that old SHA as current.
No Issue, PR, branch, worktree, or historical evidence was changed.

**2026-10-18 r17 — current-main family recheck:** At 14:38 UTC, GitHub `main` was `c72c9b186dac29c57ed0d63d92748bfc7ba4d971`. Fresh paginated endpoint counts were 1,676 open Issues and 514 open PRs; this was a count check, not an ID-set comparison or semantic review. The existing #59 MAP01 packet crosswalk was rechecked against this exact main: all six packet PRs remain open at their recorded heads, with no GitHub assignees, and their heads range from 478 to 857 commits behind current main. Empty assignee fields do not prove that work is released, and old heads do not justify closure. The crosswalk now records current-main distances and keeps each read-only audit scope separate. No Issue/PR state, branch, or historical packet was changed.

**2026-10-18 r16 — cleanup baseline at 14:25 UTC:** At that capture, `main` was `9ff8ab4df85c2359cf5d2055f54586c7e4fe816e`. A fresh paginated metadata snapshot had 1,676 open Issues and 514 open PRs, with no ID changes from r7; the [r8 note and CSVs](maintenance/repository-inventory-20261018-r8.md) were the discovery baseline. This is not semantic review or current ownership proof. Semantic status is established one research family at a time from current Issues, current PR heads, preserved reports, and active worktrees. The cleanup has four independent ledgers: (1) idea/hypothesis and its falsifiable remainder, (2) Issue workflow and actual successor, (3) PR code/evidence/owner custody, and (4) branch/worktree recovery. Each reviewed family must link these ledgers or state which link is unknown. Unverified ideas remain searchable; closure requires verified completion of the Issue's own scope, evidence-based rejection, or a real successor that carries the remainder. PR integration/removal requires current diff, tests, unique evidence, and ownership checks. Repository-wide cleanup is complete only when every current open Issue and PR is either family-reviewed or explicitly marked untriaged in a dated inventory, each retained idea is indexed, and each local/remote ref removed has verified custody. This is a progress criterion, not a requirement to close all Issues or to finish all research before work resumes.

**2026-10-18 r15 — #17 process-fence evidence reconciliation:** The main-tree [#7034 result](../research/concurrency/x11_requested_process_fence_17_4d74_20261003/REPORT.md) already supports requested task-process retirement in its frozen four-cell Xvfb scope: keepalive accepted cancellation before the paused child later injected F9; kill/reap before acceptance prevented that suffix, and the fixed prearmed cleanup path released F8. This result is `SCOPED_REQUESTED_PROCESS_FENCE_SUPPORTED` / `HOLD_RUNTIME_PROMOTION`; do not rerun the consumed producer. It does not integrate the owner into the standard MCP caller, prove public cleanup-scope reconstruction (the distinct #7024 allocation ended STOP/METHOD_FAIL), establish a physical release deadline, or cover an unresponsive X server. The next worker seam is process-owner integration plus independently confirmed cleanup and honest aborted-call reporting, recorded in the [safety-control agenda](ideas/safety-control-agenda.md) and [work map](WORKER_WORK_MAP.md).

**2026-10-18 r14 — #17 cancellation acknowledgement seam:** In the current-main guarded MCP caller, a blocked Fake X writer could acknowledge cancel while `review_required` remained false until its next cooperative cancellation check. The retained red/green regression and normal/optimized related-suite results are in [`cancel_ack_review_fence_mcp_20261018`](../research/integration/cancel_ack_review_fence_mcp_20261018/README.md). The bounded change sets the review fence at cancel acknowledgement. It does not retire a blocked writer, retract queued input, establish native/physical release or a deadline, or verify task effect. Treat this as one caller-family item with its original raw and limitations; keep #17 open. Next gate: single-authority writer retirement/fencing and late-send rejection through the selected caller, then separately qualify native release and task effects. This is a family update, not a semantic sweep of the open Issue/PR inventory.

2026-10-15。対象は `Unjuno/agent-interface` 全体とGitHub Issue/PR。コンピューターコントロールの研究を再び見通せる状態にする。

**2026-10-18 r11 — ユーザー確認済みの整理目的:** リポジトリを、大量のワーカーがアイデアを失わず、互いに衝突せず、個別に着手・検証・統合できる状態へ近づける。Issue/PRを一律に閉じたり、件数をゼロにしたりすることは目標にしない。まず研究上の問いごとにアイデア、出典Issue、反対仮説、既存コード/証拠、その限界、依存、次の判別可能な作業を結ぶ。結果が出ていない案は `unverified` 等で実行候補に残し、実際の重複・完了・根拠付き棄却・実在する後継への移管だけを個別の証拠に基づいて処置する。元Issueと歴史的rawは保持し、要約は索引に留める。

**2026-10-18 r12 — #17 current-main update:** PR [#9027](https://github.com/Unjuno/agent-interface/pull/9027) merged at `ce1a0e93c67fafaf4f05bf25e6b86fbe50196ecc`. The selected guarded MCP caller now requires fresh visual review after `execution_failed`, preventing reuse of a still-live alias after uncertain partial input. Its Fake X queued-press expiry case still delivers an already-queued DOWN only after the fixture resumes; cleanup is then verified in Fake X, not under permanent platform nonresponse. The focused module passes 7/7 and four related modules pass 60/60 in normal and optimized Python. The [safety-control agenda](ideas/safety-control-agenda.md) and [work map](WORKER_WORK_MAP.md) link the retained packet and exact limits. Native X behavior, physical release deadline, task effect and matched efficiency remain open; next caller seam is writer retirement/fencing and late-send rejection.

**2026-10-18 r13 — refreshed orchestration inventory:** On current main `f4cd5577ef57a01d7b25a389d877c9d1b3ab9d21`, a fresh paginated GitHub REST read at 13:50 UTC returned 1,676 open Issues (17 pages) and 514 open PRs (6 pages). Membership is unchanged from r6; zero Issue IDs and zero PR IDs entered or left. The r7 CSVs preserve current titles, timestamps, labels, assignees, and (for PRs) draft, author, head/base and head SHA: [Issues](maintenance/open-issues-20261018-r7.csv), [PRs](maintenance/open-prs-20261018-r7.csv). SHA-256: Issues `80fda3cd11f9abeb2c72ca0aa420fe055efb928ae0b319087608c4e25691680b`; PRs `7d9dc08157e03b437b9c9f09513141c32416a07afe79891dfc3cb76ce78bd1da`. This is a membership/metadata refresh, not semantic review or proof of current ownership. The model-economics first batch is no longer pending: #7521 was closed with #8772 as its named, still-open draft successor. Next, select PR batches by research family and compare exact current heads to main; do not treat age, draft state, or an empty assignee/reviewer field as disposition evidence.

今回の収束作業は、(1) main SHAとページング済みIssue/PR一覧を時刻付きで固定、(2) 仮説と証拠で一族を束ねる、(3) 既存担当・PR stack・資源競合を確認して次の仕事を小さく切る、(4) 一族ごとに必要な実験/ローカル検証と統合を進める、(5) 差分・raw・所有者の保全確認後に限り不要refを回収、の順で進める。各バッチは「何件閉じたか」ではなく、保存されたアイデアから現在の根拠と次の独立作業へ迷わず辿れるかで評価する。全件の意味仕分けを、研究を始める前提条件にしない。

**2026-10-18 r10 現在地:** 13:19 UTCのGitHub Search APIはopen Issue 1,676件・open PR 514件を返した。これは件数確認であり、全件本文・コメント・所有者の意味仕分けではない。mainの#9022は#17に関するFake X caller回帰として、選択writer内でDOWNがserver処理前に停止した後のcancel、同一call custody、解除後のcleanup UP、suffix/replay拒否を追加した。関連Issue #17、[safety-control agenda](ideas/safety-control-agenda.md)、[work map](WORKER_WORK_MAP.md)を一つの入口で結ぶ。証拠はFake X caller範囲に限り、物理deadline・writer/server非応答時のrelease・task effect・efficiencyは未達。次の有限な実装判別は、現在のselected callerでsingle-authority writer retirement/fencingとlate-send拒否を接続し、release不確実性をUNKNOWNのまま維持できるかの確認。これは全件整理の完了ではなく、独立したworkerが選べる研究一族一件の更新である。

**2026-10-18 r9 現在地:** 13:05 UTCのGitHub REST全ページ再取得でもopen Issue 1,676件・open PR 514件で、r8の件数から変化なし。これは一覧件数の再確認であり、Issue/PRの全件意味分類や担当確認ではない。入力解放・割込み一族ではmainに統合済みの#9014がFake Xの別connection UPによるfalse-clear反例を、#9015がguarded MCP callerでのblocked release-sync待ち・同一call custodyを記録する。既存の[safety-control agenda](ideas/safety-control-agenda.md)と[ideas/outcomes index](IDEAS_AND_OUTCOMES.md)へ結果と未解決境界を結び直した。物理解放期限・backend非応答時の成功・task effectは未確認で、#17はopenのままとする。

**2026-10-18 r8 現在地:** `2026-10-18 12:33:06 UTC` にGitHub REST APIを全ページ取得し、open Issue
1,676件・open PR 514件をCSV化した。SHA-256とr5からのID差分は[r6 inventory note](maintenance/repository-inventory-20261018-r6.md)、
個別の一覧は[Issue snapshot](maintenance/open-issues-20261018-r6.csv)と[PR snapshot](maintenance/open-prs-20261018-r6.csv)に保存した。
PRはr5から#9007が一件減り、Issue IDの増減はなかった。これは時点付きの一覧であり、本文の意味分類・担当確認・一括closeを意味しない。

同日12:31 UTCに[#9007](https://github.com/Unjuno/agent-interface/pull/9007)をmerge commit
`7b2d531b305e178d84ab599944758a2202cf647a`で統合した。同期後のheadで9 checksすべてsuccess。
Issue #8914に関する二つの保存済みmethod-failure結果とgzip rawを保全し、候補/監査器の再実行はしていない。
結果は`sentinel_not_reproducible` / `HOLD_AUDITOR_METHOD_FAILURE`であり、科学的な合格・失敗やIssue完了を示さないため#8914はopenのまま。

**2026-10-18 r7 現在地:** `2026-10-18 12:24 UTC` にopen Issue一覧17ページとopen PR一覧6ページを
GitHub RESTから取得し、Issue 1,676件・PR 515件を保存した。metadata snapshotのSHA-256とr4からの
ID差分は[refresh note](maintenance/repository-inventory-delta-20261018-r5.md)に記録した。
これは最新のopen-set inventoryであり、本文の全件意味分類、担当照合、Issueの一括処置を示さない。

同期後のmainは`c95caacce56925a03fb5724b6559506fcdac2050`。#9011/#9018/#9009/#9008を統合し、
PR #9008の現行V39 pair-watermark回帰と43件のSHA manifestを確認した。PR #9009の保存T0結果は
mainへ入り、Issue #9004は`NO_INCREMENTAL_AGREEMENT_VALUE`を残すためopenのまま。#59も
ライブゲーム・入力・効果の証拠がないためopenのままで、いずれもIssue全体の完了とは扱わない。

**2026-10-18 r5 現在地:** `2026-10-18 11:47 UTC` のGitHub Search API `total_count` は
open Issue 1,676件、open PR 519件。これは最新件数の照合であり、全件ページ取得・内容判定・
担当判定ではない。過去のCSVは各取得時点の履歴として保ち、現在の完了数には流用しない。

**2026-10-18 r6 現在地:** `2026-10-18 12:10 UTC` にGitHub RESTのopen Issue endpointを22ページ、
open PR endpointを6ページ取得して再集計した。Issueは1,676件、PRは517件。件数は全件本文の
意味判定や担当確認の完了を意味しない。

**2026-10-18 r6 統合記録:** mainは`5dc27cff7ffed6fb218719ddc53b95a901e03d0c`。
整理計画・アイデア台帳・履歴保全を含む[#9012](https://github.com/Unjuno/agent-interface/pull/9012)
に続き、guarded relayのpackage source pinningと回帰テストを含む
[#9011](https://github.com/Unjuno/agent-interface/pull/9011)を12:07 UTCにmerge commit
`5dc27cff7ffed6fb218719ddc53b95a901e03d0c`で統合した。#9011の14 checksはhead
`62b3d1632e7b2ddd0ec2ecbec957d0a51e16a833`上ですべてsuccess。手元にPython 3.12がなく、
対象の`research/live_control`全体を展開すると大容量の保存rawまで含まれるため、今回の環境では
同じローカル再実行を完了できていない。テスト成功の根拠は当該headのGitHub checksであり、
新しいheadでの再実行やライブGUI/model効果の証拠とは扱わない。

同日、統合済み#9011のsource branchは、merge状態とhead SHAを確認し、open PRのhead/baseに
使われていないことを確認した後にremoteから削除した。整理PR #9017のリンク欠落指摘は
sparse-checkoutの未展開パスを現行treeにないと誤認したもの
だったため取り下げ、実tree上で確認し直した記録を#9012に統合した。誤った指摘は監査結果として
再利用しない。全件の意味分類・PR処置は継続中である。

整理用PR [#9012](https://github.com/Unjuno/agent-interface/pull/9012) は元head
`a8cb43d9179fcef27c77170941de3b38b2a2ac41`、base
`13e0b1c1b622085e0007e3ee52a744d1f2b32977`で、当時mainだった
`befe2de22743cfe4a77f513a2876d204f5cf48d5`との比較でmerge conflict状態だった。
同期候補では`docs/REPOSITORY_CONSOLIDATION.md`、`docs/ideas/README.md`、
`docs/ideas/safety-control-agenda.md`の3競合を、両側の追記内容を保つ形で解消した。
同期候補のGit tree上で計画文書の相対リンク23件は全件解決し、生成済み分析indexは
対象848ディレクトリを順序・一意性・欠落なしで列挙した。
現行mainのリンク14件も全件解決している。Fake X A01の保存監査テストは通常/-Oの各4件が通過。
通常のfilesystem index checkerも起動したが、sparse checkoutでは「stale」と表示した後に
兄弟ディレクトリの欠落判定を省略するため、統合候補に対する完全な検証にはならなかった。
候補headの新しいhosted checksも未実行。
同期候補の検証後にPR headを更新し、履歴保全を維持したまま統合可否を再判定する。

**2026-10-17 open-Issue inventory refresh:** a fresh paginated GitHub REST read
returned 1,677 open Issues, compared with 1,678 in r3. The exact metadata and
the three-ID delta are recorded in the [r4 inventory note](maintenance/open-issues-inventory-20261017.md)
and [CSV snapshot](maintenance/open-issues-20261017-r4.csv). This refresh does
not claim all open Issues have been semantically reviewed.

**2026-10-17 open-PR inventory refresh:** the current listing returned 521 open
PRs, compared with 517 in r3. The full head/base metadata is in the
[r4 snapshot](maintenance/open-prs-20261017-r4.csv); the seven-in/three-out
transition is separately recorded in the [delta review](maintenance/open-pr-delta-20261017.md).
The transition review is not a disposition of all 521 open PRs.

**2026-10-18 r4：** 目的はIssue/PRをゼロにすることではなく、研究アイデア・実装・証拠・担当中の仕事の関係を保ったまま、各ワーカーが安全に独立した次の作業を選び、結果を統合できる状態にすること。過去の全件スナップショットは取得時点の資料として扱い、現在数や全件判定の証拠に流用しない。以下の手順で一族ずつ整理し、科学的な問いを閉じる判断とGitHub上の作業状態を分ける。

**2026-10-18の実行記録：** モデル経済性一族で#7521/#8772の現在のPR差分を再確認した。
実装と回帰テストを引き継いだ#8772を後継として残し、重複する#7521はその理由・未解決条件を
コメントして閉じた。#8772はdraft/openでcurrent mainへの追随・再検証が未完、親#57もopen。
実施したのは一族内の重複一件の収束であり、PR全体やIssue全体の整理完了ではない。

## r4 実行計画：アイデアから成果・統合まで

「クリーン」は空のIssue一覧や差分のない作業ツリーではなく、研究の行き先と未解決点が明確で、保存・統合・削除の判断を追跡できる状態と定義する。実行単位は全件一括ではなく、同じ研究上の問いを扱うIssue/PRの一族とする。

| 段階 | 作業 | 残す成果・通過条件 |
|---|---|---|
| 0. 現在地の固定 | mainの基準SHA、最新のIssue/PR一覧、既存worktree/branch、作業中の所有者、無視対象の証拠を時点付きで取得する。古い一覧やassignee欄を現在の割当とみなさない。 | 取得条件とhash付きsnapshot。既存の未コミット変更・原rawを変更しない。 |
| 1. 問いごとの整理 | Issue本文・必要なコメント・関連PR・現行実装/結果を読んで、重複タイトルではなく仮説と判別対象で束ねる。各アイデアに出典、独自仮説、反例、証拠と限界、依存、次の有限な実験、結果による判断、実行先を記録する。 | `docs/ideas/`のテーマ別agendaとIssueへのリンク。保存しただけの案は`unverified`等で残し、研究対象から落とさない。 |
| 2. Issueの状態判断 | Issueを「実行中」「次の検証待ち」「証拠不足/所在調査」「結果あり・親問い未達」「根拠付き棄却」「実行先へ移管」に分ける。完了した作業と上位研究の完了を別に扱う。 | 完了・棄却・実在する後継への移管を確認した場合だけcloseする。後継には残る仮説と次の作業を実際に引き継ぎ、単なる文書保存や古さをclose理由にしない。 |
| 3. PRごとの統合判断 | 各open PRを現在のmerge-baseから比較し、固有差分、mainとの競合、テスト、raw/evidence、依存PR、作者/作業中の所有状態を確認する。stackのmergeとmain統合を区別する。 | 「局所検証後に統合」「修理して継続」「固有部分を移管・保全して終了」「根拠を残して棄却」「所有・証拠確認待ち」のいずれかと、正確なhead/継続先を記録する。重複コードでも独自研究結果は別に保全する。 |
| 4. branch/worktreeの回収 | Issue/PR状態だけで削除せず、現在のtip、追跡外・ignoredファイル、未push commit、原raw、所有者、利用中プロセスを照合する。 | 変更・証拠の保存先と一致を確かめ、使用者がなく、再開先が明示された自分のrefだけを回収する。不明な所有物は一覧化して残す。 |
| 5. 並列作業の入口を整える | work mapに互いに衝突しない有限な作業範囲、根拠、出力先、競合境界を置く。共有GUI/実験資源の排他は実在する取得機構または有効な引継ぎだけで扱う。 | ワーカーが全Issueの精読や中央管理者の応答待ちなしに作業を始められる。実際の保護設定を超える必須レビュアー数・投票・全員待ち・新しいロックを追加しない。 |

### 一族バッチの標準レコード

整理する一族ごとに、次を短く残す。Issue本文やコメントをagendaへ丸ごと複製せず、原記録へのリンクを保つ。

1. **問いと価値**：解決したいコンピューターコントロール上の失敗と、別の問いとして残す理由。
2. **仮説・対立仮説**：何が変われば成功か、単純な代替説明や反例は何か。
3. **既存成果**：mainに統合済みのコード、候補実装、保存結果、ライブ結果を区別し、source SHA・環境・監査・rawを辿れるようにする。
4. **残差と依存**：未達の性質、必要な資源/権限/別チーム依存、判別できない条件。
5. **次の一手**：有限なテスト/実験、比較対象、事前の合否/HOLD、結果で変える判断、担当中ならその実在する所在。
6. **Issue/PR処置**：open継続、実装統合、移管、棄却、closeの根拠。閉じる場合は残る問いと次の実行先も記録。

### 優先順位と最初のバッチ

一族の順番は、(a)主要ゴールへの寄与、(b)既存成果の再利用可能性、(c)最小の作業で仮説を判別できる度合い、(d)依存・実行可能性、(e)大量ワーカー間の競合を減らす効果で決める。古さ、Issue/PR数、レビュー待ち件数は優先度や棄却理由にしない。

最初のモデル連携・比較評価バッチは実施済みである。PR #7521を、未解決の実装・評価を引き継いだopen draft #8772へ理由を記録して移管した。親Issue #57と#8772は未完了として残る。次は最新一覧から一つのPR/Issue familyを選び、本文・必要なコメント・正確なhead差分・証拠・担当中の作業を照合して、処置または次の独立作業を決める。直近のr7一覧は候補発見用であり、全件本文確認済みとは扱わない。既存成果がある一族も、親Issueの問い全体が達成したとは推定しない。

### 全体完了の判定

- 最新時点のopen Issue/PR一覧に対し、**未評価・評価中・処置済み**の件数と取得時刻が一致し、未評価を未評価と表示している。
- 全ての処置済み研究アイデアから、出典、証拠、残る問い、次の実行先または棄却根拠へ辿れる。
- 処置済みPRから、mainに入った変更または証拠の保全先、正確なhead、ローカル検証と限界が辿れる。未解決PRの理由も具体的である。
- 消したbranch/worktreeに未保全の差分・raw・所有権が残らない。確認できないものは削除せず記録する。
- work mapに独立した開始可能な仕事があり、架空の人手ゲートや一つの巨大Issueへの集約でワーカーを停止させない。

この判定は研究ゴール達成や全アイデアの実験完了とは別であり、未達の仮説は整理後も実行対象として残す。

**2026-10-16 r3：** 大量ワーカーが独立した有限の仕事を選べる状態まで整理を続ける。
[r3棚卸し](maintenance/inventory-20261016-r3.json)はIssue 1,678件、open PR 517件。
全件の内容を判定した件数ではない。取得後の処理と未統合変更は
[現在の整理状態](maintenance/consolidation-status-20261016.md)から辿る。

**先行更新（履歴）：** [現在の整理状態・実行順・完了条件](maintenance/consolidation-status-20261016.md)を次の作業の入口とする。
r2時点の取得結果はIssue 1,678件、open PR 518件（[r2取得条件](maintenance/inventory-20261016-r2.json)）。
先行する同日棚卸しはIssue 1,678件、open PR 524件。初回PR 538件との差14件は、直接merge 7件とmergeせず終了7件に分けて照合した。
stack内のmergeはmain統合とは限らない。#5の未完了状態とcompleted closureの不整合も訂正した。
後続の6件は保存先を示して旧PRを終了しており、元PRを直接mergeした件数ではない。
以下の初回棚卸しは履歴として保持し、最新状態や全件レビュー済みの根拠にしない。

**2026-10-17 branch cleanup receipt:** the superseded, unprotected
`research/v39-cancel-batch-race-a01-20261009` branch was removed after its
closed PR and current-main successor were checked. GitHub's retained
`refs/pull/8688/head` still points to the exact source tip. See the
[cleanup evidence](maintenance/branch-cleanup-20261017.md) for this and other
superseded cleanup branches. No tag was pushed, avoiding unrelated
push-triggered workflows.

**2026-10-17 additional remote-ref cleanup:** three redundant branch names were
removed after exact-head and retention checks: two main-merged fixes
([PR #8816](https://github.com/Unjuno/agent-interface/pull/8816) and
[#8763](https://github.com/Unjuno/agent-interface/pull/8763)) and the A07
correction branch merged into the retained A03 source branch by
[#8707](https://github.com/Unjuno/agent-interface/pull/8707). Related local
worktrees and the A03 source branch remain. Evidence is in the
[cleanup receipt](maintenance/branch-cleanup-20261017.md).

## 到達点

- アイデアをテーマ・関係・依存・優先順位で整理し、既存の実装と研究結果につなぐ。
- 各アイデアから、次に行う実験/実装と結果による採用・修正・棄却判断へ進めるようにする。
- 現行実装・実験候補・過去の証拠・運用記録の入口を区別する。
- 重複した案内・旧計画を収束させ、次に必要な文書を一か所から見つけられるようにする。
- 完了、未検証、棄却、停止、保留を混同しない。

## 「クリーン」の完了条件と実行順（r3）

作業ツリーに差分がないだけでは全体完了にしない。次を別々に確認する。

| 対象 | 完了を確認する条件 | 次に行うバッチ |
|---|---|---|
| 入口とオーケストレーション | README→現行ゴール→work mapから、対象範囲・既存Issue・現行成果・未達・次の有限な仕事へ辿れる。古い割当や必須レビュー人数を新しい開始条件にしない。 | #9027/#9028の結果を現行mainで照合済み。r7 inventoryを追加。次は各themeの次の独立仕事と衝突範囲を定期的にmain基準で更新する。 |
| 研究アイデアとIssue | 各テーマの独自仮説、反例、出典、依存、既存成果、最小検証、実行先が結ばれる。保存しただけの未達は未達と分かる。 | 視覚・安全制御・モデル比較などの既存agendaを維持。未評価を明示しつつ、work mapのtheme単位で本文/コメントを読み、独自の残差を検証へつなぐ。全件を一つの親Issueへコピーしない。 |
| PR | 全open PRに、採用候補・修理・証拠保全・後継へ移管・根拠付き棄却の処置がある。統合/終了の正確なheadと継続先を辿れる。 | r7の514件から一族ずつ意味仕分けする。最初の現行例は#59のMAP01 six-packet family crosswalk。各packet監査後、exact head・固有raw・所有・current-main差分を確認し、そのpacket単位で継続/統合/移管/終了を判断する。 |
| branch/worktree | 固有変更・raw・未追跡/無視対象・依存PR・使用者を確認し、残すものには理由と所在、消すものには保全先と一致したtipの記録がある。 | まず自分の統合済みrefのみ回収。他者/所有不明の領域は削除せず、照合対象として残す。 |
| 実装・検証 | 採用するコードが現行mainに接続され、必要なローカル検証と限界が残る。旧sourceのPASSを移植しない。 | 未統合のV15選択変更は専用branchに保全。証拠パケットの読戻し後に独立した統合として扱う。 |

順序は **入口の矛盾修理→一族の読解とアイデア整理→固有差分/証拠の保全→ローカル確認→統合→後継付き終了→不要ref回収**。
一族ごとに区切って繰り返し、最後に一覧との差分を照合する。全件整理を研究開始条件にしない。
新しいワーカーは[work map](WORKER_WORK_MAP.md)から一つの範囲を選び、既存の記録先に
対象・branch・出力先・次の成果を短く残す。共有indexの編集と同じコード範囲だけを調整する。
この計画は新しいscheduler、投票、全員待ち、実行資源の割当を作らない。

各バッチの成果は「何件閉じたか」だけでなく、整理した仮説、mainで再利用できる成果、
未解決点と実行先、証拠の不足、回収した自分のrefで確認する。

**方針訂正：** PR #8924でアイデア保管を理由に#3/#5/#8を閉じたが、ユーザーの目的はアイデアを整理して研究を行うことである。3件は再オープンした。未着手・古い・未担当・文書化済みという理由だけで実行対象から外さない。整理の成果は研究判断と実行への接続であり、close件数ではない。

## 現状の棚卸し

取得時のopen Issueは **1,678件**、open PRは **538件**。Issueのうち355件はタイトルが`[Research]`で始まり、1,676件にはGitHub assigneeがない。ただし、assignee空欄は未担当の証明にはならない。

全件の番号・タイトル・URL・更新時刻・ラベル・assignee・open PRのclosing参照を[Issue棚卸し](maintenance/open-issues-20261015.csv)に保存した。関連PR欄はGitHubのclosing参照だけであり、本文・branch・コメントでの関連や実行担当を網羅しない。棚卸しは取得時のスナップショットで、現在の実行権やclosureの可否を自動判定するものではない。

既存の`docs/ideas/README.md`には保存形式があるが、集約されたエントリはゼロだった。最初の移行は[視覚表現・アドレス・フィードバックのアイデア](ideas/visual-interface.md)。#3/#5/#8の原文も保存し、未検証の着想として残す。

## 1. Issueを整理する

次の4種類へ、人が根拠を確認して振り分ける。タイトルや古さだけで閉じない。

| 種類 | 保存先・扱い | closeの理由 |
|---|---|---|
| 今進める作業 | Issueを残し、目的・最小の次の実験/変更・合否条件・担当がいる場合はその所在を書く | 未完了なので残す |
| 次に検証するアイデア | `docs/ideas/`へ仮説・既存証拠・残差・依存・最小実験・判定条件を整理し、実行するIssueと結ぶ | 保存しただけでは閉じない |
| 完了した作業 | 結果・実装・検証・限界をリンク | `completed`。仮説や上位目標の達成とは分ける |
| 重複・後継へ移行 | 集約先に元の独自の仮説・検証項目・次の作業を引き継ぐ | 実行先を確認してから閉じる。単なる文書リンクでは不十分 |

各バッチで、本文、コメント、関連するopen/closed PR、現在の実装・証拠を対象に応じて確認する。進行中の実験、未解放資源、未保存raw、担当中の修理があるIssueは、その状態を引き継ぐまで残す。包括的な親課題に子Issueを丸ごとコピーせず、リンクと短い不足点を置く。

closeコメントには **理由、保存先、科学的状態、残る問い、その実行先** を書く。単なるアイデア保管を`completed`にしない。棄却する場合も、不要/不適切と判断できる根拠を残す。後継課題は実在する不足を扱う場合だけ作り、整理のためだけにIssueを増やさない。既存の議論・raw・失敗記録は消さない。

最初のバッチは#3/#5/#8。[実行計画](ideas/visual-interface-agenda.md)に沿って既存成果との照合、残差の検証、比較実験へ進める。それ以外の1,675件は未判定であり、この棚卸しだけでは閉じない。

次のバッチでは[#2/#10/#14/#15/#16/#17の安全制御・証拠・回復](ideas/safety-control-agenda.md)の関連部分を整理し、公開経路のblocked-I/O残差をFake Xで実行確認した。各Issue全体の達成や、残り全件の判定を済ませたという意味ではない。

## 2. 研究の見取り図を作る

既存の`docs/IDEAS_AND_OUTCOMES.md`、`docs/RESEARCH_MAP.md`、`docs/RESEARCH_ISSUE_INDEX.md`、`RESEARCH.md`を入口として、次のテーマに研究項目をまとめる。

1. 観測・視覚表現・対象指定
2. 入力権限・期限・解放・対象世代
3. 環境応答・タスク効果・有限回復
4. モデル連携・待ち時間・トークン・資源比較
5. アプリ/ゲーム別の移植・検証
6. 実行基盤・配布・プラットフォーム
7. 実験方法・証拠・統計

テーマの一覧は一つに集約し、各テーマに「解決したい操作上の問題」「アイデア」「既存の実装/証拠」「残る問い」「優先順位と理由」「依存」「次に行う最小実験」「結果が変える判断」「実行するIssue」を置く。似た専門用語というだけで仮説を同一視しない。未確認は未確認として照合作業へ結び、放置や棄却と扱わない。

優先順位は、コンピューターコントロールの不足を減らす効果、既存成果の再利用、最小の検証で得られる判別力、依存と実行可能性で決める。全体が整理されるまで、着手可能な実験・実装を止めない。各バッチは少なくとも一つのアイデアを具体的な検証へ進め、結果をテーマの見取り図に戻す。

## 3. 文書とディレクトリを整理する

| 用途 | 入口 | 整理方針 |
|---|---|---|
| プロジェクトの説明 | `README.md` | 目的、利用可能なもの、最短の案内だけを置く |
| 直近の優先順位 | `docs/CURRENT_GOAL.md` | 長い履歴を分離し、少数の次の作業と未完了条件へ縮める |
| 採用実装 | `runtime/`、`src/`、architecture文書 | 実際の呼出し経路と対応プラットフォームを確認して案内する |
| 実験・候補実装 | `research/`、`experiments/`、`construction/` | current/候補/歴史を明示。移動前に参照とsource hash依存を調べる |
| アイデアと実行計画 | `docs/ideas/` | 仮説・出典・既存成果・依存・次の検証・判定条件をテーマ別に整理 |
| 証拠 | `RESEARCH.md`と各実験のraw/audit | 原本を維持。移動や削除はcustody・再現性を確認した後に限定 |
| 運用・保全 | `docs/maintenance/`と既存窓口 | 時点つき棚卸し。現在の禁止や担当と混同しない |

入口の重複を先に直し、巨大なファイル移動を最初に行わない。凍結ソース、manifest、相対リンク、公開URL、テストの参照を壊す変更は別の実装作業として扱う。

## 4. PRとbranchを収束させる

538件のopen PRも、実装待ち、レビュー/統合待ち、後継に吸収済み、証拠保全のみ、放棄済みへ分ける。merge済みの同等変更と検証済み証拠がある場合、重複PRは保存先を示して閉じる。未統合コミットと未追跡ファイルを保全する前にbranch/worktreeを削除しない。

マージ判定には実際の権限・保護条件と変更に必要なローカル検証を使う。この整理計画から新たな必須レビュアー人数や合議条件を追加しない。Issueを閉じることとPRをmergeすることは別に判断する。

## 実行順と完了確認

- [x] 全open Issue/PRの初回取得。Issueは1,678件、PRは538件。
- [x] 既存のアイデア保存先を確認。#3/#5/#8を原文つきで集約。
- [x] 集約文書をmainへ届けた。先行した#3/#5/#8のclosureは訂正し、再オープン。
- [x] #3/#5/#8の実行計画を作り、#5の最初のCLI compositionを実行して結果を記録した。全アイデアの検証完了ではない。
- [ ] テーマごとに残りのIssueを確認し、アイデア・既存成果・優先順位・実行項目を結ぶ。
- [x] 現行ゴール・統合計画・quickstartを短い入口へ分離し、Git原文を同じdocsディレクトリ内の履歴として保存。作業選択は[worker work map](WORKER_WORK_MAP.md)へ接続。
- [ ] 残りの研究テーマと入口を照合し、各アイデアを既存成果・次の検証へ結ぶ。
- [ ] PRを実装差分・後継・証拠所在で分類し、重複と統合待ちを減らす。
- [ ] 保全済みの不要branch/worktreeを整理する。

バッチごとに、確認したアイデア、再利用できる成果、新しく実行した検証、結果で変わった採否・次の作業を残す。未実行の計画は実行済みと数えない。最終的には、任意の研究項目から現在の実装・証拠・未解決点・次の作業へたどれ、優先するアイデアが実際に検証されていることを確認する。

## 進捗と次の整理対象

[Calc移植の証拠と次の課題](../research/live_control/calc_saved_convergence_20261016/README.md)では、
古い1ケース時点のREADMEから、完了した4ケース・保存ファイル採点・joint usageへ入口を接続した。
保存済み監査を通常・最適化Pythonで再確認し、Windowsのmutation overlayのパス差を別runnerで修理した。
原本568ファイルは変更せず、経路別費用・有限回復・現行sourceでのライブ検証は未達として残す。

[カバー取消の収束記録](../research/doom/v39_cover_cancel_convergence_20261016/README.md)では、
未統合PR #8384の15ファイルを元のblobのまま保全し、重複ケースを見逃す監査の指摘を
別版で検証した。現行テストの古いfixtureも修理し、planner割込み応答待ちが解放失敗の
確認を止める残差を新たに判別した。過去の構成PASSを実機の解放・回復PASSへ読み替えない。

[2026-10-15の統合・保全記録](maintenance/consolidation-progress-20261015.md)に、mainへ届けた修理、PR stackの収束、ローカル作業ツリーの未統合変更と保全先をまとめた。mainがクリーンであること、研究候補が保全済みであること、リポジトリ全体の整理完了は別々に確認する。

Dockerless local-iteration documentation is also reconciled: successor [#8882](https://github.com/Unjuno/agent-interface/issues/8882) delivered the residual-workflow inventory in merged [PR #8884](https://github.com/Unjuno/agent-interface/pull/8884), at [`research/outputs/wsl3-docker-residual-inventory-20261012.md`](../research/outputs/wsl3-docker-residual-inventory-20261012.md). The inventory keeps native WSL as the ordinary local route and WSLc for eligible image-bound work, while retaining Docker-specific frozen recipes; it makes no performance or security-equivalence claim.

**2026-10-17 PR reconciliation (snapshot at catalog head `e75b63224b0d37b0b896d1c0b66a80ef51e0e3c4`):** [PR #9005](https://github.com/Unjuno/agent-interface/pull/9005) and [PR #9012](https://github.com/Unjuno/agent-interface/pull/9012) were open, both `CLEAN`, with all reported required checks passing and no recorded review decision. They share only `docs/IDEAS_AND_OUTCOMES.md` and `docs/ideas/README.md`, with no duplicate newly added outcome IDs. PR #9005 retains the canonical family notes for constrained diagnosis, privacy discovery, lossy evidence, joint reserves, and macro validation; #9012 omits those copies and keeps its distinct entries. #9012 adds concise proposal summaries for 49 open Issues that had been represented only by machine-readable inventory; the summaries describe the questions without setting allocation status or execution authority. Later head and review state should be read from GitHub; neither PR was recorded as merged in this snapshot.

**2026-10-17 open-PR delta:** a fresh GitHub read returned 521 open PRs, up from 517 in the 2026-10-16 r3 inventory: seven entered the open set and three left. The [delta review](maintenance/open-pr-delta-20261017.md) classifies those ten transitions. It preserves #8714's branch because open #8720 still uses it as its base and records the two closed V39 PRs against their existing successor/custody notes. Among newly open PRs, #9006 remains a draft: native-mcp reports four failures in relay/source-dependency/handle-bridge tests, and the native Win32 fixture returns `release_unverified` where an existing test expects `completed`. Its diff adds tests only, so it does not demonstrate verified release behavior.

**2026-10-17 issue/branch reconciliation:** A fresh open-Issue export returned 1,677 issues. A direct-reference scan across current `main`, PR #9005, and PR #9012 found all 1,677 referenced and zero unreferenced. This covers current open Issues, not every historical closed issue or every PR. The citation-audit subset remains 49 Issues; separate #8872 and #8870 notes preserve their distinct unverified proposals, with #8872 retaining #5776's failed early-warning result. Nine additional closed/superseded remote branch names were removed after exact-tip, worktree, protection, open-PR and pull-ref checks; the receipts are in [the branch cleanup log](maintenance/branch-cleanup-20261017.md). This remains progress, not repository-wide completion.

**2026-10-17 PR overlap correction:** A fresh file-list comparison at #9005 head `63d4d22f54adb626920b2d547a587421e63bbbfe` and #9012 head `11286bcda198719013adf6e8daeba025b8e08385` found a third shared path, `docs/ideas/skill-conditioned-terminal-event-memory.md`, in addition to the two indexes. #9005 contains the fuller #8886 proposal; #9012's duplicate page and index entry were removed. The shared outcome index had 55 Issue IDs with differently worded rows in both PRs. #9012 now combines both summaries for all 55 IDs, preserving distinct outcomes and qualifications in one row; it also moved the #8887, #8889, #8897, #8898, and #8900–#8905 research proposals out of the engineering/operations and early-history sections into `Recent open ideas`. That section has no repeated primary Issue IDs, and five byte-for-byte repeated rows were removed earlier. The corresponding 55 older rows still remain in #9005 and need cleanup before both PRs can integrate without duplicate Issue entries. The #9005 update worktree at `/private/tmp/agent-interface-9005-update` was still dirty at its original HEAD during this review and was left untouched.

**2026-10-17 overlap follow-up:** PR #9005 advanced to `b0e2ff0b137ef9add65398e4ecc8e06f39ad11f7`, removing the 55 newly added primary Issue rows shared with #9012. A comparison of both current PR diffs against `main` now finds zero shared changed primary Issue IDs. The focused index check passes locally; hosted checks for #9005 are queued and neither PR has a recorded review decision. The older `/private/tmp/agent-interface-9005-update` worktree remains untouched. Its #8668 agenda update is now identical to the #9005 file at `880c6b63036`; its stale #8631/#8668 index additions are superseded by the fuller rows already present on the updated #9005 head.

**2026-10-17 PR merge preview:** `git merge-tree --write-tree` across current #9005/#9012 heads found content conflicts in `docs/IDEAS_AND_OUTCOMES.md` and `docs/ideas/README.md`, despite zero overlapping changed primary Issue IDs. Keep the conflict boundary explicit; resolve both shared indexes in the authorized integration change before claiming the pair can merge cleanly.

**2026-10-17 catalog branch integration:** The #9012 branch now incorporates #9005 head `880c6b63036fa297d4a5c0a68498edf94e1b48d4`. The shared indexes were resolved by retaining disjoint issue rows, selecting the fuller #59 evidence summary, combining the complementary #6468/#6284/#5521 outcomes, and removing repeated rows and page links. Local audit found 525 primary Issue rows with no duplicate IDs, 122 distinct idea-page links, and 283 resolving relative links; the research index check passed with 845 retained result/failure directories. This is a reviewable PR-branch integration, not a merge to `main`; hosted checks and review remain outstanding.
