# 入力解放・割込み・証拠・回復の研究整理

2026-10-15〜2026-10-19更新。#2/#10/#14/#15/#16/#17の関連部分と#8909の独立した診断可能性仮説を、現行実装・保存結果・残る問いへ結ぶ。
これは役割の異なるアイデアの見取り図であり、重複扱いや一括closureの根拠ではない。
[原Issue本文のスナップショット](sources/safety-control-issues-20261015.json)を保存した。
コメント全文や個別実験のrawは置き換えず、各Issueと元の証拠を参照する。

**2026-10-19 #2 issue triage:** Keep architecture-risk [Issue #2](https://github.com/Unjuno/agent-interface/issues/2) **open / active**. It is a broad risk register, not one experiment that can be closed by the two already-completed process-boundary studies. Its owner-crash risk has a scoped `PASS_OWNER_CRASH_WATCHDOG_SCOPED` in closed [#821](https://github.com/Unjuno/agent-interface/issues/821); the X-server-stall limitation has a separate scoped `PASS_XSERVER_STALL_LIMITATION_SCOPED` in closed [#823](https://github.com/Unjuno/agent-interface/issues/823). I checked #2's current body and result comments on #821/#823, not the original experiment raw. These results narrow only the process/backend fault boundary. The other register items (authority over-conservatism, coordinate frames, task-relevant completion, image provenance, end-to-end latency, local continuation, closed-loop drag, benchmark collateral effects and held-out generality) remain separate risks; do not mark #2 complete or infer a production failsafe. Its existing family row below is the canonical handoff. This semantic review does not add #2 to the historical research-only primary table or change its r15 navigation-coverage count.

**2026-10-19 #17 standard-caller composition update:** merged [PR #9047](https://github.com/Unjuno/agent-interface/pull/9047) exercises `interface_guarded_cancel` with a blocked owner, injected exact-owner retirement and XRes disappearance, a mocked successful fresh-client empty readback, and a late old-connection queued DOWN. The composed caller and terminal result correctly retain release `UNKNOWN`, no task success, and no replay. The five selected regressions pass in normal and optimized Python; see the [retained report](../../research/integration/standard_caller_release_order_composition_20261019/README.md) and its raw logs. This closes the PR's implementation task, not #17's research question: Fake X injects the server receipts and late ordering; it does not establish whether a supported live X server can produce that schedule, physical release, bounded recovery, or an independent application effect. Keep #17 open and UNKNOWN. A private Xvfb discriminator is now preserved below; it does not use WSLc or qualify the standard caller.

**2026-10-19 #17 Fake X post-readback late-request regression:** the new [counterexample packet](../../research/integration/standard_caller_fake_x_relay_20261019/late-down-after-release-counterexample-20261019-r01/README.md) composes the standard owned-process caller with the Fake X relay. It holds an old-owner KeyPress in a synthetic queue, injects disconnect and a separate empty release readback, then delivers the queued press. The public caller and terminal record stay `UNKNOWN`, release remains unconfirmed, replay is denied, and `task_success` remains null (1/1 normal and `-O`). The first assertion attempt exposed equal adjacent `monotonic_ns` values on this Windows host; that failure is retained, and the corrected test uses explicit event indexes. This is modeled order only: it does not observe server ordering, physical key-up, a release deadline, application effect or MAP01. No WSLc allocation was used. Keep #17 open; before a live candidate, #7924's ownership/allocation boundary must be resolved by current evidence, not inferred from this local regression.

**2026-10-19 #17 A02/A03 proxy-gate discriminator:** the [offline framing packet](../../research/integration/offline_proxy_reply_framing_20261019/README.md) reproduces that the frozen A03 broad predicate selects a pre-press process-identity reply when it shares the owner PID. A connection-and-sequence-scoped policy model passes seven normal and optimized tests: it forwards that identity reply and selects only one action-bound input-sync reply after its KeyPress receipt. This is a scoped model result, not evidence that A03 emitted the selected reply or that its server-side blocked predicate was reached. Do not rerun A02/A03 or close #17. Immediate next work is to inspect whether the actual proxy/caller can produce trustworthy connection, sequence, request-role, and action bindings; only then consider a fresh eligible live candidate. Release/task remain `UNKNOWN`.

