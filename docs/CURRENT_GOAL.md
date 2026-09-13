# Current goal — 2026-09-13 revision 3

Latest actual use: [live pending-clock recovery](../research/live_control/PENDING_CLOCK_LIVE.md)
returned history and image in one response; explicit reviewed move/save passed.
Eight frames/40 unique events verified; one read-only recovery exchange. Total
capture-to-evaluation 75.753 s, local reader/persistence 20.182 ms; these are not
paired speed/model-token gains. Next fix comparison conditions before adding
more local mechanisms, and preserve failure/recovery and domain coverage gates.

Latest implementation: [pending-clock reader](../research/live_control/PENDING_CLOCK.md)
adds bounded read-only progress to an already-issued clock. Recorded recovery
reconstructs the intervening history in one read; nine injected controls remain
unresolved. No commands/retries/continuation approval are generated. New live use
and model round-trip/latency benefits remain to be tested.

Latest live integration: [sequence mismatch and history assembly](../research/live_control/LIVE_HISTORY.md)
uses a current cursor with deliberately stale image records. Own clock identity
matches, sequence mismatch stops before input, and real received-history assembly
supports a separate observe-only recovery. Three frames/22 records verified; no
physical input recorded. Scripted readiness, not task/model performance. Next
bound read-only progress through historical clock boundaries without weakening
identity or review requirements.

Latest implementation: [bounded received-history assembly](../research/live_control/RECEIVED_HISTORY.md)
replaces manual concatenation with cursor/overlap checks and complete slice
metadata retention. Seven actual slices restore exactly; ten negative controls
reject invalid or unresolved histories. This remains offline review assistance;
live read-only draining and direct sequence-mismatch validation are outstanding.

Latest recovery evidence: [Inkscape live view](../research/live_control/POINTER_VIEW_RECOVERY.md)
stopped on a stale historical clock boundary before input. A subsequent malformed
save-key program was rejected before admission; explicit correction completed the
legacy move-right task. All 45 unique records and nine frames are audited, with
both failures retained. Direct sequence-mismatch and automatic bounded recovery
remain unqualified; do not weaken identity checks to bypass the observed boundary.

Latest follow-up: [live reversible report use](../research/live_control/POINTER_VIEW_LIVE.md)
completed a new known OpenTTD task with both program views and original images in
their respective single responses, without observed truncation or image-only
recovery. Six frames/37 records and original-view restoration pass the audit.
This is one actual-use integration result, not a paired speed/token qualification.
Next stress the live presentation/reconciliation boundary and another domain.

Latest evidence: [actual combined OpenTTD response](../research/live_control/POINTER_COMBINED.md)
passed the guarded task, but the second full report was truncated at the model
presentation boundary. Recovery read the saved result/image without input retry.
All 37 records and six frames are audited. A reversible offline report view removes
exact duplicate receipts while retaining unique evidence. Next, validate this view
in actual combined result/image use before paired timing/token qualification.
The full 358.071-second capture-to-evaluation interval remains in the record.

This document incorporates the user's research convergence proposal. It is the
current working objective for this task and future handoffs. The app's existing
active goal remains active: the available tool cannot edit its objective text.
Do not mark that goal complete merely to replace its wording.

## 最終目標

Agent Interfaceを、私自身が実際に使い、画面の変化に応じて普通の人間に
近い速度・テンポでライブ操作できるインターフェースへ改善する。
正確性を必須条件とし、同一モデル・課題・環境で、最初の有用なフィードバック、
意味的完了の把握、待ち時間、操作・観測の往復、回復コストを測る。
トークン削減は実際のモデル入力・費用で評価し、バイト削減と区別する。
DOOMは実時間で進む環境への転用とデモの評価対象とし、他のGUIでの正確性を
代替しない。人間並みの性能・製品完成は比較可能な証拠なしに宣言しない。

## Domain coverageを基準にした直近の優先順位

DOOMを最大・最難関benchmarkとして扱わない。重要なfast continuous motor /
reactionのstress benchmarkとして残し、Desktop apps、real-time planning /
multi-object manipulation、dense GUI / long-horizon planning、3D navigation /
manipulationと直交する一領域に位置づける。

Linux/X11のArchitecture Discoveryに集中する。まずMindustry・OpenTTD・Luantiの
小さなfeasibility studyで導入・固定scenario・Xvfb・独立採点・reset・資源負荷・
課題の明確さを比較する。正式採用やcross-domain合格と起動成功を混同しない。
[Domain Coverage Matrix](../research/benchmark_discovery/README.md)に要求能力、
現在のshared runtimeで測れた範囲、未検証の能力を分けて記録する。

