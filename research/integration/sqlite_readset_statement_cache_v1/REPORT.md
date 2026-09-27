# SQL文キャッシュと依存読取記録：実行結果

## 結論

`PASS_SQLITE_READSET_CACHE_BOUNDARY_SCOPED`。
正式60件（10条件×3方針×2反復）、10個の固定batchを各1回実行。
独立実装のraw／SQLite監査はエラー0件。8種類のcase単位改変対照を全件拒否。

ただし、これは比較方針と限定されたadapterの結果である。
**SQLiteの欠陥、authorizerによる認可の破れ、既存production runtimeの不具合、
一般SQLの完全な依存取得を主張しない。** authorizerは全呼出しでSQLITE_OKを返す。

**GitHub公開は未実施。** この接続で公開された48操作は読取り／検索のみ。
ローカルgh・Docker・Podman・設定済みGitHub credential変数もない。
プラグインディレクトリを検索しても別の利用可能なGitHub書込み経路は見つからなかった。
Issue／PR草案・追加パッチ・全証拠を保存するが、remote番号・mergeを捏造しない。

## 1. 出発点とロードマップ

開始main: `2308b8301d69b7089a2e0636486736ed59b61537`。
正式直前／終了時main: `33e86e997d02b769af17a3f03f6035c68927da6e`。
このmain進行は他workerによるもので、本作業はremoteを変更していない。

README、CURRENT_GOAL冒頭100行、ROADMAP、ISSUE_FAILURE_CLASSIFICATION、
直近open／closed Issueとopen PR、139個の返されたbranch名を確認。
対象は#1713の自動read-set取得、閉じた#501の観測read receiptの後継条件。
`authorizer`のIssue検索、`readset`のbranch検索は該当0件。
SQL statement/cacheのPR検索は別問題の#3839/#843のみだった。
網羅的・原子的な調査ではなく、未pushの並列作業は不明である。

実行した範囲：対象選定→構築と失敗保存→ローカルsource/gate freeze→正式60件→
別実装監査／改変対照→成果保存。残る範囲：remote Issue／PR／mainとそのCI・review。
広い#1713、#57、#2789、リポジトリROADMAPは本実験では完了しない。

## 2. H / T / D / C / U

H: コンパイル時のSQLITE_READ callbackを実行ごとの読取記録と誤認すると、
statement cacheの再実行で依存が欠落する。接続・schema・SQLに結び付いた
依存メタデータだけを再利用し、revisionは毎回読み直す方式を検証する。

T: 三つのsingleton tableと一つのviewを持つ新規DBをcaseごとに作成。
reader workerとwriter／observer peerを別processとし、後者は操作ごとに新接続を開く。
観測はmode=ro。prepareはvalueとrevisionを同一read transactionで取得し、
checkとeffects表への保存は一つのBEGIN IMMEDIATE内で行う。
処理順はJSON-line要求応答で固定し、sleepで競合を作らない。

D: 全60行・10outer exits・60worker exits・60peer exits・source／raw整合性を要求。
EVENT_ONLYの欠落10件／古い値の保存2件を再現。
NO_STATEMENT_CACHEは欠落・古い値0、不要拒否は別集計。
METADATA_REUSEは欠落・古い値・不要拒否0、10回のメタデータ再利用と新revisionを要求。
全条件はPLAN／FREEZEに正式前に保存。GitHub事前登録ではない。

C: コンパイル時callbackは一般的な行単位動的依存とは違う。
再コンパイル時の複数access setは過大な依存にもなり得る。
writerのversion更新規律、接続の閉じた寿命、schema cookie非リセット等を仮定。

U: 2反復／セルの決定論的条件だけで、自然な競合確率や母集団性能を推定しない。
速度・token・モデル品質・GUI効果・認証・耐障害性・production採用は未検証。

## 3. 正式結果

| 方針 | 件数 | 依存欠落 | 古い値の保存 | 不要な拒否 | 保存件数 |
|---|---:|---:|---:|---:|---:|
| EVENT_ONLY：callbackだけ、SQL cache128 |20|10|2|0|14|
| NO_STATEMENT_CACHE：SQL cache0 |20|0|0|2|10|
| METADATA_REUSE：SQL cache128＋依存メタデータ |20|0|0|0|12|

保存件数が多いことを成功と解釈してはならない。EVENT_ONLYの14件のうち2件は古い値。
候補の12件はcurrentな保存、8件は対応するrevision変更を拒否したもの。
拒否はtask完成や回復の成功ではない。

READ callback件数はEVENT_ONLY10、NO_STATEMENT_CACHE24、METADATA_REUSE10。
候補はcallback再発生を必要としない10回の依存メタデータ再利用を記録した。
これらはcallback発生数であり、CPU時間・速度改善・token削減ではない。

### 直接観測された反例

cold SELECT aはa.valueのcompile callbackを出す。同じ接続でwarm SELECTを実行すると、
SQL実行traceとvalueは存在してもcallback一覧は空になる。
それを依存なしと扱った比較方針では、その後aが更新されても検査が通り、
古いvalueがeffects表へ保存された。別processの観測と最終DBの読取りで照合した。

