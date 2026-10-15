# 整理の進捗と未完了項目

2026-10-15。確認基準はmain `b44a95453fbcfeeb41fff6a7e07cc733f2402e1b`。この記録は整理の進捗であり、研究全体の合格やワーカーへの割当ではない。

## mainへ統合したもの

| 変更 | 到達点と限界 |
|---|---|
| [#8924](https://github.com/Unjuno/agent-interface/pull/8924)、[#8925](https://github.com/Unjuno/agent-interface/pull/8925) | 全open Issue/PRの初回棚卸しと#3/#5/#8の研究計画。アイデア保管だけを理由としたclosureを訂正し、3件とも再オープン。残るIssue群は未判定。 |
| [#8926](https://github.com/Unjuno/agent-interface/pull/8926) | 実際のv10/v15 CLIで8条件の配信composition。保存・選択・flush・モデル受信を区別。GUIやモデル受信の成功ではない。 |
| [#8927](https://github.com/Unjuno/agent-interface/pull/8927) | 公開guarded X11の問い合わせ後、期限切れの新規押下を拒否する修理。停止した問い合わせ中の有限解放は未検証。 |
| [#8928](https://github.com/Unjuno/agent-interface/pull/8928) | ゴール・統合計画・quickstartを短くし、旧Git原文を履歴へ保存。[作業マップ](../WORKER_WORK_MAP.md)で有限な作業を選べる。 |
| [#7981](https://github.com/Unjuno/agent-interface/pull/7981) | 59ファイルの凍結証拠と公開時の改行差分を照合して統合。結果はFAIL_CROSS_CLIENT_ISOLATIONのまま。新規実験やPASSへの変更なし。 |
| [#8929](https://github.com/Unjuno/agent-interface/pull/8929) | settle timeout後の予定holdを停止し、期限後のcapture返答をquiet成功にしない。修理前に3件を再現し、関連15件が通常・最適化Pythonで成功。実Executorとinert backendによる構成試験であり、blocked I/Oの割込みや物理解放期限を証明しない。 |
| [#8931](https://github.com/Unjuno/agent-interface/pull/8931) | mainのsource-attribution監査で5件のエラーを再現。改行属性の指定順により変換されていた凍結ソース3件を元Git blobから復元した。監査18件が通常・最適化Pythonで成功し、20件のsource hashはindexからのcheckout後も一致。元freeze/result/auditは不変。 |
| [#8932](https://github.com/Unjuno/agent-interface/pull/8932) | 古い準備作業ツリーに残っていた708ca固定ソースの未公開回帰記録11ファイルを既存probeへ追加。原checksum10件、exit 4件、source pin 2件を照合。過去の記録であり、新規ライブ実験ではない。 |

追加照合ではmain `4062116ea4d70f1904cdea9669c8c2226acd7b9d`のcontroller・planner・release関連9スイート98件が通常・最適化Pythonで成功した。この構成試験を、blocked I/O中の有限解放やライブ回復の証明には使わない。

## PR stackを収束させたもの

[#8723](https://github.com/Unjuno/agent-interface/pull/8723)を[#8707](https://github.com/Unjuno/agent-interface/pull/8707)へ、#8707を親[#8701](https://github.com/Unjuno/agent-interface/pull/8701)へ統合した。v2/v3の26テストは通常・最適化Pythonで成功し、両merge後のtreeは検証したtopと一致する。

**#8701は未統合。** A07の2,358 rawファイルはこのWindows側にない。保管元でraw/hashとv3の保存済みepisode監査を確認する必要がある。元のFAILと報告されたHOLDを維持し、syntheticテストからライブPASSへ読み替えない。消費済み実験を再実行して補わない。

## ローカル作業ツリーの保全

14作業ツリーを確認した。primary mainと整理用作業ツリーはクリーンで、primary mainも上記基準へfast-forwardした。クリーンな作業ツリーにも未統合commitはあり、削除可否は別途確認する。

`pr8771-currentmain-integration`にあった11追跡変更と400未追跡ファイルは、元base `993f96e61a5a5f44496295836097dc68b1f1255f`を親とするローカル保全commit `50a863b314a3454d6b8e293d9d6523ff943c0808`へ保存した。保全refは`preserve/vizdoom-local-state-20261015`。増分bundleのSHA256は`8d1b11d8c42b048169fa58f0a1bbb068ca6967b8960fe119253816c4c4036c89`。411ファイルと無視対象456ファイルを再照合し、ソースを書き換えずindex/branchを保全commitへ揃えた。作業ツリーはクリーンだが、世代確認・scorer・過去実験はmain未採用の候補である。

残る4作業ツリーも、未保存・無視対象のファイル、binary diff、元HEAD/statusを外部ZIPへ保全し、全ファイルをハッシュ照合した。元ファイル・HEAD・statusは変更していない。

| 作業ツリー名 | 未保存差分 | 次の処理 |
|---|---|---|
| issue59-v39-renewal-invalidation-a01 | 未追跡7ファイル。無視対象込み54ファイルを保全 | probe本体・初回結果はmainと一致（sourceは改行差のみ）。古いREADME/checksumの独自原本も外部保全済み。作業ツリーの引退処理はまだ行っていない。 |
| issue59-current-main-live-prep | 未追跡27ファイル。無視対象込み101ファイルを保全 | 既存mainと一致する記録と、未公開708ca記録を区別し、後者を#8932で追加。旧READMEの時点付き状態は現行割当として使わない。作業ツリーの引退処理は未実施。 |
| issue59-main-576d | controllerの追跡変更1件。現在0バイト、元HEADから1,435行減 | 0バイト原本も保全済み。意図した変更か中断による破損かを履歴と照合し、判定前に完了扱いしない。 |
| issue59-v39-guard-crossing-replay-a01-20261008 | 追跡変更5件、未追跡4件。無視対象込み16ファイルを保全 | audit v2/v3、freeze変更と公開済み証拠の一致を確認して統合を判断する。 |

外部保全の所在は、この作業ホストの`C:\Users\user\Documents\Codex\2026-10-03\new-chat-2\outputs\repository-consolidation-20261015\`。`vizdoom-dirty-preservation/PRESERVATION.json`、`CLEAN_WORKTREE.json`、`snapshot.bundle`と、`remaining-worktree-preservation/SUMMARY.json`、各作業ツリーの`MANIFEST.json`/`files.zip`/`changes.patch`に復元情報がある。これらはローカル保全であり、この文書だけで他ホストから復元できる公開rawではない。

## 次の有限な整理

1. 上の4作業ツリーの差分を既存成果へ照合し、独自の未公開証拠を届ける。消失や0バイト化を空の変更として消さない。
2. #8701を保管元の保存済みrawで監査し、結果に従って統合または修理する。
3. 未判定Issueを一つの研究テーマずつ読み、仮説・既存結果・依存・次の実験を[整理計画](../REPOSITORY_CONSOLIDATION.md)へ接続する。保存だけで閉じない。
4. 各PR/branchの固有差分と依存を照合し、検証済み統合と重複解消を進める。別作業ツリーのHEADがmainに含まれるだけでは、未保存・無視対象・現在の利用まで消してよい根拠にならない。

全体の整理は未完了。入力解放・task effect・有限回復・効率比較の残差も継続している。新しい必須レビュー人数や、整理が終わるまで全ワーカーを止める条件は追加しない。
