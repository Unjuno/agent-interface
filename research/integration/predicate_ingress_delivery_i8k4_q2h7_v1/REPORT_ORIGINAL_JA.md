# #4236後継の入力境界検証 — i8k4

## 1. 結論

**PASS_LOCAL_TYPED_INGRESS_ENGINEERING**。110種類の固定入力を既存実装と追加アダプタへ各1回送り、220独立workerの結果を保持した。正式なGitHub事前登録実験ではなく、ソースをローカルで固定した工程検証である。

既存の研究用コードでは、不正な現在状態61件のうち49件が値を返し、そのうち45件がTRUE/FALSEの確定値、8件がキャッシュ再利用扱いとなった。`executable`がboolでない結果も3件あった。新アダプタは61件すべてを`INVALID_CURRENT_STATE`として既存のprepare/consume/truthを呼ぶ前に拒否した。

正常12件は既存結果を保持。不正キャッシュ17件は、有効な現在状態からの再計算に変換。不正wire11件と不正request9件も評価前に拒否した。ADAPTERの予期しない例外は0件。

**これはデプロイ済みAgent Interfaceの事故・攻撃・不正操作を測定したものではない。** 対象はmainに保存された#4236研究コードと、新たに明示した入力契約である。旧#4236の`HOLD_AUDIT_GATE_SPEC_ERROR`、旧実験、旧監査は変更せず、再実行もしていない。

## 2. 実際に確認した3つの例

| 固定入力の変更 | 既存コードの観測 | 追加アダプタ |
|---|---|---|
| 保存済みintent_versionは整数1、現在側をJSON trueへ変更 | exact_dependency_hit、reused=true | INVALID_CURRENT_STATE、既存関数呼出0 |
| source_currentに文字列「false」 | value=TRUE、executableも文字列「false」 | INVALID_CURRENT_STATE、既存関数呼出0 |
| artifact.valueにJSON配列 | TypeError: unhashable type: list | 有効な現在状態から再計算、reused=false |

rawに含むcase IDは072-bool_alias_one、052-current_str、073-value_bad_73。
Pythonのbool/int関係とtruth-value testingは既知の言語仕様であり、新発見ではない。観測が示すのは、研究コードを外部入力アダプタとして再利用する前に明示的な型契約が必要だという境界である。

## 3. H/T/D/C/U

| 項目 | 固定内容 |
|---|---|
| H | 正常入力の結果を保持し、不正な現在状態は評価前に拒否、不正キャッシュだけは安全な再計算へ分岐する。 |
| T | 110入力、2実装、220fresh worker。正常12、現在状態不正61、cache不正17、wire不正11、request不正9。ケースごとに実装順を交替。 |
| D | 110/220分母、全worker・runnerの実exit0、独立再構成一致、拒否時の関数呼出0、中立フラグ、14個の有効な改変検出、14固定ファイル不変。 |
| C | 合成の境界入力。より厳しい新契約であり、元研究の正常入力HOLDを再判定しない。既知のPython/JSON仕様に依存する。 |
| U | 1環境・1述語、依存集合完全性と現在状態の信頼性を仮定。認証、GUI、モデル精度、速度/token、本番統合、全JSON空間の保証は未検証。 |

閾値・入力・ソースはローカルfreezeの後に変更していない。再試行、ケース置換、除外、旧行との混合は0。公開事前登録を後付けしたとは主張しない。完全な変数表・条件付き証明・単位チェックはPLAN.mdに収録。

## 4. 全入力群の結果

| 群 | 既存return | 既存exception | アダプタreturn |
|---|---:|---:|---:|
| VALID | 12 | 0 | 12 |
| CURRENT_INVALID | 49 | 12 | 61 |
| ARTIFACT_INVALID | 14 | 3 | 17 |
| WIRE_INVALID | 8 | 3 | 11 |
| REQUEST_INVALID | 2 | 7 | 9 |

既存のexceptionはworkerが観測値として捕捉した。worker exit0と述語評価成功は別である。新アダプタのreturnには81件の明示的なINVALID分類を含むため、110returnを110件のtask成功とは解釈しない。

各入力に対する2実装の結果は同じ固定条件の対照であり、220件の無作為な独立試行や自然故障率ではない。

## 5. 実装と残る前提

アダプタはUTF-8限定、最大65,536 byte、コンテナ深さ32。重複JSONキー、非有限数、数値overflowはwire不正として拒否する。5個の世代値は非負の厳密なint、currentnessは厳密なbool、intentはsubmit/inspectのみ。非負整数の一般的な上限は加えず、JSON整数文字数の解釈器上限は継承する。

正常なprepare/consumeはGit blob一致を確認した既存コードへ渡す。不正artifactのみNoneへ正規化して既存のmiss処理へ渡す。現在状態の不正をキャッシュmissに混同しない。全外側応答はauthority=none、input_dispatched=false、task_success=null。

アダプタは新しい性能最適化ではない。既存consumeはhitでもtruthを評価してoracle/correct診断を作る。この処理も保存しているので、reused=trueをモデル呼出や計算の削減に数えてはならない。

