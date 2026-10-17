# リポジトリ全体の整理計画

2026-10-15。対象は `Unjuno/agent-interface` 全体とGitHub Issue/PR。コンピューターコントロールの研究を再び見通せる状態にする。

**2026-10-17 open-Issue inventory refresh:** a fresh paginated GitHub REST read
returned 1,677 open Issues, compared with 1,678 in r3. The exact metadata and
the three-ID delta are recorded in the [r4 inventory note](maintenance/open-issues-inventory-20261017.md)
and [CSV snapshot](maintenance/open-issues-20261017-r4.csv). This refresh does
not claim all open Issues have been semantically reviewed.

**2026-10-17 open-PR inventory refresh:** the current listing returned 521 open
PRs, compared with 517 in r3. The full head/base metadata is in the
[r4 snapshot](maintenance/open-prs-20261017-r4.csv); the seven-in/three-out
transition is separately recorded in the [delta review](maintenance/open-pr-delta-20261017.md).
The transition review is not a disposition of all 521 open PRs.

**2026-10-16 r3：** 大量ワーカーが独立した有限の仕事を選べる状態まで整理を続ける。
[r3棚卸し](maintenance/inventory-20261016-r3.json)はIssue 1,678件、open PR 517件。
全件の内容を判定した件数ではない。取得後の処理と未統合変更は
[現在の整理状態](maintenance/consolidation-status-20261016.md)から辿る。

**先行更新（履歴）：** [現在の整理状態・実行順・完了条件](maintenance/consolidation-status-20261016.md)を次の作業の入口とする。
r2時点の取得結果はIssue 1,678件、open PR 518件（[r2取得条件](maintenance/inventory-20261016-r2.json)）。
先行する同日棚卸しはIssue 1,678件、open PR 524件。初回PR 538件との差14件は、直接merge 7件とmergeせず終了7件に分けて照合した。
stack内のmergeはmain統合とは限らない。#5の未完了状態とcompleted closureの不整合も訂正した。
後続の6件は保存先を示して旧PRを終了しており、元PRを直接mergeした件数ではない。
以下の初回棚卸しは履歴として保持し、最新状態や全件レビュー済みの根拠にしない。

**2026-10-17 branch cleanup receipt:** the superseded, unprotected
`research/v39-cancel-batch-race-a01-20261009` branch was removed after its
closed PR and current-main successor were checked. GitHub's retained
`refs/pull/8688/head` still points to the exact source tip. See the
[cleanup evidence](maintenance/branch-cleanup-20261017.md) for this and other
superseded cleanup branches. No tag was pushed, avoiding unrelated
push-triggered workflows.

