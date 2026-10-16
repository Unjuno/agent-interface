# 現在の整理状態と次の実行順

2026-10-16 JST。基準main `ed87095fda10147ec91d247eb382b4ffbafd3495`。
目的は、多数のワーカーが研究内容を失わず、独立した仕事を選び、検証済み成果を統合できる状態にすること。
整理全体は未完了であり、全Issueを閉じることを完了条件にしない。

## 後続の現在地（r2）

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
