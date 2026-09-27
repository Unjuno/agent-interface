# 参照画像の保持先が容量不足になった場合の通知・cursor整合性

## 1. 〈本論〉

**正式18ケースの結果は `PASS_IMAGE_CAPACITY_TRANSACTION_SCOPED`。通知・読取位置を先に確定し画像を後から保存する比較方式は、容量不足後の通常のsaved-cursor再開で欠落画像を回収できませんでした。通知・画像・cursorを同一transactionで保存する方式は、容量不足時に旧cursorを保ち、事前指定した容量回復処理後に全画像を保持しました。**

このPASSは有限のhost保存契約の検証です。SQLiteの新しい性質の発見、現production readerの不具合認定、GUIタスク成功、製品採用ではありません。GitHubへのIssue/PR投稿・main反映は未実施です。

### 1.1 リポジトリ確認と起点

ソース起点は `2308b8301d69b7089a2e0636486736ed59b61537`。README、CURRENT_GOAL、ROADMAP、追加された `docs/ISSUE_FAILURE_CLASSIFICATION.md`、最新open/closed Issue、open PR、branch二頁および関連語をGitHub MCPで確認しました。検索は重点的・有限で、未pushの作業まで網羅していません。

最終読取時のmainは `33e86e997d02b769af17a3f03f6035c68927da6e`。使用したreader/CLI/DeliveryLedgerのGit blobは起点と同一でした。その他のmainファイルの同一性や完全checkoutでのCIは主張しません。参照は `FINAL_MAIN_CHECK.json`。

**#3876は現在closed（2026-09-21T20:10:34Z）です。** 旧成果中のopen記述は歴史的原文として残し、現在の状態と区別します。閉じたこと自体を全体の統合成功と解釈せず、再openもしていません。

閉じた#3876の復元可能な内容・容量契約と、#717のbounded pending要求を再検討しました。前回の24ケースは保存成功後の元画像削除/置換を扱い、保存途中の容量不足は扱っていません。並行する#3931/#3955のprocess-crash、#3941の並行commit、#4029/#4057のPNG cache/size研究は実行していません。今回の科学的変更因子は画像BLOB保存時の実エンジン容量エラーです。

### 1.2 H/T/D/C/U

| 区分 | 固定した内容 |
|---|---|
| H — 仮説 | metadata先行確定では画像保存失敗時にcursorが先へ進む。同一transaction保存なら旧完全prefixを維持し、容量回復後の1回のsaved-cursor再開で画像も保存できる。 |
| T — 最小検証 | 2方式・3容量条件・3反復の18ケース。6ケースずつ3固定バッチ、別processの実CLI/保存worker/読取専用observer。元通知・画像は不変。構築12ケースは除外。 |
| D — 判定 | 18ケース、198process receipt、3バッチ終了、PNG/通知/cursor/実DB/sourceが独立監査と一致し、容量エラー位置と回復結果が事前表に一致する場合のみ限定PASS。完全な反証はFAIL、不完全な証拠はSTOP/HOLD。 |
| C — 対立・限界 | 同時writer、元画像の取得途中変更、電源断、物理ディスクENOSPC、別修復手順では結果が変わり得る。比較方式もエラーは正しく返すので、虚偽の成功返却を発見したとはしない。 |
| U — 不確かさ | 1環境、生成PNG、有限の方向付けた容量条件。自然発生率・速度・token・モデル閲覧・ACK・実GUI・productionは未測定。校正済み合成標準不確かさ/包含係数は算出していない。 |

完全な事前手順、変数表、単位チェック、合否条件は凍結済み `PLAN.md` / `PLAN.json` にあります。事前固定はローカルであり、GitHub上の事前登録ではありません。

### 1.3 実装前提と実験

提供されたLinux 6.18.44 / x86_64 / glibc2.41実行コンテナ、CPython3.13.5、SQLite3.46.1を使用しました。guest CPUはAMD EPYC9V74、周波数と共有host負荷は固定していません。時間はCLOCK_MONOTONICの診断値だけで、性能比較をしていません。Docker/OrbStackのdaemon/image同一性は確認できず、その再現性は主張しません。インストール、実験中のネットワーク要求、GUI・モデル・操作inputはありません。

同一writer・私有SQLite database、DELETE journal、synchronous=FULL、page_size4096B。`max_page_count`でdatabase自体を最大64pageに制限しました。これは262144BのDB上限であり、journal/evidence全体やhost disk占有の上限ではありません。実ディスクを満杯にしていません。[S1]

各caseは3通知と3生成PNG（852B、24713B、49363B）を使います。同じ反復内では方式/容量条件をまたいでPNG bytesを同一にしました。actual DeliveryLedger.prepareと変更していないCLIが通知を扱います。通知1と画像1を保存した状態から、通知2/3を読んで比較します。

`META_THEN_OBJECTS`は通知pageとcursorを先にcommitし、その後、画像を1つずつ別transactionでcommitします。`ATOMIC_PAGE`は通知、元CLI応答、検証済み画像2つ、cursorを1つのtransactionに入れます。前者は意図的な比較方式、後者は研究用host候補で、どちらもproduction runtimeではありません。