**2026-10-17 additional remote-ref cleanup:** three redundant branch names were
removed after exact-head and retention checks: two main-merged fixes
([PR #8816](https://github.com/Unjuno/agent-interface/pull/8816) and
[#8763](https://github.com/Unjuno/agent-interface/pull/8763)) and the A07
correction branch merged into the retained A03 source branch by
[#8707](https://github.com/Unjuno/agent-interface/pull/8707). Related local
worktrees and the A03 source branch remain. Evidence is in the
[cleanup receipt](maintenance/branch-cleanup-20261017.md).

## 到達点

- アイデアをテーマ・関係・依存・優先順位で整理し、既存の実装と研究結果につなぐ。
- 各アイデアから、次に行う実験/実装と結果による採用・修正・棄却判断へ進めるようにする。
- 現行実装・実験候補・過去の証拠・運用記録の入口を区別する。
- 重複した案内・旧計画を収束させ、次に必要な文書を一か所から見つけられるようにする。
- 完了、未検証、棄却、停止、保留を混同しない。

## 「クリーン」の完了条件と実行順（r3）

作業ツリーに差分がないだけでは全体完了にしない。次を別々に確認する。

| 対象 | 完了を確認する条件 | 次に行うバッチ |
|---|---|---|
| 入口とオーケストレーション | README→現行ゴール→work mapから、対象範囲・既存Issue・現行成果・未達・次の有限な仕事へ辿れる。古い割当や必須レビュー人数を新しい開始条件にしない。 | 統合済み#8998/#8999をmapに反映。計画中・ローカル検証済み・main統合済みを明示。 |
| 研究アイデアとIssue | 各テーマの独自仮説、反例、出典、依存、既存成果、最小検証、実行先が結ばれる。保存しただけの未達は未達と分かる。 | 視覚・安全制御の既存agendaを維持し、次はモデル連携・比較評価の一族を本文/コメントから整理。全件を一つの親Issueへコピーしない。 |
| PR | 全open PRに、採用候補・修理・証拠保全・後継へ移管・根拠付き棄却の処置がある。統合/終了の正確なheadと継続先を辿れる。 | #8874/#8867はr4/r5の記録どおり終了済み。PR #9005/#9012の重複は現行headで再照合済み。次は残るopen PRから独立成果の優先batchを選び、差分・証拠・後継を分類する。 |
| branch/worktree | 固有変更・raw・未追跡/無視対象・依存PR・使用者を確認し、残すものには理由と所在、消すものには保全先と一致したtipの記録がある。 | まず自分の統合済みrefのみ回収。他者/所有不明の領域は削除せず、照合対象として残す。 |
| 実装・検証 | 採用するコードが現行mainに接続され、必要なローカル検証と限界が残る。旧sourceのPASSを移植しない。 | 未統合のV15選択変更は専用branchに保全。証拠パケットの読戻し後に独立した統合として扱う。 |

順序は **入口の矛盾修理→一族の読解とアイデア整理→固有差分/証拠の保全→ローカル確認→統合→後継付き終了→不要ref回収**。
一族ごとに区切って繰り返し、最後に一覧との差分を照合する。全件整理を研究開始条件にしない。
新しいワーカーは[work map](WORKER_WORK_MAP.md)から一つの範囲を選び、既存の記録先に
対象・branch・出力先・次の成果を短く残す。共有indexの編集と同じコード範囲だけを調整する。
この計画は新しいscheduler、投票、全員待ち、実行資源の割当を作らない。

各バッチの成果は「何件閉じたか」だけでなく、整理した仮説、mainで再利用できる成果、
未解決点と実行先、証拠の不足、回収した自分のrefで確認する。

**方針訂正：** PR #8924でアイデア保管を理由に#3/#5/#8を閉じたが、ユーザーの目的はアイデアを整理して研究を行うことである。3件は再オープンした。未着手・古い・未担当・文書化済みという理由だけで実行対象から外さない。整理の成果は研究判断と実行への接続であり、close件数ではない。

## 現状の棚卸し

取得時のopen Issueは **1,678件**、open PRは **538件**。Issueのうち355件はタイトルが`[Research]`で始まり、1,676件にはGitHub assigneeがない。ただし、assignee空欄は未担当の証明にはならない。

全件の番号・タイトル・URL・更新時刻・ラベル・assignee・open PRのclosing参照を[Issue棚卸し](maintenance/open-issues-20261015.csv)に保存した。関連PR欄はGitHubのclosing参照だけであり、本文・branch・コメントでの関連や実行担当を網羅しない。棚卸しは取得時のスナップショットで、現在の実行権やclosureの可否を自動判定するものではない。

既存の`docs/ideas/README.md`には保存形式があるが、集約されたエントリはゼロだった。最初の移行は[視覚表現・アドレス・フィードバックのアイデア](ideas/visual-interface.md)。#3/#5/#8の原文も保存し、未検証の着想として残す。

## 1. Issueを整理する

次の4種類へ、人が根拠を確認して振り分ける。タイトルや古さだけで閉じない。

| 種類 | 保存先・扱い | closeの理由 |
|---|---|---|
| 今進める作業 | Issueを残し、目的・最小の次の実験/変更・合否条件・担当がいる場合はその所在を書く | 未完了なので残す |
| 次に検証するアイデア | `docs/ideas/`へ仮説・既存証拠・残差・依存・最小実験・判定条件を整理し、実行するIssueと結ぶ | 保存しただけでは閉じない |
| 完了した作業 | 結果・実装・検証・限界をリンク | `completed`。仮説や上位目標の達成とは分ける |
| 重複・後継へ移行 | 集約先に元の独自の仮説・検証項目・次の作業を引き継ぐ | 実行先を確認してから閉じる。単なる文書リンクでは不十分 |

各バッチで、本文、コメント、関連するopen/closed PR、現在の実装・証拠を対象に応じて確認する。進行中の実験、未解放資源、未保存raw、担当中の修理があるIssueは、その状態を引き継ぐまで残す。包括的な親課題に子Issueを丸ごとコピーせず、リンクと短い不足点を置く。

closeコメントには **理由、保存先、科学的状態、残る問い、その実行先** を書く。単なるアイデア保管を`completed`にしない。棄却する場合も、不要/不適切と判断できる根拠を残す。後継課題は実在する不足を扱う場合だけ作り、整理のためだけにIssueを増やさない。既存の議論・raw・失敗記録は消さない。

最初のバッチは#3/#5/#8。[実行計画](ideas/visual-interface-agenda.md)に沿って既存成果との照合、残差の検証、比較実験へ進める。それ以外の1,675件は未判定であり、この棚卸しだけでは閉じない。

次のバッチでは[#2/#10/#14/#15/#16/#17の安全制御・証拠・回復](ideas/safety-control-agenda.md)の関連部分を整理し、公開経路のblocked-I/O残差をFake Xで実行確認した。各Issue全体の達成や、残り全件の判定を済ませたという意味ではない。

## 2. 研究の見取り図を作る

既存の`IDEAS_AND_OUTCOMES.md`、`RESEARCH_MAP.md`、`RESEARCH_ISSUE_INDEX.md`、`RESEARCH.md`を入口として、次のテーマに研究項目をまとめる。

1. 観測・視覚表現・対象指定
2. 入力権限・期限・解放・対象世代
3. 環境応答・タスク効果・有限回復
4. モデル連携・待ち時間・トークン・資源比較
5. アプリ/ゲーム別の移植・検証
6. 実行基盤・配布・プラットフォーム
7. 実験方法・証拠・統計

テーマの一覧は一つに集約し、各テーマに「解決したい操作上の問題」「アイデア」「既存の実装/証拠」「残る問い」「優先順位と理由」「依存」「次に行う最小実験」「結果が変える判断」「実行するIssue」を置く。似た専門用語というだけで仮説を同一視しない。未確認は未確認として照合作業へ結び、放置や棄却と扱わない。

優先順位は、コンピューターコントロールの不足を減らす効果、既存成果の再利用、最小の検証で得られる判別力、依存と実行可能性で決める。全体が整理されるまで、着手可能な実験・実装を止めない。各バッチは少なくとも一つのアイデアを具体的な検証へ進め、結果をテーマの見取り図に戻す。

## 3. 文書とディレクトリを整理する

| 用途 | 入口 | 整理方針 |
|---|---|---|
| プロジェクトの説明 | `README.md` | 目的、利用可能なもの、最短の案内だけを置く |
| 直近の優先順位 | `docs/CURRENT_GOAL.md` | 長い履歴を分離し、少数の次の作業と未完了条件へ縮める |
| 採用実装 | `runtime/`、`src/`、architecture文書 | 実際の呼出し経路と対応プラットフォームを確認して案内する |
| 実験・候補実装 | `research/`、`experiments/`、`construction/` | current/候補/歴史を明示。移動前に参照とsource hash依存を調べる |
| アイデアと実行計画 | `docs/ideas/` | 仮説・出典・既存成果・依存・次の検証・判定条件をテーマ別に整理 |
| 証拠 | `RESEARCH.md`と各実験のraw/audit | 原本を維持。移動や削除はcustody・再現性を確認した後に限定 |
| 運用・保全 | `docs/maintenance/`と既存窓口 | 時点つき棚卸し。現在の禁止や担当と混同しない |

入口の重複を先に直し、巨大なファイル移動を最初に行わない。凍結ソース、manifest、相対リンク、公開URL、テストの参照を壊す変更は別の実装作業として扱う。

## 4. PRとbranchを収束させる

538件のopen PRも、実装待ち、レビュー/統合待ち、後継に吸収済み、証拠保全のみ、放棄済みへ分ける。merge済みの同等変更と検証済み証拠がある場合、重複PRは保存先を示して閉じる。未統合コミットと未追跡ファイルを保全する前にbranch/worktreeを削除しない。

マージ判定には実際の権限・保護条件と変更に必要なローカル検証を使う。この整理計画から新たな必須レビュアー人数や合議条件を追加しない。Issueを閉じることとPRをmergeすることは別に判断する。

## 実行順と完了確認

- [x] 全open Issue/PRの初回取得。Issueは1,678件、PRは538件。
- [x] 既存のアイデア保存先を確認。#3/#5/#8を原文つきで集約。
- [x] 集約文書をmainへ届けた。先行した#3/#5/#8のclosureは訂正し、再オープン。
- [x] #3/#5/#8の実行計画を作り、#5の最初のCLI compositionを実行して結果を記録した。全アイデアの検証完了ではない。
- [ ] テーマごとに残りのIssueを確認し、アイデア・既存成果・優先順位・実行項目を結ぶ。
- [x] 現行ゴール・統合計画・quickstartを短い入口へ分離し、Git原文を同じdocsディレクトリ内の履歴として保存。作業選択は[worker work map](WORKER_WORK_MAP.md)へ接続。
- [ ] 残りの研究テーマと入口を照合し、各アイデアを既存成果・次の検証へ結ぶ。
- [ ] PRを実装差分・後継・証拠所在で分類し、重複と統合待ちを減らす。
- [ ] 保全済みの不要branch/worktreeを整理する。

バッチごとに、確認したアイデア、再利用できる成果、新しく実行した検証、結果で変わった採否・次の作業を残す。未実行の計画は実行済みと数えない。最終的には、任意の研究項目から現在の実装・証拠・未解決点・次の作業へたどれ、優先するアイデアが実際に検証されていることを確認する。

## 進捗と次の整理対象

[Calc移植の証拠と次の課題](../research/live_control/calc_saved_convergence_20261016/README.md)では、
古い1ケース時点のREADMEから、完了した4ケース・保存ファイル採点・joint usageへ入口を接続した。
保存済み監査を通常・最適化Pythonで再確認し、Windowsのmutation overlayのパス差を別runnerで修理した。
原本568ファイルは変更せず、経路別費用・有限回復・現行sourceでのライブ検証は未達として残す。

[カバー取消の収束記録](../research/doom/v39_cover_cancel_convergence_20261016/README.md)では、
未統合PR #8384の15ファイルを元のblobのまま保全し、重複ケースを見逃す監査の指摘を
別版で検証した。現行テストの古いfixtureも修理し、planner割込み応答待ちが解放失敗の
確認を止める残差を新たに判別した。過去の構成PASSを実機の解放・回復PASSへ読み替えない。

[2026-10-15の統合・保全記録](maintenance/consolidation-progress-20261015.md)に、mainへ届けた修理、PR stackの収束、ローカル作業ツリーの未統合変更と保全先をまとめた。mainがクリーンであること、研究候補が保全済みであること、リポジトリ全体の整理完了は別々に確認する。

Dockerless local-iteration documentation is also reconciled: successor [#8882](https://github.com/Unjuno/agent-interface/issues/8882) delivered the residual-workflow inventory in merged [PR #8884](https://github.com/Unjuno/agent-interface/pull/8884), at [`research/outputs/wsl3-docker-residual-inventory-20261012.md`](../research/outputs/wsl3-docker-residual-inventory-20261012.md). The inventory keeps native WSL as the ordinary local route and WSLc for eligible image-bound work, while retaining Docker-specific frozen recipes; it makes no performance or security-equivalence claim.

**2026-10-17 PR reconciliation (snapshot at catalog head `e75b63224b0d37b0b896d1c0b66a80ef51e0e3c4`):** [PR #9005](https://github.com/Unjuno/agent-interface/pull/9005) and [PR #9012](https://github.com/Unjuno/agent-interface/pull/9012) were open, both `CLEAN`, with all reported required checks passing and no recorded review decision. They share only `docs/IDEAS_AND_OUTCOMES.md` and `docs/ideas/README.md`, with no duplicate newly added outcome IDs. PR #9005 retains the canonical family notes for constrained diagnosis, privacy discovery, lossy evidence, joint reserves, and macro validation; #9012 omits those copies and keeps its distinct entries. #9012 adds concise proposal summaries for 49 open Issues that had been represented only by machine-readable inventory; the summaries describe the questions without setting allocation status or execution authority. Later head and review state should be read from GitHub; neither PR was recorded as merged in this snapshot.

**2026-10-17 open-PR delta:** a fresh GitHub read returned 521 open PRs, up from 517 in the 2026-10-16 r3 inventory: seven entered the open set and three left. The [delta review](maintenance/open-pr-delta-20261017.md) classifies those ten transitions. It preserves #8714's branch because open #8720 still uses it as its base and records the two closed V39 PRs against their existing successor/custody notes. Among newly open PRs, #9006 remains a draft: native-mcp reports four failures in relay/source-dependency/handle-bridge tests, and the native Win32 fixture returns `release_unverified` where an existing test expects `completed`. Its diff adds tests only, so it does not demonstrate verified release behavior.

**2026-10-17 issue/branch reconciliation:** A fresh open-Issue export returned 1,677 issues. A direct-reference scan across current `main`, PR #9005, and PR #9012 found all 1,677 referenced and zero unreferenced. This covers current open Issues, not every historical closed issue or every PR. The citation-audit subset remains 49 Issues; separate #8872 and #8870 notes preserve their distinct unverified proposals, with #8872 retaining #5776's failed early-warning result. Nine additional closed/superseded remote branch names were removed after exact-tip, worktree, protection, open-PR and pull-ref checks; the receipts are in [the branch cleanup log](maintenance/branch-cleanup-20261017.md). This remains progress, not repository-wide completion.

**2026-10-17 PR overlap correction:** A fresh file-list comparison at #9005 head `63d4d22f54adb626920b2d547a587421e63bbbfe` and #9012 head `11286bcda198719013adf6e8daeba025b8e08385` found a third shared path, `docs/ideas/skill-conditioned-terminal-event-memory.md`, in addition to the two indexes. #9005 contains the fuller #8886 proposal; #9012's duplicate page and index entry were removed. The shared outcome index had 55 Issue IDs with differently worded rows in both PRs. #9012 now combines both summaries for all 55 IDs, preserving distinct outcomes and qualifications in one row; it also moved the #8887, #8889, #8897, #8898, and #8900–#8905 research proposals out of the engineering/operations and early-history sections into `Recent open ideas`. That section has no repeated primary Issue IDs, and five byte-for-byte repeated rows were removed earlier. The corresponding 55 older rows still remain in #9005 and need cleanup before both PRs can integrate without duplicate Issue entries. The #9005 update worktree at `/private/tmp/agent-interface-9005-update` was still dirty at its original HEAD during this review and was left untouched.

**2026-10-17 overlap follow-up:** PR #9005 advanced to `b0e2ff0b137ef9add65398e4ecc8e06f39ad11f7`, removing the 55 newly added primary Issue rows shared with #9012. A comparison of both current PR diffs against `main` now finds zero shared changed primary Issue IDs. The focused index check passes locally; hosted checks for #9005 are queued and neither PR has a recorded review decision. The older `/private/tmp/agent-interface-9005-update` worktree remains untouched. Its #8668 agenda update is now identical to the #9005 file at `880c6b63036`; its stale #8631/#8668 index additions are superseded by the fuller rows already present on the updated #9005 head.

**2026-10-17 PR merge preview:** `git merge-tree --write-tree` across current #9005/#9012 heads found content conflicts in `docs/IDEAS_AND_OUTCOMES.md` and `docs/ideas/README.md`, despite zero overlapping changed primary Issue IDs. Keep the conflict boundary explicit; resolve both shared indexes in the authorized integration change before claiming the pair can merge cleanly.
