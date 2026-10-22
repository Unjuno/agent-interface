# 視覚インターフェースの研究実行計画

2026-10-16：標準guarded MCP callerへ明示的な
[window lifecycle option](../../runtime/guarded_x11_v1/WINDOW_LIFECYCLE.md)を接続した。
[Fake X構成結果](../../research/live_control/window_lifecycle_local_checks_20261016/README.md)で、
process-onlyの旧alias受理と、対象自身への購読によるDestroy拒否・prefix解放を区別した。
続く[#8969](https://github.com/Unjuno/agent-interface/pull/8969)で、選択されたMAP01/V12経路にも
[capture→lease→入力ownerの構成結果](../../research/doom/map01_window_lifecycle_local_checks_20261016/README.md)を残した。
captureと入力は一つのcanonical lifecycle readerを共有する。readerごとの不透明tokenを別reader間で比較しない。
実機の購読・可用性・最終check/use競合、task effect・回復・効率は未検証であり、#5全体は完了しない。

**2026-10-18 current-main recheck:** `runtime.cli_v1.test_mcp_window_lifecycle` passed 14/14 in normal and optimized Python 3.12.3 on Ubuntu WSL, from main `8a899106b19b82afa99aa5c1fa0fe8dca18c2d9b`. Through the standard MCP caller and actual query-worker/lifecycle-reader code with Fake X transport, the tests retain `window_generation` in the call report and refuse an old alias after a modeled `DestroyNotify` without input emission. The full command outputs and source hashes are in the [recheck record](../../research/integration/target_generation_mcp_caller_recheck_20261018/README.md). This is not live X, and the test does not recreate an XID; native event delivery and the real capture-to-press race remain unqualified.

**2026-10-18 capture-time destruction composition:** a new caller regression queues `DestroyNotify` after Fake X capture returns but before the lifecycle reader's post-capture check. The standard MCP observation refuses without publishing a source; mint from the attempted sequence is refused and no input is emitted. The full lifecycle module passes 15/15 in normal and optimized Python 3.12.3. Raw output and source hashes are in the [capture-destroy caller record](../../research/integration/target_generation_capture_destroy_mcp_caller_20261018/README.md). This exercises the existing direct-subscription reader through its public caller but remains Fake X-only; native X event delivery, XID reuse, physical input/release, task effect and efficiency remain unqualified.

**2026-10-18 guarded-generation composition:** merged [PR #9016](https://github.com/Unjuno/agent-interface/pull/9016) records 31 selected standard guarded-MCP tests passing in normal and optimized Python. The retained [report](../../research/integration/guarded_generation_mcp_recheck_20261018/README.md) composes startup-selected process-generation and window-lifecycle evidence through observation, alias minting, pre-input validation, result retrieval and cancellation. Fake X cases refuse stale process-generation and same-XID destroy/reuse aliases, release a held modifier after invalidation, and retire blocked lifecycle workers without restoring the old source's authority. This is caller-construction evidence, not live XRes/PID-namespace trust or native event qualification; generation remains sampled and can change after the final check, while synchronous Xlib I/O can delay release. It does not establish application effect, MAP01 success or recovery quality. Issue #5 remains open. Next target-binding gate is native event delivery and capture-to-press continuity on an eligible real X target; physical release, task effect and recovery remain separate questions.

**2026-10-19 PR #9099 private-Xvfb crosswalk:** merged [PR #9099](https://github.com/Unjuno/agent-interface/pull/9099) preserves six failed first attempts and one scoped pass in the [seven-run report](../../research/integration/standard_caller_xvfb_generation_20261019/README.md). The passing run used the public guarded MCP caller on private X.Org Xvfb; it bound XRes PID plus `/proc` start ticks and process/window generations, delivered a KeyPress/KeyRelease to a synthetic window, independently read property `[1]`, and read the key up. After `DestroyNotify`, the old alias was refused with `input_dispatched=false`, its query worker retired, review was required, and close verified neutral state. The six earlier failures remain separate first outcomes; the seven runs are one fixture/debug sequence, not seven independent samples. This is stronger than the Fake X-only construction in #9016 for the stated Xvfb path, but the synthetic property is not product-app task success, and one pass is not a timing bound, native-desktop result, physical release guarantee, MAP01 outcome or matched efficiency result.

**2026-10-19 Fake X check/use result:** the [r01 packet](../../research/integration/fake_x_window_lifecycle_check_use_20261019/README.md) injects `DestroyNotify` after the final local press check and release-obligation prearm, then forces an independent lifecycle query to drain it before XTEST. Both normal and `-O` runs reproduce one KeyPress after the reader is closed; the next press fails, caller status is `execution_failed`, review is required, replay is denied, `task_success` is null, and prefix release is verified with an empty Fake X keymap. The full caller lifecycle module passed 16/16 in both modes. This is evidence of a check/use race in the constructed schedule, not actual X server ordering or physical release. Keep #5 open. **Next finite decision:** audit whether the existing lifecycle contract can support an ordered/admission fence without serializing on blocked Xlib I/O; any code change needs a separate design and local fault test. No live allocation is implied.

関連する[#4008](https://github.com/Unjuno/agent-interface/issues/4008)の36ケースは、
共有接続のmask置換による通知喪失、unionと別接続の条件付き保持を報告している。
2026-10-16の照合では予定パス`research/integration/x11_subscription_composition_v1/`の
公開packetをmain `2b9df51535c7662d76ac29477bb14e2219eb9865`に確認できず、
完全原本の公開・読み戻しが残る。コメントのPASSだけで統合済み・終了可能とはしない。
原217ファイルの保全先を確認して公開する作業を#4008に残し、消費済み実験は再実行しない。

対象：north-star [#4](https://github.com/Unjuno/agent-interface/issues/4)、grid [#3](https://github.com/Unjuno/agent-interface/issues/3)、address/feedback [#5](https://github.com/Unjuno/agent-interface/issues/5)、multi-view selection [#7](https://github.com/Unjuno/agent-interface/issues/7)、composite packing [#8](https://github.com/Unjuno/agent-interface/issues/8)。[元の仮説と制約](visual-interface.md)を維持し、問いを混ぜず既存成果との照合から進める。#4は広い設計 thesis、他は別々に反証する介入である。保存しただけで研究対象から外さない。

## 別軸：推定観測channelの頑健な優越証明 — #6678 / #8911

[#6678](https://github.com/Unjuno/agent-interface/issues/6678)のBlackwell比較は、既知の有限channel kernelについてgarbling関係を検査する。
Open successor [#8911](https://github.com/Unjuno/agent-interface/issues/8911)は、有限captureから推定したkernelの不確実性を扱う別の方法課題であり、既存の#6678結果を否定・再採点しない。

#8911の提案は、stateごとのraw countとsampling設計を保ち、同時信頼領域内の全kernel対で優越関係が成立するときだけ`ROBUST A≽B`または`ROBUST B≽A`を返す。それ以外は`UNRESOLVED`とし、単なる領域の重なりをincomparableと呼ばない。これは未実施案で、統計保証やGUI routeの順位はまだ得られていない。

提案T0は、既知のgarbling方向、逆方向、境界・近傍、希少出力、label permutation、cluster/dependenceを含む有限multinomial fixtureを、point-kernel判定とset-valued判定で比較する。state oracle、sampling unit、同時信頼手順、許容誤差、solver、independent auditを事前固定する。confidence regionが境界の両側を許す場合は`UNRESOLVED`を維持する。モデル、GUI、ライブcapture、実運用上の優越はこの案の結果に含めない。

## 最初に行うこと

1. **既存成果の対応表を埋める。** 下表の実装/資料を入口に、実際の呼出し元、固定ソース、raw、監査、比較条件を確認する。ファイルの存在や単体テストPASSだけでアイデアを検証済みとしない。同じ問いに有効な結果があれば再実験を省き、未検証部分だけを選ぶ。
2. **入力を伴わない表現・意味の検証を行う。** 座標変換、観測ID、元画像の保持、状態省略とイベント保持、完了レベルの区別を、既存コードの実際のcompositionで確かめる。これらはGUI入力やMAP01の資源を待たずに進められる。
3. **モデルを含む比較を実行する。** #3のgrid、#7のview-set selection、#8のcomposite packingは別々の介入として扱う。同じsource画像・task semantics・model条件を固定し、#7はview-setの相補性、#8は情報を保つencoding変換を識別する。まず視覚的な対象指定で評価し、その後、入力解放・観測・独立効果判定の条件が整った経路でGUIタスクを行う。
4. **結果を採否と実装へ戻す。** 有益なら最小の共通経路へ接続し、害やコストが勝れば修正または根拠つきで棄却する。未検証の残りを明示する。

この順序は研究上の暫定優先順位であり、現行担当や共有資源の割当ではない。照合で残差や依存が変われば理由を記録して更新する。全リポジトリの整理完了は着手条件にしない。

## 仮説別の実行項目

以下の「入口」は現行mainで存在を確認した照合先であり、仮説全体の達成証拠ではない。

**2026-10-19 #3 issue triage:** Keep [Issue #3](https://github.com/Unjuno/agent-interface/issues/3) **open / queued**; this classification does not assign a worker or consume an experiment allocation. Merged [PR #8924](https://github.com/Unjuno/agent-interface/pull/8924) archived the proposal, but the Issue was reopened after the maintainer clarified that ideas should lead to organized research. The linked `PRESENTATION_CHOICE.md` and `PRESENTATION_EMISSION.md` are about JSON result composition and output-stream receipts, not screenshot coordinate grids, so they are not evidence for #3 and are removed from that row below. A focused search of current-main tracked `research/live_control` found no grid-specific implementation or result report. First audit any retained grid comparison and its custody; if none exists, freeze a matched no-grid / always-on / selectable / coarse-to-fine comparison before running it. Do not infer a result from unrelated presentation or serialization work.

| アイデア | 既存成果を探す入口 | 次の有限な検証 | 結果が変える判断 |
|---|---|---|---|
| #3 選択可能なgrid | [#3原文](https://github.com/Unjuno/agent-interface/issues/3)、[`visual-interface.md`](visual-interface.md)とその[source snapshot](visual-interface-sources-20261015.json)。current-main grid-specific experiment/resultは未発見 | まず過去のgrid比較とrawの所在・custodyを確認する。なければfreshな細かい/粗い対象でno-grid・always-on・selectable・coarse-to-fineを比較する条件を固定し、正答率、対象誤差、補正回数、時間、実測可能なモデル費用を記録 | gridを追加/修正するか、特定条件だけに限定するか。先行rawや有効な結果が見つかれば重複実験を避ける |
| #5 観測に束縛したvisual address | `runtime/USING_CURRENT_INTERFACE.md`、`research/live_control/anchor_evidence_contract_v1.py` | 使われている対象参照を追跡し、別観測・別surface・frame変更・stale参照で誤った入力権限が発生しないか調べる | 既存契約の再利用か、欠けた座標/観測bindingの修理か |
| #5 選べるpresentation | `research/live_control/PRESENTATION_CHOICE.md`、`presentation.py` | 要求→元画像→派生表現→モデルに渡るものの経路を追い、余分なplanner往復と元画像の欠落を測る | 宣言方法や出力経路の改善が必要か |
| #5 決定的anchor | `research/live_control/VISUAL_ANCHOR.md`、`DRAG_ANCHOR_DIAGNOSIS.md` | 残存rawでcursor変位とobject変位を区別できるか確認。未検証のdistractor/喪失条件だけを比較する | anchor方式の採用範囲、曖昧時のyield条件 |
| #5 有限servo | `research/live_control/SERVO_INTERFACE.md`、`SERVO_RECOVERY.md` | 実際のcallerで目標・上限・中断条件を調べ、stall/target喪失/取消しの残差をfault injectionする | servo導入より先に修理すべき解放/停止経路があるか |
| #5 stateとeventの分離 | `research/live_control/presentation.py`、`test_presentation.py`、`EVENT_CURSOR.md` | stateの連続更新中にfocus変化・critical event・terminalが欠落しないか、保持/配信経路を通して確認する | 最新state省略を許す範囲とevent保持の必要修理 |
| #5 completionレベル | `runtime/core_v1/compiled_gui.py`、独立効果監査 | input成功・program terminal・task effectの不一致例を既存rawから一つずつ確認し、callerの結果表示/判定へ追跡する | 完了語彙と効果判定の実装修理、追加oracleの必要性 |
| #5 continuation | `research/live_control/CONTINUATION_ADMISSION.md`、`CHECKPOINT_CONTINUATION.md` | owner/revision変更、expiry、duplicate/late reply、古いtail再開を実際のcompositionで照合する | 既存ticketの再利用か、取消しと経路置換の修理か |
| #5 自己記述schema | `research/live_control/SCHEMA_PREFLIGHT_V1.md`、公開CLI/MCP仕様 | モデルに提示したschemaと実際に受理する操作・値・エラーを照合し、不一致を最小ケースで実行する | 共通schemaの修理で閉じるか、新機構が必要か |
| #7 adaptive view-set selection | [#7原文](https://github.com/Unjuno/agent-interface/issues/7)、[#1946 package-integrity result](https://github.com/Unjuno/agent-interface/issues/1946)、[#1968 serialization result](https://github.com/Unjuno/agent-interface/issues/1968)、[#2031 model-facing localization](https://github.com/Unjuno/agent-interface/issues/2031) | raw/auditの再実行はせず、既存rungsと#7の固定budget/set-choice問いをcrosswalkする。#2031のper-arm scoreはschema/scorer mismatchでaccuracyとして使わない。欠けた識別条件だけを新しくpreregisterする | 新しいview-set介入が必要か、どの条件が識別されていないか |
| #8 composite packing | #8原文、`runtime/USING_CURRENT_INTERFACE.md`、既存presentation比較 | 既存比較を照合後、同じsource/ROI情報をseparate/compositeで提示。overviewのみとtask-selected版は情報量の異なる別対照にする。正答率・panel混同・準備時間・モデル費用を測る | packingを採用するか、タスク限定か、追加費用により棄却するか |

## 関連する別仮説：image-space Jacobian adaptation（#7765）

これは#5のbounded-servo admission/recovery契約とは別の制御則の仮説である。画像特徴の誤差と入力変化の局所Jacobianを更新し、固定gainよりgain driftや軸間結合の補正回数を減らせるかを、有限な合成2-D plantで問う。visual servoingの一般採用やGUIでの改善を前提にしない。

- **状態:** Issue [#7765](https://github.com/Unjuno/agent-interface/issues/7765) はOPEN。新しい実験割当はこの整理記録からは作らない。
- **T0:** 機械的gateは240行を再構成したが、online armの比例gain 0.75とfixed armの0.48が不一致で別seed calibrationもなく、`HOLD_METHOD_DESIGN_CONFOUNDED`。40.7%の補正減少はJacobian効果の根拠にしない。[T0 report](../../research/analysis/image_jacobian_adaptation_7765_t0_20261005/REPORT.md)
- **T0b:** calibration A01は監査の605不一致で`STOP_CALIBRATION_AUDIT_FAILED`。A01を再実行せず、別seed A02はgain 0.9をcalibration-onlyで選択した。独立したheld-out監査は240行を誤りなく再構成したが、drift/cross-coupling subsetではfixed 185 corrections、online 191となり`FAIL_NO_GAIN`。[T0b report](../../research/analysis/image_jacobian_adaptation_7765_t0b_20261005/REPORT.md) · [A02 calibration record](../../research/analysis/image_jacobian_adaptation_7765_t0b_cal_a02_20261005/README.md)
- **境界:** 有限の作者作成simulatorとfeature oracleのみ。GUI、遅延/遮蔽、task effect、実actuationや製品便益の結果ではない。T0のHOLD、A01のSTOP、T0bのno-gainを一つのPASS/FAILへまとめない。

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

### 実行結果：state/eventのCLI composition

[A01の実行記録](../../research/live_control/idea5_delivery_boundary_a01_20261015/RESULT.md)では、mainの実際の`interactive_v10.main()`/`interactive_v15.main()`とprojection/ledgerを、アプリ・Executorだけをstubにして実行した。version×full/compact×正常/送信失敗の8条件を通常・最適化Pythonで検証し、rawだけを読む独立監査でも確認した。

明示的critical eventは出力候補に残ったが、同じfocusの一時的な警告観測はcompact表示から省略された。送信前BrokenPipeErrorではstdoutは空でも`delivered.jsonl`は残る。v15のflush記録は成功時だけ作られるため、この既存機構を再利用する。ただしモデル受信、実際の警告検知、GUI入力・task effectは未検証である。

**判断の更新：** state/event projectionとローカルflush記録は新設せず既存成果を使う。次は実際に採用する公開callerの検知→保持→配信→acknowledgement/decisionを追跡し、不足部分だけをcompositionで検証する。#5の全体達成やcompactの一般採用は未成立なのでIssueは継続する。

### 実装修理：公開X11経路で問い合わせ後の期限を再確認する

観測に束縛した操作の公開経路を調べると、`runtime/guarded_x11_v1/bridge.py`はfocusを確認した後、キー変換やpointer問い合わせが元の期限を消費しても、新しい押下へ進めた。`test_deadline.py`に、focus・key mapping・pointerの各返答でclockを期限へ進める3件のテストを追加し、修理前に全件が期待どおり失敗した。

`runtime/backends/x11_v1/backend.py`の押下直前に、guarded adapterが既存の期限を再確認するローカルfenceを追加した。問い合わせを追加せず、期限後の新規キー/ボタン押下を拒否し、解放は許可する。期限関連19件が通常・最適化Pythonで成功した。これは公開経路にあった具体的な残差の修理であり、停止したX11問い合わせの割込み、保持中入力の有限解放、target generationの統合やタスク成功を証明するものではない。

### Process identityを公開Python callerへ接続する

[明示的なprocess-identity mode](../../runtime/guarded_x11_v1/PROCESS_IDENTITY.md)は、XResのclient PIDとLinux process start ticksのdigestをcapture前後・alias解決・新規押下直前へ結ぶ。同じXID/画像でも観測されたprocess変化や欠落は拒否し、押下済みmodifierは既存cleanupへ進む。照合自身が期限を消費した場合も新しい押下を拒否する。既定modeとCLI/MCP設定は変えない。

Fake Xによる実際のhandle/public dispatch/session/backend compositionとprotocol parserの19件を追加し、guarded suite 102件が通常・最適化Pythonで成功した。これは元研究候補のライブ結果を移したものではなく、この公開sourceの構成試験である。trusted local X serverと同じPID namespaceが前提で、その対応自体は実装が認証していない。同一process内のclient/window再利用、読取後の競合、blocked I/Oからの有限解放、ライブ効果・回復・効率は未検証または未解決であり、#5/#17の残差として続ける。

統合前のレビューで、XResのcanonical client baseとwindow XIDの混同を検出した。異なるIDの実際のPython-Xlib replyを使い、修理前の拒否と修理後の成功を確認した。単一resource/PID-mask要求への単一応答だけを受理し、余分なrecord・不正なmask/client IDを拒否する。また配布archiveのmodule一覧への追加漏れを既存archive testが検出し、同梱を修理した。修理後のguarded 102件は通常・最適化で成功し、distribution 21件、backend 78件中64件（実X14件skip）、core 142件が成功した。いずれもライブ実行ではない。

### MCPの標準callerへ明示的選択を接続する

上記のPython optionだけでは標準MCP callerが選択できなかったため、既存のguarded-x11起動設定に`--guarded-process-identity`を追加した。設定は起動時だけ選び、他のsession modeや不正な型は起動時に拒否する。tool引数からは変更できず、identityが読めなくても再接続や従来modeへのfallbackを行わない。`session.process_identity`は選択されたpolicyを表し、資格確認の成功ではない。

新規9テストが通常・最適化Pythonで成功した。実際のMCP server→owner→bridge→handle→public dispatch→session/backendと保存・表示経路を通し、同じXID/画像での旧alias拒否、modifier押下後の変化とprefix解放、保存/配信digest一致、結果再取得時の再入力なし、既定modeと確認不能時の動作を確認した。X I/Oとplatform初期化はFake Xであり、実サーバーのnamespace一致、ライブMCPとモデル受信、有限の物理解放、task effect・回復・効率を示す結果ではない。

統合確認ではCLI/MCP全体377件が通常・最適化Pythonで成功した（各5件skip）。実行はrootから`python -B [-O] -m unittest discover -s runtime/cli_v1 -t . -p 'test*.py'`、Windows/Python 3.13.14、MCP 1.30.0。最初の広範囲実行はpackage指定と隔離依存の不足で失敗したため、元ログを保全し環境を修正した。また既存のfailed-accepted-Future testはmainでも失敗し、未実行workerの解放callbackが返答に遅れて次のcallをbusyにしていた。終了済みhandleだけは返答前にpending admissionを取り消し、実行中/queued workerはtransport取消しだけでは奪わない修理を含む。実行が始まったworkerや遅い呼出しの既存回帰も含めて確認した。