容量条件はROOM=64page、FULL_FIRST=初期page_count（観測6）、FULL_SECOND=初期+10（観測16）。FULL_FIRSTは最初の新画像、FULL_SECONDは2つ目の新画像で実SQLite `SQLITE_FULL`（code13）を生じました。例外を偽造したmockではありません。

エラー時のtransaction全体rollbackを無条件には仮定しません。保存実装はtransaction状態を調べ、残っていれば明示rollbackします。SQLite公式文書も、エラーと状況によってstatement/transactionのrollback範囲が異なることを説明しています。[S2]

その後に行うのは、**事前に指定した1回だけの保存回復**です。容量を64pageへ戻し、保存済みcursorからactual CLIで読み直します。source画像を残したままの保存処理で、application actionの再送ではありません。新しい正式allocationや隠れた成功までのretryにも数えません。

### 1.4 正式結果

| 方式 | 正式case | 容量エラー | エラー時に旧cursor維持 | 回復処理終了時に全画像保持 | 最後に画像欠落が残ったcase | 欠落画像総数 |
|---|---:|---:|---:|---:|---:|---:|
| metadata先行 | 9 | 6 | 0/6 | 3/9 | 6 | 9 |
| 同一transaction | 9 | 6 | 6/6 | 9/9 | 0 | 0 |

上表の9/9は容量回復処理後の結果です。容量不足の6caseを初回成功に数えていません。3反復は有限coverageで、母集団の故障率ではありません。根拠は `evidence/FORMAL_AUDIT.json` と各caseの実DB snapshot・CLI応答・PNG bytesです。

| 容量条件（方式ごと各3case） | metadata先行の初回結果 | 同一transactionの初回結果 | 宣言済み回復後 |
|---|---|---|---|
| ROOM | 全通知・全画像を保存 | 全通知・全画像を保存 | 両方式とも完全、未読なし |
| FULL_FIRST | cursorは全3通知の後。画像2/3が欠落 | 通知1/画像1/旧cursorだけを保持 | 同一transactionのみ2通知を再取得し完全保存。先行方式は未読なしで2画像欠落のまま |
| FULL_SECOND | cursorは全3通知の後。画像2は保存、画像3が欠落 | 画像2のstageもrollbackし旧完全prefixだけを保持 | 同一transactionのみ完全保存。先行方式は未読なしで1画像欠落のまま |

**metadata先行方式も容量エラーを返しました。** 問題は成功と偽って返すことではなく、宣言されたsaved-cursor回復では既に読み進めた通知が再取得されないことです。元source bytesは全caseで不変かつ利用可能であり、専用の不足画像repairが不可能だとも、永久的データ消失だとも主張しません。

終了記録は198subprocess中186件が0、容量失敗を報告する12件が予定された2です。3runnerと3supervisorの実終了はすべて0、timeoutなし。全childを0と表現しません。formal再実行・case置換・事後閾値変更は0です。

### 1.5 結論までの理由

最初は保存prefix内の通知1に必要な画像1が同じhost storeに存在します。一括方式で新pageのtransactionが成功すれば、画像2/3とそれを指す通知/cursorが一緒に確定し、全3通知の画像が存在します。エラーでtransactionをrollbackすれば、新しい通知/cursorも公開されず、旧完全prefixだけが残ります。実験の両エラー位置はこの保存状態を実DBから確認しました。

metadata先行方式では最初のcommit時点で新しい通知とcursorが既に確定しています。後続の別transactionのrollbackは、その既確定cursorを戻しません。読み直しは通知3の後から始まるため、新pageは返らず、宣言された回復処理は不足画像を埋めません。

したがってこの試験範囲では、**読取位置を「証拠が完全保存された位置」として扱うなら、参照画像の保存失敗とcursor前進を分離してはいけません。** これは既知のtransaction設計原理をこのhost境界へ当てはめた有限実測で、あらゆるstorage障害を解いた証明ではありません。

### 1.6 監査・構築・前回成果

独立監査は別実装・別processであり、runner/workerをimportしません。各保存状態を実SQLite bytesから確認し、別observer出力、PNG CRC/復号pixel、通知内容、CLI response/cursor、process終了、エラーcode、容量、source digestを再構成しました。同じ作者による監査で、独立した人間のreviewや他machineでのreplicationではありません。

18case/198processが一致し、監査errorsは0。case欠落/重複、bool反復ID、終了記録欠落、偽成功、誤エラーcode、誤容量、部分stage欠落、失敗cursor前進、旧画像欠落の10改変をすべて拒否しました。整合性PASSで比較方式の画像欠落を消していません。

構築r0は6case完了後、画像saltが方式/条件に依存していたため、**正式前に**比較用画像をphase/反復だけで決めるよう修正しました。旧4scriptと全r0dataを `construction_history/01/` に保存し、r1を別6caseとして実行・監査しました。両方とも正式分母へ含めません。tool shellのTERM警告も構築記録に残し、空のchild stderrと混同していません。

