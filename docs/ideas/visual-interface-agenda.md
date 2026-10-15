# 視覚インターフェースの研究実行計画

対象：[#3](https://github.com/Unjuno/agent-interface/issues/3)、[#5](https://github.com/Unjuno/agent-interface/issues/5)、[#8](https://github.com/Unjuno/agent-interface/issues/8)。[元の仮説と制約](visual-interface.md)を維持し、既存成果との照合から実験へ進める。3件を保存しただけで研究対象から外さない。

## 最初に行うこと

1. **既存成果の対応表を埋める。** 下表の実装/資料を入口に、実際の呼出し元、固定ソース、raw、監査、比較条件を確認する。ファイルの存在や単体テストPASSだけでアイデアを検証済みとしない。同じ問いに有効な結果があれば再実験を省き、未検証部分だけを選ぶ。
2. **入力を伴わない表現・意味の検証を行う。** 座標変換、観測ID、元画像の保持、状態省略とイベント保持、完了レベルの区別を、既存コードの実際のcompositionで確かめる。これらはGUI入力やMAP01の資源を待たずに進められる。
3. **モデルを含む比較を実行する。** #3のgrid比較と#8のpacking比較は、同じsource画像・タスク・モデル条件を固定して別々の介入として扱う。まず視覚的な対象指定で評価し、その後、入力解放・観測・独立効果判定の条件が整った経路でGUIタスクを行う。
4. **結果を採否と実装へ戻す。** 有益なら最小の共通経路へ接続し、害やコストが勝れば修正または根拠つきで棄却する。未検証の残りを明示する。

この順序は研究上の暫定優先順位であり、現行担当や共有資源の割当ではない。照合で残差や依存が変われば理由を記録して更新する。全リポジトリの整理完了は着手条件にしない。

## 仮説別の実行項目

以下の「入口」は現行mainで存在を確認した照合先であり、仮説全体の達成証拠ではない。

| アイデア | 既存成果を探す入口 | 次の有限な検証 | 結果が変える判断 |
|---|---|---|---|
| #3 選択可能なgrid | #3原文、`research/live_control/PRESENTATION_CHOICE.md`、`PRESENTATION_EMISSION.md` | 既存grid介入と結果を照合後、freshな細かい/粗い対象でno-grid・always・selectable・coarse-to-fineを比較。正答率、対象誤差、補正回数、時間、実測可能なモデル費用を記録 | gridを追加/修正するか、特定条件だけに限定するか |
| #5 観測に束縛したvisual address | `runtime/USING_CURRENT_INTERFACE.md`、`research/live_control/anchor_evidence_contract_v1.py` | 使われている対象参照を追跡し、別観測・別surface・frame変更・stale参照で誤った入力権限が発生しないか調べる | 既存契約の再利用か、欠けた座標/観測bindingの修理か |
| #5 選べるpresentation | `research/live_control/PRESENTATION_CHOICE.md`、`presentation.py` | 要求→元画像→派生表現→モデルに渡るものの経路を追い、余分なplanner往復と元画像の欠落を測る | 宣言方法や出力経路の改善が必要か |
| #5 決定的anchor | `research/live_control/VISUAL_ANCHOR.md`、`DRAG_ANCHOR_DIAGNOSIS.md` | 残存rawでcursor変位とobject変位を区別できるか確認。未検証のdistractor/喪失条件だけを比較する | anchor方式の採用範囲、曖昧時のyield条件 |
| #5 有限servo | `research/live_control/SERVO_INTERFACE.md`、`SERVO_RECOVERY.md` | 実際のcallerで目標・上限・中断条件を調べ、stall/target喪失/取消しの残差をfault injectionする | servo導入より先に修理すべき解放/停止経路があるか |
| #5 stateとeventの分離 | `research/live_control/presentation.py`、`test_presentation.py`、`EVENT_CURSOR.md` | stateの連続更新中にfocus変化・critical event・terminalが欠落しないか、保持/配信経路を通して確認する | 最新state省略を許す範囲とevent保持の必要修理 |
| #5 completionレベル | `runtime/core_v1/compiled_gui.py`、独立効果監査 | input成功・program terminal・task effectの不一致例を既存rawから一つずつ確認し、callerの結果表示/判定へ追跡する | 完了語彙と効果判定の実装修理、追加oracleの必要性 |
| #5 continuation | `research/live_control/CONTINUATION_ADMISSION.md`、`CHECKPOINT_CONTINUATION.md` | owner/revision変更、expiry、duplicate/late reply、古いtail再開を実際のcompositionで照合する | 既存ticketの再利用か、取消しと経路置換の修理か |
| #5 自己記述schema | `research/live_control/SCHEMA_PREFLIGHT_V1.md`、公開CLI/MCP仕様 | モデルに提示したschemaと実際に受理する操作・値・エラーを照合し、不一致を最小ケースで実行する | 共通schemaの修理で閉じるか、新機構が必要か |
| #8 composite packing | #8原文、`runtime/USING_CURRENT_INTERFACE.md`、既存presentation比較 | 既存比較を照合後、同じsource/ROI情報をseparate/compositeで提示。overviewのみとtask-selected版は情報量の異なる別対照にする。正答率・panel混同・準備時間・モデル費用を測る | packingを採用するか、タスク限定か、追加費用により棄却するか |

## 比較実験の条件

- **H:** gridやpackingが、正確さを保ち対象指定・観測往復・待ち時間・費用の少なくとも指定した一つを改善する。
- **T:** 既存結果で閉じない最小の残差を選び、source画像・タスク・モデル・表示条件・比較順・出力先・実行ID・評価器をfreezeする。介入以外の意味情報をそろえる。
- **D:** 正確さをhard gateにし、採用する改善指標と閾値、sample数、停止条件、欠測/失敗の扱いを実行前に固定する。この計画だけで数値を後付けしない。
- **C:** オフライン対象指定の結果を、GUI操作成功、入力解放、タスク完了や総合効率と同一視しない。モデルtokenが得られない場合は不明とし、画像枚数やbyte数で代用しない。
- **U:** model/provider依存、拡大・panel分割の視認性、source/source-derivedの混同、fixture記憶、比較順の影響を残す。

実験前に関連PR・閉じたIssueも照合し、使用権が必要な実行だけを現行割当に合わせる。比較の不足や担当不明は、独立したオフライン照合まで止める理由にしない。

## 完了条件

各行に現在の実装・証拠・未検証残差・実行結果・採用/修正/棄却判断が記録されること。既存成果で問いが解決していれば、その根拠を確認して再利用する。残差があれば実験または実装修理へ進む。Issueを閉じる場合も、残る独自の問いが実際にどこで実行されるか確認する。

## 初回照合と次の検証

2026-10-15、main `e0d657c7288d4e3f8dd3314b2decbb89c817cb56`の`presentation.py`と`test_presentation.py`を読み、`python3 -m unittest -v test_presentation`と`python3 -O -m unittest -v test_presentation`を通常WSLで実行し、それぞれ4/4成功した。最新画像の結果直前flush、focus変化の転送、unknown/critical eventの転送、失敗terminal時の未配信画像flushを、その実装の単体範囲で確認した。

これは#5のstate/event分離の一部を既存実装から再利用できる根拠である。配信経路全体での欠落防止、独立したtask effect、gridやpackingの効率を示す結果ではない。次はこのprojectionのcaller→保存→モデルへの配信を追跡し、同じeventの保持と可視化をcompositionで確認する。他の行のrawと比較条件の照合も継続する。新しいGUI操作、WSLc allocation、モデル比較はこの初回照合では行っていない。
