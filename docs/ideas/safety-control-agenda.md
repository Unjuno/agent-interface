# 入力解放・割込み・証拠・回復の研究整理

2026-10-15、2026-10-16更新。#2/#10/#14/#15/#16/#17の関連部分と#8909の独立した診断可能性仮説を、現行実装・保存結果・残る問いへ結ぶ。
これは役割の異なるアイデアの見取り図であり、重複扱いや一括closureの根拠ではない。
[原Issue本文のスナップショット](sources/safety-control-issues-20261015.json)を保存した。
コメント全文や個別実験のrawは置き換えず、各Issueと元の証拠を参照する。

## 問い・依存・次の検証

2026-10-16：[X11 custody候補の保全](../../research/integration/x11_custody_convergence_20261016/README.md)で、
閉じた未統合#7148の391公開ファイルと22省略原本を区別した。
V4の構成PASSの後に、読取制限による条件付きfalse-clearとdevice世代・routingの不足が見つかり、
採用が保留された。修理を再開する際は反例・初回失敗・source crosswalkから始める。
緑の旧テストだけで候補を再採用せず、N02の要約を未取得のnative原rawの代用にしない。
公開バイトの新しい保存専用検証であり、実機実験や過去producerを実行した結果ではない。

| Issue / 仮説 | 既存成果と今回の照合 | 残る問い・次の有限な作業 | 判断へのつながり |
|---|---|---|---|
| [#17 安全経路をdata/planner経路から独立させる](https://github.com/Unjuno/agent-interface/issues/17) | V39のcancel-before-planner-ack修理は#8392で統合済み。今回の公開経路Fake Xではfocus query停止中の保持が残った。 | 単一の入力権限を守って、blocked observationから独立した取消し・期限・cleanupを構成する。遅い返答と不確かなrelease readbackも検証。 | 最優先の修理。呼出し元への早い返答だけで有限解放の達成にしない。 |
| [#2 architecture risk register](https://github.com/Unjuno/agent-interface/issues/2)のprocess/backend境界 | 閉じた#821はowner crash時のcleanup、#823はX server stall時の限界を報告している。今回はそのIssue本文・結果コメントを確認した範囲であり、元rawを再監査してはいない。 | 観測処理停止、owner死亡、backend停止を別の故障として扱い、採用callerのどの境界が隔離されるか示す。その他の保守性・座標・観測・oracle等のリスクは#2に残る。 | watchdogやprocessという名前だけで下位backendのrelease保証を引き継がない。 |
| [#10 実装言語・fault boundary・形式化](https://github.com/Unjuno/agent-interface/issues/10) | latencyをplanner/tool、interface、research overheadに分ける提案。今回の停止はmicro-optimizationでは消えない依存である。 | まず必要な権限・順序・未知状態を固定する。移植時は期限、late reply、release/verification、差分costを同条件で検証する。 | Python/Rustの速度比較と解放可能性を分離。言語移植だけを解決策として採用しない。 |
| [#14 event attentionとinterrupt保持](https://github.com/Unjuno/agent-interface/issues/14) | #8926のCLI compositionは保存・出力選択・flushを区別した。モデル受信やACK後の解決は未検証。 | 安全取消しとplannerへの通知を分離し、critical eventの保持→配信→ACK→解決の実経路を照合する。coalescingで未解決eventを消さない。 | data-plane outageを許す範囲と、attention節約の可否を判断する。通知ACKで入力権限を復活させない。 |
| [#15 observation-action-effectの因果trace](https://github.com/Unjuno/agent-interface/issues/15) | 今回、fake release送信・fake bitmap・検証済み結果の非同時性を実際のrelease処理で区別した。 | observation/authority/program/release/effectのIDと時計を結ぶ。証拠不足をunknownで保ち、recording不能がcleanupを妨げないか検証する。 | ログ欠落と入力保持を同一視せず、独立task effectの判定が可能なtraceへ進める。delegation等の他の仮説は元Issueに残る。 |
| [#16 transactional action groups / compensation](https://github.com/Unjuno/agent-interface/issues/16) | commit/compensationにはinput terminalとsemantic effectの区別が必要。今回のfake neutralだけではtask commitを判断できない。 | 独立効果predicateとforbidden effects、変更provenanceを先に定める。外部writerが介在した場合のrefusalと別途許可されたforward repairを既存実験へ照合する。 | 有限回復を「何でもUndoする」処理にしない。安全に採用できる補償条件を限定する。 |

優先順は、#17のblocked-I/O residual → #15のrelease/effect証拠 → #14の保持と通知
→ 独立task effectを伴う有限回復・#16の補償条件 → #10の同条件移植/費用比較。
#2は横断risk registerとして維持する。この順序は作業割当や他の独立作業の停止条件ではない。

## 今回実行した判別

[公開経路Fake X A01](../../research/live_control/public_guard_blocking_a01_20261015/RESULT.md)
は、実際のpublic dispatch/session/guarded backend/cleanupを通す3条件を通常・最適化
Pythonで実行した。query停止中はCTRLが期限後も保持され、cleanup sync停止中は
fake bitmapが空でも結果は未返却だった。どちらも返答再開後は新しい`a`押下を拒否し、
verified-empty cleanupでexecution_failedとなった。raw-only監査は各26条件を確認し、
4改変を拒否した。

採用判断：既存のlate-press fenceは再利用するが、有限解放の不足は未解決。
観測処理とcleanupの分離を、単一writer・late reply fencing・unknown readbackと組み合わせて
検証する必要がある。guarded bridge全体のvisual binding、実際のcancel、OS入力、ライブ回復、
タスク成功・効率の証拠は追加していない。

## 故障の境界を分ける

[別backendへの受理比較](../../research/doom/map01_cross_backend_custody_20261016/README.md)では、
同じbackendは解放未確認時に拒否するが、同じFake X対象の別backendは新しいintentを受理した。
同じsession・別sessionの両条件で元key38は保持されたままで、probeが受理直後に止めたため
2本目のworker・入力送信はゼロ。通常・最適化PythonでこのFAILを保全した。
責務をreplaceable backendの外で保持するauthority、対象incarnation、late writerの排除と
独立した解放/回復の証拠が必要である。物理解放・別process・ライブ回復の達成にはしない。

[保存済みwake-pipe比較の再確認](../../runtime/results/cancel_wake_rescue_17d0/README.md)
では、元packetの213チェックサム、18個のfirst-outcomeと個別row、元freezeを通常・最適化
Pythonで照合し、各4個の保存データ改変を拒否した。元native実験・collector・auditor CLI・
FD操作は再実行していない。native auditorのPID/monotonic記録が欠ける限界も保持した。

| 故障 | 関連する証拠 | 次の修理で混同しない点 |
|---|---|---|
| 通知pipeが満杯 / EAGAINを捨てる | #7049→#7296→#8764の保存済み18セル。retained Eventを先に公開する比較を限定的に支持 | owner loopが動いている通知経路の比較。blocked platform queryを中断できるとは示さない。 |
| focus/identity等の問い合わせでinput ownerが停止 | 今回の公開経路Fake X A01。保持中のCTRLと結果未返却を区別 | Eventを記録するだけでは、止まっているwriterにcleanupを実行させられない。 |
| input owner processが死亡 | #821の報告したcleanup-only watchdog | 単一の権限とlate writerの排除を保ち、backendが応答する条件を別に確認する。今回は元raw未再監査。 |
| X server/backend自体が停止 | #823の報告した確認遅延 | cleanup要求とbackendが受理・検証した解放を区別。process分離だけで物理解放期限を保証しない。今回は元raw未再監査。 |

したがって、retained cancellation stateは再利用候補だが、それだけで#17全体を閉じない。
現行の[入力解放計画](../INTEGRATION_PLAN.md)は、観測停止から独立したcleanup・単一writer・
late reply fencing・unknown readbackを組み合わせて進める。旧rescue文書の委員人数/投票条件は
歴史へ保存し、現在の運用はユーザーのFINAL v5 8.1に従う。人数条件を新たな停止理由にしない。

## 単一writerと観測分離のFake X spike

[凍結した構成試験](../../research/live_control/fake_x_single_writer_spike_20261015/REPORT.md)
では、実際のbackend key/button/release primitiveを使い、問い合わせをwriterと分けた。
通常・最適化Pythonで各10条件を実行し、保存データだけの監査で各11改変を拒否した。
観測停止中の取消・期限切れ・重複取消では、単一writerのままfake cleanupを返し、遅い
epochの返答から後続入力を復活させなかった。解放送信停止では保持が残り、sync停止では
fake neutralでも返却済み確認がなく、readback失敗はunknownと追跡義務を保った。

この凍結spike自体は採用runtimeやguardianの完成ではない。program loop・epoch・時計・観測proofはprobe
所有で、公開bridge/MCP経路・実X・独立アプリ効果は実行していない。次は採用callerへ
観測request/reply境界を接続し、実際のsource/generation/deadlineを保って同じ故障を通す。
backend自体の停止、有限の物理解放、回復・task effect・効率は別の未達gateとして残す。

後続の[active target-query worker](../../runtime/guarded_x11_v1/TARGET_QUERIES.md)は、
公開Python bridgeと標準guarded MCPへfocus/process問い合わせの分離を明示的optionで接続した。
Fake Xで両問い合わせ停止中の取消・原期限切れ・cleanup、遅い返答の破棄、世代変更拒否を通す。
通信エラーのsticky retirementと、取消済み接続開始後に追加問い合わせを始めない回帰も確認する。
capture・保存・input transport等は同期のままで、spike全体の採用や物理解放の保証とはしない。

## #8909 保護制御下の診断可能性 A01

Open Issue #8909 は、後続の安全応答が異なる故障クラスの観測履歴を、
保護的なローカル制御が同一化してしまうかを問う。Draft
[PR #8910](https://github.com/Unjuno/agent-interface/pull/8910) は、作成した有限モデル
(5 states × 3 policies × 2 ticks、計15 trace)に対する `PASS_METHOD_SCOPED` を記録する。
応答が異なるA/B組は、coverなしでは区別でき、規定したprotective-cover観測規則では
同一化し、真実を返すと仮定したpassive sentinelにより再び区別された。独立のliteral
oracleは15 traceすべてに一致し、モデル上で安全性を破るprefixはなく、5 mutationを拒否した。

これは合成モデルの結果に限る。最初の試行で見つかったout-of-catalogのcover適格性に
関するcandidate/oracle不一致は構築失敗として保持し、科学的証拠に数えない。sentinelの
正確性は仮定であり、Agent Interface runtime、GUI、実測sentinel、診断不能の実環境頻度、
本番安全性は検証していない。Issueはopenのまま。runtime policyの変更根拠にはしない。

## #8917 stratified negative claimのincremental maintenance

Open Issue #8917 は、absenceやcardinalityに依存するclaimを、evidence rowのinsert/deleteや
scope不完備の後も正しく更新できるかを問う。#4431のpositive support/cycle deletion、#8624の
stratified negative-queryに対するcounterfactual responsibility、#2305のより広いlive evidence
maintenanceとは、問いを分けて保つ。

提案中のT0は有限でdeterministicなCPU-only比較であり、`STRATIFIED_DRED`、full rebuild、
positive-only support、global invalidationを独立oracleと比較する。claimはscope・epoch・
completenessへ結び、条件が足りない場合は不在を断言しない。mixed insert/delete、代替positive
support、modal absence、exactly-one、下流claim、unrelated claim、completeness欠落を扱い、
stale negative claim、誤retraction、epoch混同、unknown coercionを監査する。Issue本文はこのT0を
「not yet run」と明記しているため、現時点で結果・性能・GUI動作は主張しない。

## Soft-signal recovery deadline — #8024

Open Issue [#8024](https://github.com/Unjuno/agent-interface/issues/8024) asks whether calibration of recovery times can set a finite persistence deadline for an already-authorized local mode after one declared soft excursion. Hard identity, focus, lease, effect, and release failures remain immediate yield conditions; shifted or insufficiently calibrated episodes must remain uncertified.

The A01 finite authored fixture reports `METHOD_PASS_SCOPED`: nominal held-out coverage was 9/9 and no hard event was delayed. However, a simple fixed timeout retained the same 9/9 recoverable cases as the calibrated rule, so incremental value was not shown. The result and raw evidence are in open Draft [PR #8036](https://github.com/Unjuno/agent-interface/pull/8036), not main. This establishes no real recovery distribution, GUI safety, or production deadline. Keep the issue open; any later transfer needs separate authorization and a fresh preregistered gate.

## Issueを閉じる条件

この一覧のIssueは今回の整理では閉じない。各原文の独自の問いと評価軸は残っている。
個別の有限な実験が完了した場合は、そのIssueの判定条件・原raw・結果・限界を確認して閉じ、
上位の一般保証へ拡張しない。重複を解消する場合は固有の追試・原案・次の検証を実際の
実行先へ引き継ぐ。保存、古さ、未担当、別の近い用語だけではcloseしない。
