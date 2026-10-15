# 入力解放・割込み・証拠・回復の研究整理

2026-10-15。#2/#10/#14/#15/#16/#17の関連部分を、現行実装と残る問いへ結ぶ。
これは役割の異なるアイデアの見取り図であり、重複扱いや一括closureの根拠ではない。
[原Issue本文のスナップショット](sources/safety-control-issues-20261015.json)を保存した。
コメント全文や個別実験のrawは置き換えず、各Issueと元の証拠を参照する。

## 問い・依存・次の検証

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

## Issueを閉じる条件

この6件は今回の整理では閉じない。各原文の独自の問いと評価軸は残っている。
個別の有限な実験が完了した場合は、そのIssueの判定条件・原raw・結果・限界を確認して閉じ、
上位の一般保証へ拡張しない。重複を解消する場合は固有の追試・原案・次の検証を実際の
実行先へ引き継ぐ。保存、古さ、未担当、別の近い用語だけではcloseしない。