### キャッシュ無効化だけでは十分でない

viewをaからbへ変更したNO_STATEMENT_CACHEの記録には、a.valueとb.value双方の
callbackが存在した。実際のSELECT結果はbだが、旧aの更新だけでも拒否した。
正式2件で同じ過剰拒否を保持した。schema変更時の再prepareと整合する観察だが、
内部VMの各prepare自体を直接計測して原因を一意に確定したわけではない。

## 4. 構築・凍結・失敗の経緯

- v0構築：15件をまとめた呼出しが外側40秒で停止。6完了＋次caseの途中。
  EXECUTION／outer exitは欠落のまま保持。後のprocess scanに対応workerはなかった。
- v1構築：resident peerと6件batchへ変更し、cold6件の終了を保持。
- unit試験：最初は8項目中1項目FAIL。trace callbackが古いlist.appendを参照するのに
  list自体を交換していた、今回の計測コードの誤り。正式前に同じlistのclearへ修正。
  元source・失敗logをconstruction-source-v1に保持。修正版8/8項目PASS。
- v2構築：30件完了、raw監査エラー0。ただし当初の「両代替とも不要拒否0」ゲートは
  NO_STATEMENT_CACHEの1件で不支持。元CONSTRUCTION_AUDIT.jsonはFAILのまま保存。
- 正式前の判断：候補方針／シナリオは変えず、NO_STATEMENT_CACHEの不要拒否を
  比較上の観測値として明示した。PLANとauditorをその後freeze。構築結果を見た設計であり、
  blind replicationでも、結果を見ないで作ったゲートでもない。
- 正式：60件／10batch、各batch1回、再実行・置換・構築row混入・凍結後調整0。
  source13件とPython／SQLite binaryを各batch開始時に検査。

FREEZE SHA256: `8c4797657e9d3e5c3cc1fe6e79c62958f793c19cbeef07375891aab8db384bb7`。
AUDIT SHA256: `87b57cedb376a1df9023be342e197b6f92e2694e35e65cd78eb4a7c72a7e9b00`。

## 5. 実装前提と証明

実環境：提供Linux6.18.44 x86_64コンテナ、CPython3.13.5、SQLite3.46.1、
AMD EPYC7763、可視CPU5。SQLite DELETE journal、FULL synchronous。
Docker／OrbStack imageや別engineの再現ではない。CPU周波数未測定・未制御。
monotonic_nsは同一clock内の順序診断用であり、性能ベンチマークではない。
測定誤差の合成u_cやcoverage factor kは定義せず、ゼロと偽らない。

PLAN.mdに全数式記号の意味・単位・定義域・型、DESIGN_PROOF.mdに条件付き証明を保持。
要点は「依存resourceを欠かさず、prepareのvalue/revisionを同一snapshotで結合し、
checkからeffectまでを一つのtransactionにする」こと。
メタデータの再利用は古いvalue/revisionの再利用ではない。
一般SQL、複数行／predicate、UDF、virtual／attached table、外部hidden stateの
最小完全依存を証明したものではない。候補は固定query family外を拒否する。

## 6. ERROR CHECK

監査はpolicy／workerをimportせず、SQL実行trace、callback、RPC原本、prepare receipt、
観測前後のvalue/revision、最終SQLite DB、実process exitを別実装で再構成。
全60行、全10batch、全120worker／peer exitsが整合し、errors／gate failuresは空。
8改変対照は、移設した未変更caseが先にPASSすることを要求したうえで、
編集したcaseのbyte bindingを作り直し、意図したsemantic errorで拒否された。
これはcase単位の改変試験であり、任意の監査soundnessや第三者のreviewではない。

source凍結後の変更0、対応worker残留0をPOSTRUN.jsonで確認。
正式rawを新ディレクトリへ復元して再監査する方法はREADME参照。
re-auditは実験再実行ではない。全リポジトリCI、external review、remote branch削除は未実施。

## 7. 統合判断と学際的転用

統合への制約：absence of compile callbackをabsence of dependencyに変換しない。
未知はUNKNOWNとして扱い、再利用するものを依存の構造に限定し、current revisionと
別の寿命で管理する。これは#1713に返せるadapter設計上の条件であり、本番変更ではない。

- DB並行制御：current snapshotとread-version検査。
- コンパイラ：compile-time情報とexecution-timeイベントの区別。
- 増分計算：依存graphの再利用とvalue-cache invalidationの寿命分離。

次の問い：固定singleton SELECTの外でも、再コンパイルの途中情報を最終的な依存と
混ぜず、未知の構文／sourceを拒否できる範囲をどこまで明示できるか。

## 一次資料

- SQLite compile-time authorizer: https://sqlite.org/c3ref/set_authorizer.html
- Python3.13 statement-cache API: https://docs.python.org/3.13/library/sqlite3.html
- SQLite transaction contract: https://sqlite.org/lang_transaction.html
- Parent: https://github.com/Unjuno/agent-interface/issues/1713
- Preserved closed foundation: https://github.com/Unjuno/agent-interface/issues/501

公式仕様から既知のcompile／execution区別を、新規の限定adapter比較に移した実験である。
新規性・優先権・一般的最適性を主張しない。
