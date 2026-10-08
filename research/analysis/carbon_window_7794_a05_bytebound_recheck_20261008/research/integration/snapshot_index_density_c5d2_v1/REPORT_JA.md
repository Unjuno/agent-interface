# 固定byte数におけるスナップショット索引の保持割当 — c5d2

## 1. 実施結果と公開状態

正式9ケースを一度だけ実行し、`PASS_INDEX_DENSITY_MEMORY_SCOPED`。入力を全て1 MiBに固定しても、行数128→8192で準備後の追跡対象割当は29,721→2,130,297 byte、中央値比71.67649でした。各条件3反復は同値でしたが、別環境での誤差ゼロを意味しません。

これは入力bytesを除いたPython割当の観測です。ピーク、RSS、プロセス全体のメモリではなく、既存GUI/モデル/本番ランタイムの障害や高速化を示しません。旧b7e1の性能結果は変更していません。

**GitHub新規投稿・PR・main更新は0件。** このセッションのGitHub MCPには読取・検索のみ公開され、create/comment書込操作を確認できませんでした。Plugin Management検索は接続済みGitHubを返しましたが、別の書込経路はなく、コンテナにはgh/Docker/該当GitHub tokenもありません。これはこの環境の公開制約であり、利用者や他workerの権限・能力がないという主張ではありません。GitHub公開事前登録ではなく、ローカル事前凍結です。

## 2. 調査と並行作業の回避

開始mainは2308b8301d69b7089a2e0636486736ed59b61537。README、CURRENT_GOAL、ROADMAP、直近open/closed Issue、open PR、138件のbranch名を2回のページ取得で確認しました。収集中に状態が変わるため、原子的・網羅的な所有権確認ではありません。現行readerのGit blobはea72c166c2cea511ea91031dfbb14563fe4e3245で旧コピーと一致しました。

最初に検討した需要駆動索引の速度比較は、正式実行前の再確認で同一仮説のIssue #4068 / research/snapshot-demand-index-20260922を発見し、`STOP_PARALLEL_DUPLICATE_BEFORE_FORMAL`。9構築テストと3構築workerだけを保持し、予定した87ケースは凍結も実行もしていません。別担当の18性能ケース・30契約組合せをこの作業の成果に数えていません。

その後、旧b7e1報告が「full-drain peakは索引常駐費用ではない」と明記していた未測定点を選びました。#4068の索引作成方式・first-return速度比較は行わず、旧eager候補をそのまま使って入力byte数一定・行密度だけを変更しました。snapshot+density、具体path/branchの再検索で一致はありませんでした。未push作業の不存在までは保証しません。

前回アーカイブは387ファイル復元、386manifest項目照合、11テスト合格。旧raw-only auditは原AUDIT.jsonとbyte単位で一致。旧正式試験の再実行は0です。旧原本、共有runtime、他担当branchは変更していません。

## 3. H / T / D / C / U

| 項目 | 事前に固定した内容 |
|---|---|
| H | 1 MiBの固定入力でも、8192行の準備後保持割当中央値は128行の8倍以上になる。 |
| T | 128/1024/8192行、各3独立worker、入力1048576 byte、返却上限32件。順序を反復ごとに回転。正しいJSONLを空白で固定長化し、モデルや実ユーザーデータは使わない。 |
| D | 9ケース、実終了、全入力/prefix/cursor/neutral metadata/trace sum/sourceが一致し、別実装監査・改変10種類を通す。倍率8未満はHOLD。証拠不足はSTOP/HOLDで、再試行しない。 |
| C | paddingと行数を変える合成対照。Pythonオブジェクト表現・allocator・GC・tracerに依存し、実ワークロード分布を表さない。 |
| U | 3反復の中央値/範囲のみ。RSS、tracer内部記憶、未追跡native割当、総メモリ、CPU/モデル速度は評価しない。校正された合成不確かさu_c・包含係数kは未推定。 |

凍結日時2026-09-21T23:05:25.662574+00:00（日本時間2026-09-22 08:05:25）。FREEZEのSHA-256は`832a4e3bfa1620bfac96c126b58a54886cf100b8f05357e7229cd8ce0afea025`。凍結対象9ファイルは正式後も同一です。新しい2構築テスト（改変10種類を内包）と16行の1構築workerは正式母数から除外しました。

