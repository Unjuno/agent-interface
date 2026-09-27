# 祖先取消と子の復帰条件 — 部分実行STOP報告

## 判定

**HOLD_INCOMPLETE_30_CASE_LOCAL_PILOT**。
**STOP_CASE_WORKER_EXIT_WAIT_AND_OUTER_TOOL_TIMEOUT**。
公開事前登録済み正式実験は0件。30件のローカル凍結パイロットは21件の完全ケース記録、
1件の部分記録、8件の未実行で終了した。元の全件判定をPASSに置換しない。

## 起点と並列作業

GitHub MCPの開始・終了mainは40493a9bb77eba00dd9d72207d683f2206ea45a5。
README、CURRENT_GOAL先頭、ROADMAP、直近open/closed Issue/PR、最初の100branchと
関連検索を確認した。全件監査ではなく、未公開作業は不明。
#4307は別フレームへの子成功確認流用を検証し、#4302は完了通知の系譜、#4306は配送順序、
#4309は保存操作結果照会、別engineering branchは以前の形式検証成果の公開を担当する。
これらの割当・ソース・共有runtime・workflow・indexは変更していない。
今回の新しい比較因子は、**葉の復帰前に祖先のどの条件を継承するか**である。

## H / T / D / C / U

- H: 子自身の条件が成立しても親の取消は子の仕事を禁止する。他方、親が子の終了を待つ
  という状態は子の仕事を禁止しない。子の全条件と祖先の活動状態だけを組み合わせる方式が
  この宣言済み契約に適合する。活動状態は生体・processの生存ではなくtask_activeを意味する。
- T: STABLE / ROOT_CANCELED / MID_CANCELED / LEAF_CANCELED / ROOT_EVIDENCE_MISSING、
  3方式、2反復。6バッチ各5件、最大30件。三つの仕事フレームにaをXTEST入力し、最内モーダルを
  閉じた後、葉にbを送るかを一度だけ決める。祖先自体の仕事完了は評価しない。
- D: 全30件・source/bytes/process/cleanup・独立生ログ監査・12改変対照が必要。
  凍結した完全分母を満たさないため、今回の全件判定はHOLD。候補の取消後入力はFAIL条件。
- C: 継承済みの活動フラグを元から提供するruntimeには追加確認が不要かもしれない。
  今回の祖先関係・取消意味・整合した同一appスナップショット・入力までの静止は仮定。
- U: 任意GUI、動的reparent、認証、祖先関係発見、検査後取消、分散取消、クラッシュ復旧、
  モデル・tokens・latency・自然故障率・製品安全性は未検証。校正済み合成不確かさやkは未取得。

## 方法と論理

LOCAL_FRAMEは前回の厳密形式検証済みの葉ゲートだけを使う。
ALL_ANCESTOR_GATESは祖先の活動・scope/sourceを確認した後、祖先自身の全復帰ゲートも要求する。
ANCESTOR_LIVENESSは葉の全条件と、祖先全員の現在の活動・scope/sourceだけを要求する。
三方式とも元バイト列の重複キー・型検証を通す。前回のJSON不正例を再実行した研究ではない。

取消済みの祖先と活動中の子は同時に存在できるので、子だけの確認は契約上不十分である。
逆に親のinterrupt_resolved=falseは子の終了待ちを表す。これまで要求すると正常な子も停止する。
全祖先が活動中で、葉の全条件が成立し、完全で正しい現在の祖先証拠があるなら、
この限定契約の全必要条件は成立する。これは適格性の論証であり、OS入力権限を付与しない。
完全な必要性・十分性・帰納法・反例・変数表・単位チェックはPROOF.mdに保存した。
単一判断での過剰拒否を観測したのであり、無期限の実測デッドロックを主張しない。

## 完全記録21件だけの参考集計

| 指標 | LOCAL_FRAME | ALL_ANCESTOR_GATES | ANCESTOR_LIVENESS |
|---|---:|---:|---:|
| 完全ケース | 7 | 7 | 7 |
| 祖先取消後の子への入力 | 3 | 0 | 0 |
| 祖先証拠欠落のままの入力 | 1 | 0 | 0 |
| 正常時の子完了 | 2/2 | 0/2 | 2/2 |
| 子への後続入力合計 | 6 | 0 | 2 |
| 拒否 | 1 | 7 | 5 |
| 実XTESTタップ総数（準備入力を含む） | 27 | 21 | 23 |

根拠: POSTHOC_PREFIX_AUDIT.jsonと各APP/IPC/POLICY/CASE記録。
21件はc00..c20の固定prefixであり、成功例選別ではない。
各方式のSTABLEとROOT_CANCELEDは2件ずつ、MID_CANCELED、LEAF_CANCELED、
ROOT_EVIDENCE_MISSINGは各1件ずつ。予定された各2反復を全条件で得たわけではない。
全ケース条件別の分母はPREFIX_CELL_COUNTS.jsonに明示した。
子自身が取り消されたケースは三方式とも拒否した。abが取消後にできても成功ではない。
この表は30件の受入判定でも、自然発生確率でも、モデル効果でもない。

## 停止の正確な記録

