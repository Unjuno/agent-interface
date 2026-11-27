# モデル連携・比較評価のアイデアと次の実行

2026-10-16。照合main `1ece47014d05db898bf73afcd722a14524462e15`。
目的は、同じモデル・課題・正しさ条件で、統合経路が実際に有益かを判別すること。
アイデアをまとめたことや、人工データの計算が通ったことを、実測の達成にしない。
[本文・コメント等のAPI字段スナップショット](sources/model-economics-20261016.json)と
[今回の会計採用比較・保存結果照合](../../research/integration/model_economics_convergence_20261016/README.md)を参照。
全repoの精査ではなく、下の5課題と2候補に限定した整理である。

## 独立した問いを残す

| 実行する既存Issue | 独自の問い | 既存成果と状態 | 次の有限な実行・判定 |
|---|---|---|---|
| [#57](https://github.com/Unjuno/agent-interface/issues/57) | 高能力モデルを固定し、正しさを保った統合経路の実トークン・時間・総資源を比較できるか。 | 統合経路と失敗会計の構成成果はある。実provider会計、独立task effect、同条件比較・移植を単体PASSで置き換えない。**全体は未達**。 | 選択caller/実task adapter内の全呼出しを一つの試行台帳へ接続し、実効果/未知・失敗と費用を対応させる。適格な新規比較ではbaseline/arm、課題、モデル設定、取得/修理/失敗費用を凍結する。 |
| [#3311](https://github.com/Unjuno/agent-interface/issues/3311) | 一つのdesktop workflowでcold取得→warm利用→依存無効化→有限修理→再利用を通して評価できるか。 | #57全体と同じ問いではなく、その一つの統合実行単位。本文と135コメントを保存したが、この整理は全過去allocationの再監査ではない。 | 一つの独立採点可能workflowと現在caller/backend/effect-readerの対応を固定する。取得・warm・無効化・修理の全試行を残し、効果未確認や使用量欠落ならHOLD。古いallocationを再実行しない。 |
| [#5827](https://github.com/Unjuno/agent-interface/issues/5827) | 同じ推定対象への妥当な集計選択で結論が変わるか。別の推定対象とのトレードオフは何か。 | **合成T0はメソッド限定結果**。#5864は現在MERGEDでmainに原11ファイルがある。保存rawを元監査で再読取し5/5一致。原RUNのハッシュ不一致は末尾LF一個と特定したが、原本は不一致のまま保全。実経路の頑健性は未検証。 | 適格な同条件cohortができたら、主推定対象を維持して同一対象の感度分析群を登録する。課題完了、safe stop、model wait、人の残作業は別の結果として報告。副指標の多数決で主結果を救済/拒否しない。 |
| [#6227](https://github.com/Unjuno/agent-interface/issues/6227) | 変更後の再検証・停止/代替費用を含めると、warm時点の経路順位が変わるか。 | 原T0の**FAIL_AUDIT_GATE_ASSERTION**と、保存結果だけを読む後続監査の**PASS_AUDIT_SUCCESSOR_SCOPED**がコメントで報告されている。費用と変更は合成設定。今回、報告された2prefixにmain上の原packetを確認できず、独立raw読戻しは未実施。不在全般の証明ではない。 | 原候補/失敗監査/後続監査の保管先を特定してバイト照合する。再生ではなく保全から始める。実app変更に適用する際はdirect経路の再検証費用も同じ変更・課題scheduleで計上する。 |
| [#8859](https://github.com/Unjuno/agent-interface/issues/8859) | 必須の検証作業と余分な作業を区別した効率尺度は、正しい結果同士の利用者選好を説明するか。 | **未検証の提案**。取得時コメント0。raw呼出し数や人の最短手順だけでは、必要な安全/effect検証を余分と判定できない。 | まず成功・証拠・解放条件を満たす比較可能なtrace corpusがあるかを監査する。必須/任意の区別と判断者間一致が成立しなければUNCERTAIN。成立後に別途選好校正を行い、hard gateを重み付き得点へ溶かさない。 |

#6227の変更後維持費は初回compile/取得費と区別し、#8859の選好校正は実token/時間の測定と区別する。
これらを「効率化の重複」として一括棄却しない。5件は未達の独自部分を持つため、この整理だけでは閉じない。

## 会計PRの収束判断

**2026-10-18の再照合・処置：** #7521と#8772を最新のGitHub状態で再取得した。
どちらもdraft/openだったため、差分を比較し、#8772に#7521の実装・回帰テストが保持され、
現行protocol runnerへの登録が加わっていることを確認した。重複元#7521は、
後継#8772と未解決の再検証条件をPRコメントに明記してclosedとした
（[closure comment](https://github.com/Unjuno/agent-interface/pull/7521#issuecomment-6249421799)）。
#8772はopen/draftのままであり、current mainへの再適用・必要なローカル検証・実際の保護条件の
確認が終わるまで統合済みと数えない。#57はopenで、統合効率・実provider会計・独立タスク効果の
未達を維持する。この処置は重複PRを一件に収束しただけで、機能や研究課題の完了ではない。

[#7521](https://github.com/Unjuno/agent-interface/pull/7521) head `82656ac75d9fed59ec1a349b89ccf6d29cb2a3c9` と
[#8772](https://github.com/Unjuno/agent-interface/pull/8772) head `d4dc786cac84f542ea862cf830ac3c9911e67f98` の
model実装と2-methodテストはそれぞれ同一バイト。runnerは異なり、旧runner全体を移植しない。
現在mainには別の `GroundingCallError` 修理とactual shared callerの9-method試験がある。

同じ現行依存・inert clientで、実装×テスト契約を比較した。通常/-Oは同じ結果だった。

| 実装 | テスト契約 | 観測結果 |
|---|---|---|
| 現行main | 現行caller契約9 methods | 9 PASS、10保存行 |
| 旧#8772全model blob | 現行caller契約9 methods | 2 FAIL：await timeout後の既知ID、completed result保存失敗後の既知ID/会計。10保存行 |
| 旧#8772全model blob | 旧#8772契約2 methods | 2 PASS |
| 現行main | 旧#8772契約2 methods | 6 subtest errors：`thread_id`属性、malformed usage時の旧failure-file期待との差。6 methodsの失敗という意味ではない。 |

これは旧PR全体を旧依存で再評価した結果でも、現在へ部分移植できない証明でもない。
**暫定提案：旧module丸ごとの置換は採用しない。#7521は固有情報を保全した後に重複元として終了する候補、#8772はdraft/openのまま残る差のsalvage判断へ狭める候補とする。** 2026-10-18時点で両PRはdraft/openであり、GitHub上の処置はまだ行っていない。この提案は保存先・差分・ローカル比較を確認した結果で、PR作者の所有・未公開変更がないことの確認やmainへの統合を意味しない。
両headの全変更ファイル、原metadata、raw出力、最初の疎checkoutによる失敗を今回packetに保存した。
原branchは所有/固有local証拠の確認前に削除しない。

#8772の次の有限な判断は、現行例外/callerにthread IDやterminal usage-error/publication診断を
必要な範囲で渡すか、既存protocol記録で足りるかの確認である。旧`wait_ns`はterminal-returnまで、
現行失敗の`wait_ns`は保存/検証の失敗を含むadapter区間で、同じ名前でも終了点が異なる。
必要なら別々に命名し、現行await/保存失敗の会計を失わずに差分だけを接続する。
古い「非作者レビュー人数待ち」は現在の開始条件にしない。実際の保護条件と必要なローカル確認に従う。

## 実行順

1. #57/#3311の選択実装・全試行会計・独立効果の不足を優先する。今回の比較は、その統合時に旧修理で会計を後退させないための局所確認。
2. #5827の原バイト差を記録したまま、適格cohortに適用する主/副推定対象と不足rawを先に定義する。
3. #6227は原結果の保全所在、#8859は適格traceの有無を先に判別する。既存結果が不足するからと新しい合成研究を無制限に増やさない。
4. 合否・未知・失敗・採否と次の実行先を、このagendaと元Issueへ戻す。保存したことを研究完了としない。