**2026-10-19 #17 source-call-chain follow-up:** Current bridge/backend source and the A03 `python-xlib==0.33` pin identify the candidate reply: process identity is rechecked through a `TargetQueryWorker` thread that opens a separate X connection in the same owner PID; the input connection then sends XTEST `FakeInput(KeyPress)` and `Display.sync()` awaits `GetPointerControl` (core opcode 106). The A03 client relay does not parse request frames, so its PID-wide reply predicate cannot isolate this response. The [offline model update](../../research/integration/offline_proxy_reply_framing_20261019/README.md) now passes 8/8 in normal and optimized Python, forwarding same-PID identity replies even with a colliding sequence. This strengthens the circular-gate diagnosis at source level but does not identify A03's actual reply sequence or change its retained failure. Next: build a new per-connection candidate proxy with XTEST opcode negotiation and exact GetPointerControl reply targeting; do not rerun A02/A03. The latest #7924 checkpoint remains `STOP / HOLD` with WSLc client ownership unknown, so no live allocation is available. Keep #17 release/task `UNKNOWN`.

**Later integration correction (2026-10-19):** merged PRs [#9136](https://github.com/Unjuno/agent-interface/pull/9136) and [#9153](https://github.com/Unjuno/agent-interface/pull/9153) connect the parser to a test-only relay and standard caller. The [Windows local recheck](../../research/integration/standard_caller_fake_x_relay_20261019/local-windows-recheck-20261019-r01/README.md) and the post-readback late-request test above pass in normal and optimized Python. This supersedes the earlier parser-to-relay *next-step* statement only. It does not restore A03's missing raw reply trace, observe live X ordering, or change #17's UNKNOWN release/task status.

**2026-10-19 private Xvfb XRes disconnect observation (open PR #9057):** The retained [run packet](../../research/integration/xorg_xres_disconnect_order_20261019/README.md) records GitHub Actions run [39156382299](https://github.com/Unjuno/agent-interface/actions/runs/39156382299), server vendor The X.Org Foundation, release number `12101011`, XRes `1.2`, and XTEST `2.2`. After the owner queued a 3,000 ms delayed XTEST KeyPress and was terminated about 151.7 ms later, independent XRes queries at about 1,011.8 ms and 5,012.0 ms both still saw the client; the expected five-second disconnect bound failed. The final cleanup path sent a separate KeyRelease+XSync and read both keys up. Since no disconnect was observed, post-disconnect and post-delay keymap checks are null and the main cleanup status remains `not_attempted`; this run cannot determine whether the delayed request later executed or establish a release fence. Preserve this as an adverse bounded observation, not as evidence for or against all Xorg teardown behavior. Keep #17 open and release `UNKNOWN`; continue in the existing PR/test family without repeating a consumed run or treating this as WSLc.

**2026-10-19 follow-up run [39157339388](https://github.com/Unjuno/agent-interface/actions/runs/39157339388), PR #9057 head `85dfeae0bfcb398f05c4b519ce515a29c4254038`:** the delayed XTEST request was extended to 8,000 ms. XRes still reported the retired owner `still_connected` at ~1 s, ~5 s, and ~9.5 s after kill (about 1 s after the delay horizon). Independent KeyRelease+XSync returned both keys up; both remained up at the delay horizon and `late_input_observed=false`. Because XRes disappearance never occurred, this is not a post-disconnect sample and cannot determine whether the queued request would execute after actual disconnect. The candidate-late-press assertion failed, so preserve it as a negative bounded result, not as confirmation or rejection of a universal teardown claim. Raw/hash and exact limits are in the [run packet](../../research/integration/xorg_xres_disconnect_order_20261019/README.md). Keep #17 open and release `UNKNOWN`; this is GitHub-hosted Xvfb, not WSLc or a physical desktop.

**2026-10-18 caller統合更新:** mainに統合された[#9014](https://github.com/Unjuno/agent-interface/pull/9014)は、Fake Xの接続別queueで独立UPとempty readbackがblocked writerより先に完了し、writer再開後のlate DOWNを防げない反例を保存した。これは合成モデル内での順序反例であり、実X orderingや物理解放を示さない。続く[#9015](https://github.com/Unjuno/agent-interface/pull/9015)は、標準guarded MCP callerをFake X release-syncで止める回帰を通常/-O各19件で通し、callerが`pending`を返してrelease確認・replayをせず、session closeをbusyのまま保ち、barrier解除後に同じcallを返すことを記録した。[#9022](https://github.com/Unjuno/agent-interface/pull/9022)は同じcallerで、選択writerがDOWNをserver処理前にqueueして停止した状態のcancelを追加した。cancel中はpendingとbusy custodyを保ち、barrier解除後に同じwriterがDOWN後のcleanup UPを行い、suffix/replayを拒否する。三つを合わせてもbounded caller response/custodyとFake X内の順序証拠に限られ、実X ordering、物理解放deadline、writer/server永久非応答時のrelease、task effectは未確認。次の有限な統合対象はsingle-authority writer retirement/fencingとlate-send拒否であり、不確かなreleaseはUNKNOWNを維持する。

**2026-10-18 lease-expiry follow-up:** merged [#9027](https://github.com/Unjuno/agent-interface/pull/9027) advances the same standard MCP/Fake X caller. With CTRL-down already queued and the server held past the original lease, the caller remains pending without release confirmation; after the barrier resumes, the queued DOWN arrives late, the next key is refused, and same-writer cleanup UP is verified by Fake X. The first run also found that an explicit new call could reuse the old still-live alias after `execution_failed`, despite `replay_allowed=false`. The caller now requires review after `execution_failed`, and the regression refuses that reuse. The selected module passes 7/7 and four related modules pass 60/60 in normal and optimized Python. Exact logs/source hashes: [retained packet](../../research/integration/press_lease_expiry_queued_server_mcp_20261018/README.md). This remains a finite Fake X result: an already-queued request is not retracted, cleanup waits for resumption, and no native X ordering, physical deadline, task effect, or permanent nonresponse guarantee is established. Continue with single-authority writer retirement/fencing and late-send rejection; keep UNKNOWN on server/backend nonresponse.

**2026-10-18 requested-process-fence reconciliation:** the already-integrated [#7034 retained result](../../research/concurrency/x11_requested_process_fence_17_4d74_20261003/REPORT.md) resolves the finite Xvfb question it asked: keepalive accepted cancellation while the child was paused after a positive F9 check, then the resumed child issued F9 400.197 ms after acceptance despite a neutral checkpoint. The reference killed and reaped that exact child before acceptance; F9 was never issued, and the prearmed cleanup path released F8 with a neutral keymap readback. This is `SCOPED_REQUESTED_PROCESS_FENCE_SUPPORTED` with `HOLD_RUNTIME_PROMOTION`, not a fresh allocation or a public MCP guarantee. The original #7024 public-cleanup-scope attempt ended `STOP / METHOD_FAIL`; its immutable successor [#7041](https://github.com/Unjuno/agent-interface/issues/7041) later demonstrated scoped prearmed cleanup-scope transfer after identity-checked process death, with a disjoint F9 bystander preserved. The [#7041 report](https://github.com/Unjuno/agent-interface/blob/main/research/concurrency/x11_crash_cleanup_scope_a02_17_5ce3_20261003/REPORT.md) explicitly treats this as research instrumentation, not production recovery or a public API. The remaining integration decision is to give the standard caller an owned task-input process, bind accepted cancellation to verified owner death, and transfer a prearmed cleanup-only obligation before task input; then confirm release independently while the backend responds. Preserve `UNKNOWN` when death, server processing, or release cannot be established. Do not rerun either consumed producer.

**2026-10-18 standard-caller/process-owner source crosswalk:** On current main `a25f0d425191d4941b5fed1449be2305023e50be`, the guarded MCP path in [`mcp_guarded.py`](../../runtime/cli_v1/mcp_guarded.py) still constructs `GuardedSessionOwner` around an in-process [`NativeHandleBridge`](../../runtime/guarded_x11_v1/bridge.py); accepted operations enter `run_in_executor` in [`mcp_server.py`](../../runtime/cli_v1/mcp_server.py), and a wait timeout returns `pending` while the same worker retains custody. The owned-process construction instead launches [`input_owner_process_v3`](../../research/live_control/input_owner_process_v3.py) around the transition/input-owner RPC; [`OwnedOwnerAdapter`](../../research/live_control/input_owner_service_adapter.py) is selected by the research/DOOM process-identity backend in [`session_owned_owner_backend.py`](../../research/doom/session_owned_owner_backend.py). `runtime/cli_v1` has no `owner_service` selection or adapter hook. These are compatible custody patterns, not a composed standard-caller implementation: importing the research adapter alone would not move the X11 bridge or define the MCP operations/receipts. The next integration must explicitly adapt the selected guarded-X11 operation surface to one owned process, preserve caller call-ID and abort/no-success semantics, and keep cleanup `UNKNOWN` until separately confirmed. Do not promote or re-run any prior producer on the strength of this source comparison.

## 問い・依存・次の検証

2026-10-16：[X11 custody候補の保全](../../research/integration/x11_custody_convergence_20261016/README.md)で、
閉じた未統合#7148の391公開ファイルと22省略原本を区別した。
V4の構成PASSの後に、読取制限による条件付きfalse-clearとdevice世代・routingの不足が見つかり、
採用が保留された。修理を再開する際は反例・初回失敗・source crosswalkから始める。
緑の旧テストだけで候補を再採用せず、N02の要約を未取得のnative原rawの代用にしない。
公開バイトの新しい保存専用検証であり、実機実験や過去producerを実行した結果ではない。

| Issue / 仮説 | 既存成果と今回の照合 | 残る問い・次の有限な作業 | 判断へのつながり |
|---|---|---|---|
| [#17 安全経路をdata/planner経路から独立させる](https://github.com/Unjuno/agent-interface/issues/17) | V39のcancel-before-planner-ack修理は#8392で統合済み。Fake X A01/#9014は別connection UPとempty readbackによるfalse-clearを反証し、#9015はblocked release-sync時の同一call custody、#9022はserver処理前にDOWNがqueueされた後のcancelと同一writer cleanupを確認した。保存済み[#7034](../../research/concurrency/x11_requested_process_fence_17_4d74_20261003/REPORT.md)はXvfb上でtask-child kill/reap後のrequested fenceを支持する。#7024の初回STOPを保持した[#7041 successor report](https://github.com/Unjuno/agent-interface/blob/main/research/concurrency/x11_crash_cleanup_scope_a02_17_5ce3_20261003/REPORT.md)は、DOWNが既にsyncされた後のidentity-checked deathとprearmed F8 scope transferを支持し、F9 bystanderも保持した。これは研究用catalog instrumentationであり、一般/production recoveryではない。標準MCP owned-process branchはFake Xでblocked syncのprocess retirement後もkeycode 1がdownのまま、release `UNKNOWN`を保持した。さらにmerged [#9047](https://github.com/Unjuno/agent-interface/pull/9047) composes cancellation with injected owner/XRes retirement, mocked fresh-client empty readback, and a late queued DOWN; caller-level state remains UNKNOWN and task success/replay remain false. | #7034/#7041 producerは再実行せず、live X serverがretired clientのqueued requestをどう処理するかを、対応server上で小さく識別する。Fake Xが注入した順序をそのままserver挙動とみなさない。eligibleな未使用allocationがなければUNKNOWNを維持する。callerはaborted/no-completion receiptのまま、独立application-effect readerと有限回復を別に評価する。 | bounded caller responseとFake X orderingは任意の物理解放deadlineではない。#7041はsynced F8単独/fixture scopeに限る。A01/#9047は構成上の偽確定を避けるcaller方針と合成順序反例であり、実X serverがその順序を行う証明ではない。backend/server非応答時はUNKNOWNを保ち、physical deadlineやtask successを推定しない。#17/#59/#57は未完了。 |
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

**2026-10-18 A01：** [release-order counterexample](../../research/live_control/fake_x_release_order_a01_20261018/REPORT.md)
はFake Xの接続別queueで、DOWNが送信前またはserver処理前に止まる二条件を比較した。
別connectionのUPとempty readbackはいずれも先にverifiedを返すが、writer再開後のlate DOWNで
key37が残り、ledgerはemptyになった。same-connection cleanupはblocked syncから返らず、
server-wide stopでもreceiptは返らなかった。通常/-Oとも同じ反例となり、source freeze・raw・
saved-row auditを保存した。結論はモデル内の順序反例で、実X ordering・physical release・
deadline保証ではない。次は単一authorityのwriter retirement/fenceとlate-send拒否を実callerで
結び、backend不応答時は有限成功を偽らずUNKNOWNを保持する必要がある。

**2026-10-19 owned-process integration (local regression, not live qualification):**
The additive [standard MCP integration](../../research/integration/owned_guarded_mcp_process_20261019/README.md)
adds an opt-in spawned owner for the complete guarded-X11 session. Its selected
110-test suite passes in normal and optimized Python. A separate mutation changes
the target process-generation digest after observation/mint; the standard caller
refuses the stale alias with `SCOPE_MISMATCH` and `input_dispatched=false`. In the
blocked Fake X sync regression, cancellation retired the exact owner process,
but keycode 1 remained down; the call stayed failed/aborted, release `UNKNOWN`,
and replay refused. A composed queue regression then showed a fresh cleanup
connection's actual `X11Backend.release_all` can return an empty verified
readback while the retired writer still has a DOWN queued; applying that old
request leaves keycode 1 down. This deterministic fake-transport counterexample
means prearming a cleanup scope is insufficient by itself: first establish a
queue-drained or late-send fence. Preserve UNKNOWN otherwise; this is not a live
X ordering, task effect, physical deadline, or WSLc result.

The spawned owner snapshot now carries the Xlib connection `resource_id_base`
when available; the 110-test normal/`-O` suite adds an XRes `QueryClients`
presence helper with Fake reply/parser and cooperative poll-budget checks. It
does not bound a blocked X request.

**2026-10-19 WSLc A11 — scoped live Xvfb result:** The [retained packet](../../research/integration/xres_blocked_owner_release_a11_20261019/README.md)
passed 8/8 trials against a responsive X.Org Xvfb. Each owner remained blocked
in XSync with 32 reply bytes withheld. After exact owner retirement, a separate
XRes observer saw that client disappear; key-down was still present at that
fence, and a different X connection then sent KeyRelease, after which key-up
was read back immediately and after 50 ms. This confirms the observable
ordering for that Xvfb fixture and shows that process retirement alone did not
release the key. It does not test the standard MCP caller, permanently blocked
X-server I/O, physical desktop, XWayland, or task effect. The X-Resource
protocol's current-client query is specified in the
[protocol](https://www.x.org/releases/current/doc/resourceproto/resproto.txt).
The in-process helper still lacks an externally bounded blocked-query fence;
keep UNKNOWN if that query cannot return or the server is unqualified.

**2026-10-19 evidence correction for cleanup scope:** The original #7024 ended
`STOP / METHOD_FAIL` before crash cells, but its immutable #7041 successor later
completed the frozen 18-cell allocation and saved-only audit. The observed
outcome was `FAIL_EMPTY_SCOPE_AS_OWNER_RELEASE_EVIDENCE` with
`SUPPORTED_PREARMED_OWNER_SCOPE_TRANSFER_SCOPED`: after same-generation process
death, a prearmed F8 cleanup scope released F8 in six reference cells while
preserving the disjoint F9 bystander; empty backend scope falsely returned a
scoped verified receipt with F8 still down in six crash cells. This narrows the
next implementation question from “can scope be reconstructed?” to “can the
standard caller prearm and transfer known cleanup-only obligations safely?”
The result remains research instrumentation, not a public recovery contract.
See the [immutable #7041 report](https://github.com/Unjuno/agent-interface/blob/main/research/concurrency/x11_crash_cleanup_scope_a02_17_5ce3_20261003/REPORT.md)
and merged [PR #7134](https://github.com/Unjuno/agent-interface/pull/7134).

## Issueを閉じる条件

この一覧のIssueは今回の整理では閉じない。各原文の独自の問いと評価軸は残っている。
個別の有限な実験が完了した場合は、そのIssueの判定条件・原raw・結果・限界を確認して閉じ、
上位の一般保証へ拡張しない。重複を解消する場合は固有の追試・原案・次の検証を実際の
実行先へ引き継ぐ。保存、古さ、未担当、別の近い用語だけではcloseしない。

**2026-10-19 observation-only rerun [39157580185](https://github.com/Unjuno/agent-interface/actions/runs/39157580185), PR #9057 head `4ffa711d6bf4a5e60f18109dc779ed753eff4f88`:** the live Xvfb test no longer asserts a hypothesized late press; it records either keymap outcome and passes when the measurement completes. With the same 8,000 ms delay, XRes remained `still_connected` at ~1 s, ~5 s, and ~9.5 s after kill. Both keys were up after independent KeyRelease+XSync and after the delay horizon (`late_input_observed=false`); the dedicated X11 test passed. This is a valid bounded negative observation, but still no post-disconnect state, late request result after actual disconnection, standard caller, or release fence. Exact raw/hash are in the [run packet](../../research/integration/xorg_xres_disconnect_order_20261019/README.md). Preserve #17 open and release `UNKNOWN`; no WSLc allocation was used.

**#17 integration status after PR #9057 (2026-10-19):** The private-Xvfb measurement harness merged at `6d91411cf8b90d514ac0d05a68009e6667113d7e` after all reported PR checks passed. Its latest retained run is the observation-only 8 s horizon sample: XRes remained present and both keys were up. This integrates the experiment method, not an input-release guarantee. Issue #17 remains open / release UNKNOWN; the standard caller, post-disconnect ordering, live application effect and recovery deadline remain unverified.

**2026-10-19 #17 extended Xvfb observation:** merged [PR #9062](https://github.com/Unjuno/agent-interface/pull/9062) extended the post-horizon XRes query to 10 s after the 8 s XTEST delay. In run [39158398302](https://github.com/Unjuno/agent-interface/actions/runs/39158398302), XRes still returned `still_connected` 18,511.3 ms after owner termination; keys `a` and `b` remained up after the extended probe and no XRes disappearance was observed. The [raw and hash](../../research/integration/xorg_xres_disconnect_order_20261019/README.md) are retained. This is a longer bounded private-Xvfb observation, not post-disconnect ordering, standard caller, release proof, physical effect, or a WSLc run. Keep #17 open and release UNKNOWN.