設計変更は「どの能力軸の不足を解消するか」で選ぶ。DOOMのスコアだけで選ばない。
候補の追加は評価範囲の改訂として次の比較前に宣言し、過去のfreeze条件を遡って
書き換えない。Windows/macOS対応のためだけに候補を広げる作業はPhase Cまで待つ。
画面提示経路の未解決問題と既存の正確性hard gateは継続して扱う。

2026-09-13進捗: 三候補の初期feasibility比較を記録し、OpenTTDの保存済み小課題で
shared pointer候補による自己操作・独立採点を1回通過した。正式採用・freeze合格には
数えない。直近はテスト用GUI起動失敗の再現性、対象周辺を含む配置採点、fresh caseと
desktop回帰、動く画面での有用な観測・入力継続を検証する。次の領域は初期状態を
固定したMindustry。詳細は[自己操作記録](../research/openttd_task/SELF_USE.md)を参照。

配置採点の追記: 周辺42タイルの道路・所有状態を比較し、旧操作の再生で余分な1タイルを
検出した。終点を画面で確認した修正後の自己操作は追加条件も通過。これはdevelopment
caseの改善であり、未知課題での性能や速度改善の証拠にはしない。

## 現在のフェーズと直近の目標

caller game接続追記: 同じv1 caller/adapterでOpenTTD・Mindustryの期限切れ要求拒否、
実行中Shift hold取消・解放、その後の既知課題のscripted replay採点を通過した。
初回OpenTTD起動引数不足は入力なしの失敗として保持。22画像と134記録を監査済み。
次は実自己操作での画像同時提示、live古い観測/途中期限/混雑条件を確認してから対比較へ。
[接続試験](../research/live_control/POINTER_DOMAINS.md)。

caller統合追記: session_v9を変更せずsocket11で包む候補と、時計問い合わせ＋明示操作を
1回のcaller起動で扱う候補を実装。Inkscape実操作の保存結果・9観測・39記録を監査した。
10応答制御例も確認。次はOpenTTD/Mindustry接続とlive取消・期限・古い観測の検証を行い、
画像同時提示を含めて固定する。速度改善やtoken削減の比較は未実施。
[候補記録](../research/live_control/POINTER_CALLER.md)。

比較優先順位の追記: 同じsession_v9の実操作3領域を時間分解し、最初の撮影から最後の
操作terminalまでの95.7–98.6%がaccepted→terminalの外側にあると確認した。推論時間とは
断定できない。次はbackendを固定したcaller・画像提示経路の共通化と境界検証を先行し、
新しい対比較で往復・回復込みの全体時間を測る。過去の3例を対比較にはしない。
[時間分解と比較方針](../research/evolution/POINTER_TIMELINE.md)。

Mindustry建設自己操作追記: live unit・空の経路から共有pointerで6コンベヤーを建設し、
112タイルのguardと入力終了後の搬送48個を通過した。チタン製の誤選択、Qで建設予定を
消した失敗からの回復を含む。操作完了まで145.184秒で速度目標は未証明。新しい局所機能を
増やす前に、この領域をdesktop/OpenTTDと同じ候補比較へ接続し、判断間隔と回復コストを
残した比較を行う。[建設自己操作](../research/benchmark_discovery/MINDUSTRY_BUILD_SELF_USE.md)。

Mindustry搬送採点追記: engineで作った6状態を実GUIで校正し、正しい6タイルの搬送路は
銅32個を届け、余分な配置付きの搬送路は31個届いても112タイルのguardで不合格となった。
欠落・逆向き・部分建設・空状態の搬送は0。エージェント建設成功ではない。次は
player-readyな空経路から共有pointerで実際に建設し、建設費と搬送の測定区間を分ける。
[採点校正](../research/benchmark_discovery/MINDUSTRY_FLOW.md)。

Mindustry自己操作追記: 共有session_v9から再開・ユニット出現の画面確認・右移動・
一時停止を実行した。保存読込直後はunit=nullで、再開後に生成される。次の課題では
初期状態一致とplayer-readyを別々に確認する。12観測の完全復元と終了後の独立ログを
監査済み。最初の撮影から最後の操作terminalまで71.837秒で、人間並みの速度は証明していない。
[自己操作記録](../research/benchmark_discovery/MINDUSTRY_READINESS.md)。

Mindustry追記: 同一保存ファイルを4回の独立GUI起動で読み込み、75,000タイルの
測定項目・初期銅量・再読込画面の一致を確認した。生成時の画面は着陸演出中で
一致しないため、課題は保存ファイルの再読込から開始する。次はplayer/input readiness、
向きの異なる配置と実際の資源搬送を含む小課題の採点校正。全engine状態や再開後の
決定性は未証明。[記録](../research/benchmark_discovery/MINDUSTRY_RESET.md)。

現在は **Phase A: Architecture Discovery**。新しい局所機能の追加をいったん
優先から外し、既存研究を収束判断できる状態へ整理する。