batch0..3は5件ずつ完了し、4つのbatch終了記録はexit0。
batch4はc20完了後、c21で停止した。
c21にはCANCELED_ANCESTOR応答と、その後のappスナップショットがあるが、
policy workerのwait(timeout=3)でTimeoutExpiredが記録された。
ケースsupervisorはtimeout=true、returncode=-15を記録し、batch-4-STOP.jsonを保存した。
外側のcontainer.exec（設定65000ms）もtimeoutを返し、BATCH4_EXIT.json等は欠けている。
worker停止原因や外側timeoutとの因果順序は断定しない。

c21のCASE.json、app/server/workerの確定終了記録、最終keymapは欠けるため作らない。
生APPログは三つのprefix aと拒否時点の状態を保持するが、欠けた記録を置換しない。
c22..c29は実行しなかった。再実行・差替え・追加バッチ・凍結後source変更はいずれも0。
後の厳密argv照合で当該実験スクリプトの生存プロセスは0だったが、これは過去の終了記録ではない。
最初のps部分文字列照合は自身の外側timeoutコマンドを拾ったため、その誤検出とV2確認を両方残した。

## 監査を混同しない

- 凍結全件監査: **exit1、3369検査、11件の欠測/完全性エラー**。元出力を保存。
- 凍結pilot改変対照: baseline監査失敗でexit1、実施されたpilot変異0件。
- 構築4件: 凍結前最終監査635検査・エラー0、10単体テスト成功、12/12対照拒否。
- posthoc prefix監査: 全30条件のゲートを適用せず、固定21件と停止整合だけを検査。
  **3369検査・エラー0**、判定CONSISTENT_COMPLETE_PREFIX_ONLY、全件HOLDを明記。
- posthoc対照: 同じ12変異定義をprefix監査に適用し12/12実効拒否。全件の元gate達成ではない。
- 固定16ファイルはすべて同一。各完全ケースのアプリ・Xvfb・policy計63のexit0記録と、
  21case launcher exit0を照合した。71タップ・142appキーイベントとneutral最終状態は21件のみ。

posthoc/AUDIT_DELTA.patchが変更点を示す。元のaudit.pyやSCHEDULEやCASEは不変。
別実装・別プロセスのraw監査は同じ作成者によるもので、外部人間のレビューではない。

## 環境・再利用

Linux x86_64、CPython3.13.5、glibc2.41、Tk8.6.16、Python-Xlib0.15、
専用認証付きTCP無効Xvfb、640x480x24。guestはAMD EPYC9V74、許可CPU0..4、
周波数・CPU固定なし。monotonic_nsは診断順序用で、性能benchmarkの値は報告しない。
Docker/OrbStack imageの証明はない。キー状態はXserverの論理状態であり、物理HIDではない。
ホストdesktop、ユーザー文書、モデル/provider、実験network、パッケージ追加は使用していない。

以前のresume_json_ingress_handoff.zipはSHA256
`e13adb499573de545eb9ebb46e38917c343aed82fb8a045b5679445536d6dc7b`。
読み取り専用再監査は元AUDIT/CONTROLSをバイト同一で再現し、新GUI/policy workerは0。
そこからapp.pyとstrict_policy.pyのみバイト同一で再利用。旧STOPやpilot判定は変更しない。

## ロードマップと公開状態

完了: GitHub intake、旧証拠read-only照合、限定契約とH/T/D/C/U、構築、ローカルfreeze、
5回の初回batch呼出し、停止保存、全件監査失敗保存、prefix監査、追加パッチと引継ぎ。
未完了: 30件全体の受入、GitHubへのretrospective公開、PR、実main上CI/review/merge。
このSTOPを改善する目的だけで次の新IssueやGUI割当を増設しない。
必要な工学修正は同じ科学的問いの履歴で扱い、今回のケースを再開・プールしない。

利用可能なGitHub MCPの48操作はread/GETのみ。gh・認証設定・token環境もない。
プラグイン検索で追加の書込み接続は見つからなかった。remote書込み、PR、merge、削除は0。
これは当該接続の観測であり、他agentの書込みを否定するものではない。
公開用Issue/PR草案は草案としてのみ添付し、実在する番号を捏造しない。
差分はresearch/integration/ancestor_cancel_projection_c7e4_v1/**のみ。
実際のmain checkout/CIは行えていないため、ローカルpatch復元検査をCI成功と言わない。
リポジトリ全体のROADMAPは未完了。

## 応用・転用

構造化並行処理: 祖先の取消と子固有の完了条件を分離する。
形式手法: どの述語が親子間で継承されるかを契約に明記する。
GUIワークフロー: 子の正常効果、親の進行許可、根本タスク完了を別々に測る。
いずれも設計上の示唆であって、その分野全体に適用した実験結果ではない。

## ERROR CHECK

source/分母/入力/effect/終了/旧STOP/公開状態を分離した。
全件HOLDのまま、固定21件の記述的結果だけを提示する。欠けた終了は推定しない。

## 次に考える問い

親子間で継承するのは取消だけで十分か、それとも共有された意図・資源制約も必要か。
その境界を誰が明示し、どの現在証拠で検証するべきか。