前回continuation成果は268file / 1480848Bを復元し、旧正式監査を読取専用で再実行しました。旧auditはbyte-identical。旧formalケース再実行0で、元ZIP/旧失敗/旧publication STOPは未変更です。前回ZIPは今回のhandoffの `predecessor/` に原物のまま含めます。これはGitHubに公開済みという意味ではありません。

### 1.7 ソース・再検証と統合状況

- allocation: `image-capacity-txn-a62f-20260922-01`
- local freeze: 2026-09-21T23:04:45.292985Z（2026-09-22 08:04:45 JST）
- FREEZE SHA256: `13c1cbfa143b579eac8c3fffdca027b6d017f09c049c7179ec77864f9c3f2331`
- local preformal commit: `23b1002db7d9775399220e8681d4eb830e13c7fe`
- AUDIT SHA256: `32b804aac9456ec6ddd15d54d8283644e13c6495b76cbade03eb3918982d9495`

local commitはこの作業専用の小さなrepositoryの履歴です。remote mainのdescendantや公開commitではありません。凍結15項目は正式後も一致しています。

次のコマンドは既存rawの検査だけです。消費済みrun.py/supervise.pyを再実行しないでください。

```sh
cd research/integration/referenced_image_capacity_txn_a62f_v1
sha256sum -c SHA256SUMS
python -I -S -B audit.py . formal 1 2 3 > /tmp/capacity-readonly-audit.json
cmp evidence/FORMAL_AUDIT.json /tmp/capacity-readonly-audit.json
python -I -S -B test_audit.py . formal 1 2 3
```

| ロードマップ工程 | 結果 |
|---|---|
| intake/前回raw再監査/非重複範囲決定 | 重点確認完了、未push範囲は未知 |
| 構築/事前固定/正式18case | 完了、旧構築を保存 |
| 独立raw監査/改変検出 | PASS、10/10拒否 |
| source/raw/report配布/追加patch | この会話の成果物として保存。復元・適用検証は付属PACKAGING_CHECK.json参照 |
| GitHub successor/PR/main統合 | STOP_GITHUB_WRITE_CAPABILITY_UNAVAILABLE、このtool環境のみ |
| real producer/host・保持期限・実GUI/モデル | 未検証、productionへ自動昇格しない |
| global ROADMAP | 未完了 |

このセッションのGitHub MCPは48読取操作のみです。plugin検索でも別の書込み経路は見つからず、containerにもgh/token/credential helperはありません。ユーザーのpush権限や別workerの能力についての主張ではありません。Issue/PR下書きは未投稿、remote branch未作成、main変更0、branch削除0です。局所publication障害からwrapper専用Issueは増やしません。[S3]

追加pathは `research/integration/referenced_image_capacity_txn_a62f_v1/` だけです。全repo suite・完全main checkout・外部reviewの成功は主張しません。branch削除は、所有とmerge済み証拠・依存PR・対応する削除操作が揃ってからに限定します。

## 2. 〈応用・転用例〉

**データベース/復旧設計**では、cursorと参照objectのtransaction境界を決めるための条件になります。**データ来歴管理**では、通知を保存したかと、その解釈に必要な証拠bytesが保持されたかを別々に点検します。**HCI/エージェント設計**では、未読なしを画像提示可能と同義にせず、容量不足を明示した保留として扱う設計へ転用できます。転用効果は未測定です。

### ERROR CHECK

正式18caseと構築12caseを分離。198終了記録は186成功/12予定容量エラー。3バッチの終了は観測済み。凍結15項目と上流3blobが一致。独立監査error0、改変検出10/10。初回保留と回復後成功、sourceの存在とhost保存、local成果とGitHub公開、研究候補とproductionを区別しました。配布物の復元と追加patch検証は別receiptで記録し、正式実験の再実行ではありません。

## 3. 〈次に考える問い〉

**読取cursorを進めてよい保存単位は通知JSONまでか、それとも解釈に必要な画像bytesとその保持保証までを含むのか。**

### 〈50字超要約〉

容量不足時にmetadataとcursorだけを先に確定すると、通常のcursor再開では不足画像が読み直されません。18caseでは同一transaction方式が旧完全prefixを保ち、容量回復後に全画像を保持しました。GitHub公開・main統合と全体ロードマップは未完了です。

## 一次資料と証拠位置

[S1] SQLite PRAGMA max_page_count: https://www.sqlite.org/pragma.html#pragma_max_page_count （2026-09-22参照）。page上限の仕組みの根拠で、今回の実行成否はrawで判定。

[S2] SQLite Transaction / Response To Errors: https://www.sqlite.org/lang_transaction.html （2026-09-22参照）。エラー時のrollback範囲/状態確認の根拠。

[S3] Repository failure classification at exact intake: https://github.com/Unjuno/agent-interface/blob/2308b8301d69b7089a2e0636486736ed59b61537/docs/ISSUE_FAILURE_CLASSIFICATION.md

Repository current status/source: FINAL_MAIN_CHECK.json, SOURCE_BINDINGS.json, INTAKE.md。元Issue #3876/#717は現在closed。個々の新測定値はevidence/formal-r*/RAW.jsonlとそのcaseディレクトリ、集計はevidence/FORMAL_AUDIT.json。全H/T/D/C/Uと単位表はPLAN.md。