現時点では任意のresource/session識別、入力の認証、隠れた依存関係、現在観測の真正性・時間的一貫性までは保証しない。受理された値だけでOS入力を認可してはならない。

## 6. 実行環境

Linux-6.18.44-x86_64-with-glibc2.41、CPython 3.13.5 (main, Jul 15 2026, 20:25:40) [GCC 14.2.0]。
ゲストCPU記述: Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz。割当CPU [0, 1, 2, 3, 4]、周波数・物理コア専有は固定していない。stdlibのみ、workerはpython -S -B。Docker/OrbStackのimage-attested再現ではない。

今回は速度ベンチマークではない。monotonic_nsはプロセスと処理の順序照合にのみ使用し、アプリ効果時刻や性能比へ変換していない。実験にはモデル、GUI、OS入力、外部ネットワーク通信、ユーザーデータを使用していない。ソース取得用のraw GitHub DNS失敗は別の取得記録として保持した。

## 7. ERROR CHECK

独立構成のraw監査は2661チェック、errors=[]。14/14有効な改変を正常な監査失敗として検出し、no-opと監査例外を合格に数えていない。source freeze14ファイルはすべて不変、220workerとrunnerの実終了コード0、timeout=false。

事前構築:8unit methods、別の6入力/12worker、14mutation controls。これは110入力の評価へ混合していない。

独立とは同一著者の別実装・別プロセスを意味し、外部研究者の査読ではない。型・入力契約の工程検証であり、元研究の正式HOLDをPASSへ直したものでもない。

## 8. GitHub状態とロードマップ

開始時と最終確認のmainは4a1f3957e91b412a64769199f78f2c4b0102d28b。README、CURRENT_GOAL、ROADMAP、最近のopen/closed Issue、open PR、最初の100branchと述語関連13branchを確認した。検索は限定的かつ非原子的で、未push作業の不存在を保証しない。

今回のGitHub新規書込・Issue作成・PR作成・mergeは0。公開されたMCPは読取系48操作で、接続済みGitHubのplugin検索でも別の書込経路は見つからず、ローカルgh/設定済みGitHub token変数もなかった。これはこの実行環境の制限であり、全エージェントの能力不足ではない。

既存の自担当branchはmainに対してahead0、behind191。これをbaseとするopen PR検索は0件だったが、delete-ref操作が公開されていないため削除・force moveを行っていない。他担当のbranchは変更していない。

| 工程 | 到達点 |
|---|---|
| 現状・所有範囲確認、source一致 | 完了 |
| 構築、H/T/D/C/U、local freeze | 完了 |
| 110入力・220worker評価、raw監査、14改変 | 完了 |
| 追加source/raw/reportと引継ぎ | ローカル成果として作成 |
| successor Issue/PR公開、リポジトリCI・review、main統合 | 未実施。未投稿の草稿のみ |
| 不要remote branch削除 | 未実施 |

具体的な統合提案は、この純粋な入力アダプタをレビュー可能な追加パスで公開し、既存研究コードとruntime-defaultを分離したまま適用可否を判断すること。全体ROADMAPは未完了。

## 9. 再監査と一次資料

展開先でREADME.mdのread-only手順を実行する。audit.pyは保存rawを照合し、消費済みworkerを再起動しない。ソースの条件付き証明と変数表はPLAN.md。

- 対象ソース: https://github.com/Unjuno/agent-interface/blob/4a1f3957e91b412a64769199f78f2c4b0102d28b/research/analysis/predicate_cache_persist_4217_v1/experiment.py
- 旧Issue: https://github.com/Unjuno/agent-interface/issues/4236
- JSON: https://docs.python.org/3.13/library/json.html
- bool: https://docs.python.org/3.13/library/stdtypes.html#boolean-type-bool

文書参照は3.13.15表示、実際の検証解釈器は3.13.5であり区別している。

## 10. 応用・次に考える問い

型理論ではboolと世代整数を区別する境界、キャッシュ一貫性では不正cacheと不正current evidenceの分離、実験計画では正常・不正・拒否・例外・実行exitの別々の分母管理に転用できる。

現在観測が不正な場合と、過去キャッシュだけが使えない場合を同じ再計算処理へ流すと、どの信頼前提が失われるか。

## 主要ハッシュ

- FREEZE.json: f93b555f597de5d5b88ed1025aeaf9cf55857b4c0e6d6467e2382490b221ae74
- engineering01/RECORDS.jsonl: c13892ce105c69d60564c4949bf9c532d5831249db07ca99b73abe4dee3e1c03
- exact upstream.py Git blob: 51373e57f9966c7ca8d8518a218d02363867fb81
- local source-freeze Git commit: cbcd1a2b282dbe5f63fa838a59316f2529d5869a（GitHubの公開時刻証明ではない）

## 配布工程の記録

最初の一時的ZIP検証ドライバはsysのimport漏れで停止した。展開までは完了していたが再監査は未開始だった。元ソース・測定rawは不変。PUBLICATION_INCIDENTS.mdに保持し、測定を再実行せず、配布ドライバのみを修正して新しい展開先で検証する。