## 4. 測定条件・生データ結果

提供されたLinux6.18.44 x86_64/glibc2.41、CPython3.13.5、OpenSSL3.5.5。ゲストCPU記述AMD EPYC9V74、可用CPU0–4の5個、各workerをguest CPU0に固定。採取クロック約2596.128 MHzで固定ではありません。物理コア専有や80コア利用は主張しません。Docker/OrbStack image identityなし。実験の外部ネットワーク、GUI、入力、モデル、インストールは0。

測定順序は、入力bytes作成・import→GC→tracemalloc.start(1)→旧FrozenSnapshot.prepare→GC→割当snapshot取得→tracemalloc.stop。その後に初回32件を読み、全prefix表と応答を検証しました。**既存入力bytesとqueryはtrace window外**です。全110,271件の割当traceと28,041件のprefix記録を保存しています。これに含まれるのは準備中に割り当てられてsnapshot時点まで残った追跡対象ブロックで、索引以外の微小な追跡対象管理割当も含みます。

| 行数 | 1行byte（LF込み） | 索引entry数 | 保持割当byte：中央値［最小–最大］ | 旧eager sourceに帰属するbyte |
|---:|---:|---:|---:|---:|
| 128 | 8192 | 129 | 29,721 [29,721–29,721] | 29,665 |
| 1024 | 1024 | 1025 | 259,521 [259,521–259,521] | 259,465 |
| 8192 | 128 | 8193 | 2,130,297 [2,130,297–2,130,297] | 2,130,241 |

**推論:** max_bytesによるpayload上限を、そのまま索引を含むメモリ上限として説明してはいけません。max_records=32は返却件数であり、eager準備で作る索引entry数を抑えません。ただし固定byte数には有限の行数上限があるので、「無限・無制限メモリ」とも主張しません。

## 5. 変数表と完全な条件付き導出

| 記号 | 日本語の意味 | SI/情報単位 | 定義 | 定義域・前提 | 型 |
|---|---|---|---|---|---|
| D | 固定入力列 | byte（非SI情報単位） | exact fixture bytes | 不変bytes | byteベクトル |
| S | 入力長 | byte | len(D) | 正式1048576 | 整数スカラー |
| N | 完全行数 | 1 | 終端LF数 |128,1024,8192、行内literal LFなし | 整数スカラー |
| W | 行幅 | byte | S/N |正整数、LF込み | 整数スカラー |
| j | 境界番号 | 1 |0起点の行境界 |0からN | 整数スカラー |
| B_j | 境界offset | byte |jW |0からS | 整数スカラー |
| H_j | prefix hash | なし |SHA256(D[:B_j]) |exact bytesの整合性のみ |256 bitベクトル |
| E | 索引entry数 | 1 |prefixesの要素数 |準備後 | 整数スカラー |
| P | 返却上限 | 1 |max_records |32 | 整数スカラー |
| a_i | trace iの割当サイズ | byte |size field |正整数 | 整数スカラー |
| K | trace件数 |1 |割当snapshotの行数 |有限、環境依存 | 整数スカラー |
| M | 保持追跡割当量 |byte |全a_iの和 |入力・RSSなど除外 | 整数スカラー |
| R | 高密度/低密度比 |1 |8192行と128行のM中央値比 |各3反復、分母正 | 実数スカラー |

初期表はoffset0の1件だけです。正整数WのためB_jは毎行厳密に増加します。j−1行まで処理した時点でentry数j、末尾hashがH_(j−1)、次sequenceがjであると仮定します。次のLFはj行目末尾B_jにあります。実装はまだ取り込んでいないD[B_(j−1):B_j]だけをhashへ追加します。hashlibの逐次updateは連結列のhashと等価なので、新hashはH_jです。新offsetは過去のkeyと異なり削除もないため、表は1件増えj+1件となり、次sequenceもj+1です。j=0の初期条件を含め帰納法が成立し、準備後はE=N+1です。

