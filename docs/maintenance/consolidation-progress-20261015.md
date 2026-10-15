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

14作業ツリーを再確認し、全件で追跡変更・未追跡ファイルがゼロになった（2026-10-15 12:32 UTC、基準main `734543f4488b30b1dcae52f7f9d6dd139db867fe`）。primary mainもその基準へfast-forward済み。クリーンな作業ツリーにもローカル保全commit・無視対象・未採用の研究候補はあり、全成果のmain採用や削除可能性とは別である。

`pr8771-currentmain-integration`にあった11追跡変更と400未追跡ファイルは、元base `993f96e61a5a5f44496295836097dc68b1f1255f`を親とするローカル保全commit `50a863b314a3454d6b8e293d9d6523ff943c0808`へ保存した。保全refは`preserve/vizdoom-local-state-20261015`。増分bundleのSHA256は`8d1b11d8c42b048169fa58f0a1bbb068ca6967b8960fe119253816c4c4036c89`。411ファイルと無視対象456ファイルを再照合し、ソースを書き換えずindex/branchを保全commitへ揃えた。作業ツリーはクリーンだが、世代確認・scorer・過去実験はmain未採用の候補である。

残る4作業ツリーも、未保存・無視対象のファイル、binary diff、元HEAD/statusを外部ZIPへ保全し、全ファイルをハッシュ照合した。その後、0バイトのcontrollerだけを自身の元HEADから復旧した。他の3作業ツリーはソースを書き換えずローカル保全commitへindex/branchを揃え、検証済み増分bundleも保存した。Gitによるtext正規化とは別に、正確なraw原本はZIPへ保持している。

| 作業ツリー名 | 未保存差分 | 次の処理 |
|---|---|---|
| issue59-v39-renewal-invalidation-a01 | 元の未追跡7ファイル。無視対象込み54ファイルを保全 | probe本体・初回結果はmainと一致（sourceは改行差のみ）。保全commit `fb85369328f20caf8d079c688d5cfa0db11320d6`でクリーン。古いREADME/checksum原本も保全済み。 |
| issue59-current-main-live-prep | 元の未追跡27ファイル。無視対象込み101ファイルを保全 | 既存mainの記録と未公開708ca記録を区別し、後者は#8932で追加。保全commit `dc5c1bc3721ad03ccb749fdb04bd2c97d97c98a6`でクリーン。旧状態は現行割当として使わない。 |
| issue59-main-576d | controllerの元追跡変更1件。0バイト原本と差分を保全 | 元HEAD `2d16f5ff6387e3cdc8a6bb985c1b7a55bdcc0a34`から83,848バイトを復旧。SHA256 `c4004089e82a6e6114ea6a9451fe5e9336da8b10c9f46aa02fcaa36f8a945e95`と構文を確認。HEAD不変でクリーン。 |
| issue59-v39-guard-crossing-replay-a01-20261008 | 元の追跡変更5件、未追跡4件。無視対象込み16ファイルを保全 | 保全commit `215f48237e91e880a4170eb5ef8347db4d25c81d`でクリーン。監査v2/v3の候補は未採用。mainの後続A02・source attributionと照合し、古い変更で上書きしない。 |

外部保全の所在は、この作業ホストの`C:\Users\user\Documents\Codex\2026-10-03\new-chat-2\outputs\repository-consolidation-20261015\`。`vizdoom-dirty-preservation/PRESERVATION.json`、`CLEAN_WORKTREE.json`、`snapshot.bundle`と、`remaining-worktree-preservation/SUMMARY.json`、各作業ツリーの`MANIFEST.json`/`files.zip`/`changes.patch`に復元情報がある。これらはローカル保全であり、この文書だけで他ホストから復元できる公開rawではない。

3件の保全ref・bundle hashは`remaining-worktree-preservation/FINALIZED_SNAPSHOTS.json`と各`SNAPSHOT.json`、controller復旧は`issue59-main-576d/RESTORATION.json`に記録した。作業ツリー自体は削除していない。新しいワーカーの基準にはprimary mainを使い、保全commitを採用実装と取り違えない。

## 同じ実験を持つPRの収束

#8801と#8814は同じhealth-boundary実験のrawを持つが、前者のfinal-admission mutation追試と後者のsource revalidationは独自だった。[統合説明](../../research/doom/v39_currentmain_health_guard_boundary_a01_20261009/CONSOLIDATION_20261015.md)に両方を保持し、元checksum20件（原testを明示的に履歴へ対応付け）、当時のruntime source20件、raw監査13件を照合した。

現行mainに一致するruntime sourceは15/20であり、当時の「current main」を今日の証明として使わない。保存rawの監査テストは他の同名moduleのimportと現在sourceへの誤依存を修正し、誤ったsource hashの拒否も含む6件が通常・最適化Pythonで成功した。元candidate・raw・freeze・監査は再実行/上書きしていない。

## 次の有限な整理

1. ローカル候補のうち未採用の世代確認・scorer・監査差分を後続成果と照合し、独自の残差だけを統合する。保全commitだけで研究完了とはしない。
2. #8701を保管元の保存済みrawで監査し、結果に従って統合または修理する。
3. 未判定Issueを一つの研究テーマずつ読み、仮説・既存結果・依存・次の実験を[整理計画](../REPOSITORY_CONSOLIDATION.md)へ接続する。保存だけで閉じない。
4. 各PR/branchの固有差分と依存を照合し、検証済み統合と重複解消を進める。別作業ツリーのHEADがmainに含まれるだけでは、未保存・無視対象・現在の利用まで消してよい根拠にならない。

全体の整理は未完了。入力解放・task effect・有限回復・効率比較の残差も継続している。新しい必須レビュー人数や、整理が終わるまで全ワーカーを止める条件は追加しない。