1. Evolution Ledgerを整備し、主要revisionの根拠・判断・未測定項目を索引化する。
   生の実験記録は移動・改変しない。歴史的な未記録項目はゼロとせず欠測にする。
2. failure taxonomyを固定し、新しい失敗分類、既知分類の再発、回帰を区別する。
   後付け分類には監査済み範囲を付け、観測例と未検証リスクを混ぜない。
3. 最新の各機能が別々の試作品で成立している状態から、同じ候補意味論を複数環境で
   評価できる実験計画へ収束させる。まだ全履歴ファイルを統合・削除しない。
4. 比較前にbaseline・候補・正確性ゲート・主要指標・評価量を固定する。
   同じモデル、課題、環境、出力上限を揃え、順序効果を扱う。
5. failure discovery、regression、architecture churnの収束に加え、合理的な候補と
   実測した組み合わせがPareto frontierを意味のある量だけ改善できなくなったかを
   審査する。cross-domain correctnessをhard gateとし、単独効果の縮小は補助指標にする。
   単発10%はpromotionの強い目安であり、Research Freezeの終了条件にはしない。

直近のコンパクト表示への機能追加より、ledger・分類監査・共通評価計画を先に行う。
重要イベント保持は未解決のcritical-event lossとして候補に残すが、追加実装を
自動的な次の仕事にはしない。

## 実験の採択と目標更新

新案は次のいずれかに明確に結び付く場合に採択する：未解決の失敗分類、
core architectureの不確実性、主要指標の意味ある改善、異なる領域への一般化検証。
該当しなければDEFERする。改善値が大きい指標を結果の後で選ばない。

主要な失敗・回帰・実測・ユーザーの方向修正が次の優先順位や終了条件を変える場合、
この文書、ledger、handoffを更新する。最終目的を狭めたり、達成基準を既存結果に
合わせて緩めたりしない。変更理由と証拠を記録し、通常の方針更新で再承認を求めない。

## フェーズの終了を区別する

- Research Freeze: architecture discoveryの区切り。製品完成ではない。
- Phase B: Runtime Consolidation。意味論・共通評価をまとめ、Protocol Freezeを審査。
- Phase C: Windows/macOS backendとcross-platform validation。
- Phase D: Production stabilization、性能・配布・デモの仕上げ。

Phase A終了だけで最終目標をcompleteにしない。移植開始にはOS非依存の意味論と
X11固有部分の分離、入力権限・期限・解放・フォーカス・観測/イベント・stale action・
入力命令体系・planner/runtime境界の安定を要する。

## Change log

- 2026-09-13 r3: ユーザーのDomain Coverage Matrix提案を採用。DOOM中心の
  次段階から、Linuxでの直交benchmark候補のfeasibilityを直近の優先に変更。
  正式採用・freeze qualificationは未達のまま維持する。

- 2026-09-13 r2: Research Freeze Criteria Revision Proposalを採用。
  単独候補の採用判断と研究終了判断を分離。小さく再現可能な改善を保持し、
  組み合わせ効果・相互作用・複雑性・移植コストを含めて残る改善余地を実測する。
  組み合わせの未測定を収束と扱わない。現在もfreeze未達、最終目標は継続。

- 2026-09-13 r1: ユーザーのConvergence / Freeze Proposalを採用。
  終了条件のない局所改善ループから、収束記録と段階的freezeを伴う研究へ変更。
  現時点ではfreeze未達。新規意味論・観測漏れ・未測定のモデル性能が残る。

See [freeze criteria](../research/evolution/freeze_criteria.md),
[ledger](../research/evolution/evolution.csv), and
[original proposal](../research/evolution/source_proposal.md).

2026-09-13 Issue #4/#5 refinement: optimize the capability a planner can express
through observation, action and feedback, preserving universal GUI fallback.
Observation-bound visual addressing, selectable presentation, deterministic effect
feedback and bounded continuation are isolated research candidates, not a bundled
new requirement or evidence of performance. Evaluate correctness, application
effect, planner boundaries and cost on fresh cases across the Domain Coverage
Matrix. See the latest [handoff](LOCAL_RESEARCH_HANDOFF.md) and
[guided pointer evidence](../research/live_control/GUIDED_POINTER.md).

2026-09-13 Issue #6–#10 refinement: consider reactive local macros, optional
multi-view/composite presentation and ephemeral learned accelerators as isolated
comparison arms. Preserve independent scoring, original authority and plain GUI
fallback. Measure observable planner absence and distinguish planner/tool latency,
architectural latency and Python research overhead. Rust/native probes require
stable contracts and measured relevance; formal methods target narrow invariants.
These refinements do not change cross-domain correctness or freeze requirements.