Pはprepareの引数ではなく、後続readでのみ使われます。したがってP=32に下げてもEは変わりません。正しい固定幅行では、最初の返却は先頭min(P,N)件、cursorはB_min(P,N)、sequenceはmin(P,N)+1、hashはH_min(P,N)です。P<Nならtailはlimitです。全正式行について、別実装がバイト列からこの表と応答を再構成しました。

同じSでもWを変えるとNとEは変わります。実験ではentry数129/1025/8193です。entryには実装依存の記憶が必要ですが、これだけでbyte量や8倍という閾値を証明したことにはなりません。その残りをtracemallocで観測しました。固定Sの下ではLF数NはS以下なのでEもS+1以下であり、無限増大ではありません。

Mは記録された全Kブロックのa_iを加算して求めます。独立監査はworkerの合計だけを信じず、全traceから再計算し、別途eager_snapshot.pyへの帰属分も加算しています。ただしallocator挙動そのものを別計測器で再観測したわけではありません。Rは9個のMから各3値中央値を計算した比です。

**単位検査:** j,N,E,Pは無次元の件数、WはbyteなのでjWはoffsetと同じbyte。Mはbyteの和であり、2つのM中央値の比Rは無次元です。1 MiBは1048576 byteで、SIのMBと区別します。例として8192行ではW=128、E=8193、最初の32件cursorは4096 byte、sequence33です。

## 6. ERROR CHECK

独立raw-only auditorはworker/snapshotをimportせず、入力の固定byte形、全prefix digest、最初の32件、cursor、metadata、trace型/合計、9 workerと親の実終了を再構成しました。全て一致、errors=[]。改変10種類（prefix欠落/変更、traceサイズ変更/欠落/Boolean、誤合計、source hash、payload、authority、currentness）を全て拒否。有限の検査であり、任意の監査改変に対する完全性は主張しません。

正式再試行0、旧正式再実行0、source9/9不変。9個の異なるworker PIDの実wait記録あり。終了後のPID不存在も確認しましたが、成功判定はPID不在から推定せず、実終了コード0を根拠としています。同一著者の別実装/プロセス監査であり、独立した人間の査読や別マシン再現ではありません。

元AUDIT.json SHA256: `edf9d3c3dacccb3f9f15085cf403b4172ab3aa82116fd798299c9b7b4b86c629`。

## 7. 統合用引継ぎと残工程

今回の新規正式成果は、旧eager実装の容量説明・予算設定に関する9ケースだけです。停止した需要駆動索引比較は別添構築証拠であり、採用候補・正式結果として統合しないでください。#4068の成果はその担当者の結果を別途評価します。

新規追加pathはresearch/integration/snapshot_index_density_c5d2_v1/。ソース、元raw、trace、プロセス終了、PLAN/FREEZE、監査、STOP、未投稿の記録案を完全保持します。Gitパッチはこの専用pathへの追加のみ。元mainに適用・CI合格・GitHub公開済みとは扱いません。公開→repository-only再監査→レビュー/CI→PR経由main反映→依存確認後の自分のbranch整理が未完了です。リポジトリ全体のROADMAPも未完了です。

アルゴリズム設計では入力サイズだけでなく索引entry数を容量モデルに入れる。ランタイム/言語設計ではpayload記憶、追加Python割当、プロセスRSSを別指標として表す。計測・インターフェイス設計では返却件数、準備時の記憶、初回応答、モデルが利用できるまでの時間を混同しない、という3分野への転用が考えられます。

**次に考える問い:** 一つの「容量上限」で済ませず、入力byte数・索引entry数・返却件数のどこに独立した予算を置くべきでしょうか。

## 一次資料

Python3.13 tracemalloc: https://docs.python.org/3.13/library/tracemalloc.html
Python3.13 hashlib: https://docs.python.org/3.13/library/hashlib.html
GitHub intake main:2308b8301d69b7089a2e0636486736ed59b61537、Issue #4068、PR #4012、exact reader blob ea72c166c2cea511ea91031dfbb14563fe4e3245。
公式docsは取得時3.13.15表示、実行系は3.13.5です。外部資料の性能値は使用していません。
