# Current goal — 2026-09-13 revision 2

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

## 現在のフェーズと直近の目標

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
