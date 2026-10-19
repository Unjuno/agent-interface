# リポジトリ全体の整理計画

## Current execution checkpoint — r51 discovery queue and disjoint work batches

The latest complete live membership read is [r51](maintenance/repository-inventory-20261019-r51.md), captured 2026-10-19 00:20:08 UTC against main `0dafeff35e73316216c95d37f9f7e799bf8a21a8`: 1,675 open Issues and 503 open PRs. The immutable [r51 coverage audit](maintenance/idea-index-coverage-20261019-r51.md) finds 1,184 open Issues with historical primary rows and 491 without. Of the latter, 220 have a literal URL in an individual idea file and 271 do not. The [r51 queue](maintenance/open-issues-missing-research-primary-row-20261019-r51.csv) partitions the 491 by number into twenty non-overlapping batches of at most 25, so orchestration can assign disjoint discovery scopes. Those batch IDs and citations are routing aids, not semantic classifications. Workers must read live evidence; only one integrator at a time edits shared indexes. Preserve ideas and source history, and close only on each Issue's evidence-based disposition.

### B01 bounded intake — idea routing complete, dispositions remain open

The [B01 routing receipt](maintenance/issue-discovery-b01-20261019.md) covers the first 25 number-sorted queue entries. It checked each live Issue's body, open state, assignee field, and latest comment for navigation. Existing family notes cover the visual, reactive-macro, safety/control, risk-semantics and model-coupling groups. New parent-idea summaries were added to `IDEAS_AND_OUTCOMES.md` for #9, #11, #12, #18, #21, #22, #23, #25 and #28, preserving the difference between parent questions and narrower successors. No linked PR/raw/code or historical comment set was fully audited in this intake; empty assignee fields do not prove absence of active work. No Issue/PR state or experiment outcome changed. The next bounded intake is B02; workers must verify live ownership and use disjoint additive outputs.

### B02 bounded intake — effect, readiness, state, and orchestration ideas

The [B02 routing receipt](maintenance/issue-discovery-b02-20261019.md) covers the next 25 r51 rows. It adds parent summaries for #30/#31/#33/#34/#35/#37/#40/#44/#45/#46/#47/#48/#49/#53, refreshes the #57 checkpoint to merged #8986's finite synthetic-editor recovery result and the remaining supported-editor adapter seam, and routes #60/#61 as coordination/authority records rather than idea assignments. #30's semantic PASS and #48's readiness composition remain synthetic; no live app, effect, or end-to-end result is claimed. #60's sibling ownership remains UNKNOWN and #61's grants remain HOLD. No Issue/PR state or experiment outcome was changed. B03 is the next intake; recheck exact ownership before assigning it.

### B03 bounded intake — MAP01, lifecycle, and watcher evidence

The [B03 receipt](maintenance/issue-discovery-b03-20261019.md) routes the third 25-row batch. Most items already have curated outcome rows; new parent summaries cover #137/#186/#197, and #104 now reflects its corrected `HOLD_GRID_TOO_COARSE` outcome. The spot-checked PR chain #147/#169/#179/#181/#192/#206/#207/#220/#231/#267/#277 is merged, while issue-level questions remain open. #197's cooperative validation result has a source/raw custody gap in the author comment and must not be inferred from merged #220. B04 is next; check exact owners before any assignment. No Issue, PR, or evidence state changed.

### B04 bounded intake — publication identity, GUI selection, and accessibility

The [B04 receipt](maintenance/issue-discovery-b04-20261019.md) routes the fourth 25-row batch without pooling unlike outcomes. It adds the missing index rows for #375/#383/#389: #375 remains an unmeasured proposal, #383 retains a scoped post-check wrong-target result, and #389 retains a standard AT-SPI event-transport positive control without a document-selection identity claim. Nineteen explicitly linked PRs were merged and three closed without merge in the live spot-check; this is not a full PR/branch ownership audit. All 25 Issues were open and unassigned at the read, which does not prove no worker owns a branch or local artifact. No Issue/PR state or experiment outcome changed. B05 is the next intake; verify exact ownership before assigning work.

### B05 bounded intake — effect outcomes, AT-SPI identity, and native lifecycle

The [B05 receipt](maintenance/issue-discovery-b05-20261019.md) routes rows 101–125 and adds the missing summaries for #415/#481/#510/#584/#603. It preserves #415's unresolved selection-to-event identity question, #481's process/thread HOLD, #510's unexecuted dependency hold, and the distinct stopped allocations #584/#603. The 18 sampled linked PR references are merged; this is not a full PR or owner audit. The three old exact-head cleanup candidates noted by #672 are already absent from remote refs and open PR head/base lists, while their commit remains in `origin/main`; no ref deletion was needed. No Issue/PR state or experiment disposition changed. B06 is next; recheck owners and source custody before assignment.

### B06 bounded intake — observations, reservations, and retained evidence

The [B06 receipt](maintenance/issue-discovery-b06-20261019.md) routes rows 126–150 and adds the seven missing idea summaries. It preserves distinct MAP01, X11, readiness, planner-gap and evidence-custody questions, including explicit reservation/ownership boundaries and consumed or stopped allocations. Of 23 sampled PR citations, 19 are merged and four closed without merge. The batch is not assignment-ready from the empty assignee fields alone: refresh branches, worktrees, owners and raw custody first. No Issue/PR state or experiment disposition changed. B07 is next.

### B07 bounded intake — source custody, timing, and worker policy

The [B07 receipt](maintenance/issue-discovery-b07-20261019.md) routes rows 151–175 and adds four missing outcome summaries. It also checks #2369 against current repository settings: `main` is unprotected and there are no repository rulesets, so the CI-equivalent-before-push text is not an enforced gate. The Quickstart now directs workers to run relevant local checks, record hosted-only gaps, and open PRs without waiting on slow CI; it does not impose a full-suite or reviewer-count requirement. Shared-index edits can conflict, but disjoint worker paths remain parallel. No Issue/PR state or research disposition changed. B08 follows.

### B08 bounded intake — integration, evidence custody, and local-controller ideas

The [B08 receipt](maintenance/issue-discovery-b08-20261019.md) routes rows 176–200 and adds eleven missing direct outcome summaries, plus direct entries for governing #2789 and #3352. It keeps target binding separate from release/effect, preserves unrecovered or comment-only evidence as HOLD, distinguishes construction/synthetic Local System-1 results, and records #3857's static STOP and #3876's outstanding integration boundary. Nine linked PRs are merged and #8246 remains Draft. All 25 Issues were open and unassigned at intake; no Issue/PR state or research disposition changed. B09 is next. Workers may take disjoint Issues and paths concurrently; shared index edits still need serialized integration.

## Previous execution checkpoint — organize by research family

The latest complete paginated membership snapshot is [r50](maintenance/repository-inventory-20261019-r50.md), captured at `2026-10-19 00:11:08 UTC` against main `ec2ae97094ef2bf8e68e6cd4c21c6dba48521bd5`: 1,675 open Issues and 503 open PRs. Counts and sorted ID hashes match r49; metadata is refreshed at the post-merge main tip. This establishes discovery membership only. Semantic triage and ownership verification remain incomplete.

This update rechecks visual-interface Issue [#5](https://github.com/Unjuno/agent-interface/issues/5) against live sources. Its broad research menu stays open and is organized in the existing [visual-interface agenda](ideas/visual-interface-agenda.md). Merged PR [#9016](https://github.com/Unjuno/agent-interface/pull/9016) contributes 31 standard guarded-MCP Fake X process-generation/window-lifecycle tests in normal and optimized Python. The result narrows a caller-construction gap; it does not qualify native X lifecycle, physical release, independent task effect, bounded recovery or matched economics. Keep those residuals in their existing family/parent issues and choose the next work only after checking current ownership and the eligible environment. Do not close #5 or create a successor solely to reduce counts.

For parallel orchestration, workers should take distinct issue/PR families and separate additive output paths; the shared work map and idea indexes have one editor at a time. Each family handoff records its live source, question, retained result and limits, owner/collision boundary, and one finite next step. Unclassified items stay in a visible queue. This is the execution plan; the active computer-control goal remains broader than repository cleanup.

## Repository-wide organization plan: preserve ideas, enable parallel work

The user-requested clean state means a repository where a worker can choose one bounded, nonconflicting task and reach its question, source, evidence, owner boundary, and next decision without reconstructing history. It does not mean zero Issues, zero PRs, or deleting old experiments. Organize the research so ideas can be prioritized and executed; close or merge individual GitHub items only after their own evidence-based disposition.

### Workstreams and order

1. **Refresh the map.** Reconcile the current main SHA, complete open/closed Issue and PR membership as needed, active PR heads, and worker/worktree ownership. Keep dated inventory snapshots immutable. Any search cap, sparse checkout, or unavailable host must be recorded as a limit, not treated as absence.
2. **Group ideas by falsifiable question.** Use the existing family agendas and `IDEAS_AND_OUTCOMES.md` as navigation. For each family, connect source Issues, distinct hypotheses, strongest simple baseline, decision-changing observation, existing code/PRs, experiment packets and raw, known counterexamples, unresolved boundary, dependencies, current owner, and one finite next discriminator. Preserve different hypotheses and outcomes even when they share a family page.
3. **Separate research disposition from repository state.** Research states describe whether a question is unverified, ready, active, result-retained, blocked with a reason, rejected with evidence, or transferred. Issue states describe whether that specific request is met, still open, or moved to a real successor. PR states describe whether its exact diff should be integrated, repaired, retained elsewhere, rejected with evidence, or left for an owner. Do not infer one state from another.
4. **Consolidate implementation and evidence navigation.** Keep supported code in canonical runtime modules; point duplicate prototypes and historical snapshots to their family record rather than silently deleting or merging unlike semantics. Keep raw and first outcomes in place and immutable; improve indexes and README links so current evidence is easy to reach. Separate canonical source, executable checks, retained result packets, and generated/temporary work.
5. **Make parallel assignments safe.** A handoff names one family and question, exact Issue/PR/ref, source SHA, allowed code paths, a unique additive output path, owner/collision boundary, shared-resource needs, and a finite stopping condition. Independent families may proceed concurrently. A shared index or work map has one integrator at a time; this serializes only the shared edit, not independent research.
6. **Reconcile each item and recover only proven clutter.** For every Issue/PR, record its evidence-backed disposition and destination. For branches, worktrees, local artifacts, and generated files, verify exact tip, active user/owner, PR dependency, unique raw custody, ignored/untracked contents, and recovery path before cleanup. Unknown ownership or unique evidence means retain and label for follow-up.

### A family record that lets a new worker start

Each family record should be concise and answer: **What can the system do today? What precise behavior is still uncertain? What is the strongest simple comparator? What observation would change the design or adoption decision? What result already exists, and what does it fail to prove? Who or what owns overlapping work? What is the next finite check, its prerequisite, and its stop condition?** Link to source Issues/PRs and immutable experiment packets instead of copying long history. If any answer is unknown, mark it unknown and route the item to the unclassified queue.

### Completion gates

- A current, timestamped discovery baseline exists, with its completeness and limits stated.
- Every known active research family is reachable from the repository entry points; every unfinished family has either a finite next step or an explicit reason it cannot start.
- Workers can select disjoint family/code/output scopes without editing the same shared index or consuming the same live resource.
- Every Issue and PR touched has an individual disposition with links to the retained idea and evidence. No item is closed solely to reduce counts.
- Every retained experiment has conditions, raw/first result, source identity, interpretation, and boundary reachable without altering its historical record.
- Any removed local/branch/worktree artifact has verified ownership, dependency and recoverable custody. The cleanup log records exact targets and proof.

Until these gates are met, maintain an explicit unclassified queue and work through finite batches. Do not make completion of all 1,675 historical Issues or all PRs a prerequisite for useful research. This organization supports—not replaces—the active computer-control goal.

### Current semantic-family batch — visual-interface Issues #3/#4/#5/#7/#8

The live Issues were rechecked on 2026-10-19: #3, #4, #5, #7 and #8 are all
open. The [family record](ideas/visual-interface.md) and
[execution agenda](ideas/visual-interface-agenda.md) now distinguish #4's
north-star thesis from #3's grid presentation, #5's visual-address/feedback
contracts, #7's selection of view sets under a fixed cost budget, and #8's
composite encoding. Existing #1946/#1968 package-integrity findings are reuse
inputs, not new #7 evidence. The #2031 model-facing localization score is
quarantined because candidate response schema and scorer disagreed about the
required abstention field; it does not establish model accuracy. All five
source Issues stay open; no idea or result was closed to reduce counts.

The next finite discriminator is a read-only crosswalk of #1946/#1968/#2031
source, raw and audit against #7's set-complementarity question. A new model
comparison is considered only if that crosswalk identifies a remaining
decision-changing condition. #7's selection question remains separate from
#8's encoding comparison and #4's broader thesis.

### Current evidence-routing batch — A02/A03 blocked-X11 caller attempts

The first pair of WSLc attempts has been given a single navigation record at
[standard-caller blocked-X11 release](../research/integration/standard_caller_blocked_x11_release_20261019/README.md).
A02 is a runner/source-mount STOP before the probe began. A03's first healthy
control passed; its first blocked trial timed out before the expected held-reply
marker, so the registered acceptance gate failed and the run stopped. The exact
first outcomes, frozen conditions, source hashes, raw, and resource cleanup
receipts remain in their immutable A02/A03 packet directories. The common note
states what each attempt proves and what it does not. Read-only source/raw
diagnosis identifies a likely circular reply gate: a pre-press process-identity
reply can be blocked by the gate that waits for the KeyPress which that identity
check precedes. The next finite discriminator is an offline proxy-framing check
with per-connection sequence evidence.
This is one completed evidence-routing correction, not a semantic completion of
the release issue. No issue or PR is closed by this update.

## 現行の実行方針：アイデアを保ったまま収束する

「クリーン」はIssue/PRをゼロにすることではなく、研究の問い・根拠・担当中の変更が迷子にならず、各workerが独立した次の一手を選べる状態とする。Issueを一律に閉じず、まずテーマ別に問いをまとめ、実際の結果と移管先を確認してから個別に処置する。以下はこの文書の長い更新履歴を読む前に使う現在の運用要約である。

### アイデアの整理単位

Issueごとのタイトルではなく、反証可能な研究上の問いを単位にする。テーマ別agendaには、少なくとも次を短く結びつける。

- 出典Issueと現在状態。提案・計画・実行中・実行済みを区別する。
- 仮説、最も強い単純な比較対象、成立しないと判定する観測。
- 既存コード・実験・raw・監査結果と、それぞれが証明していない境界。
- 未解決の残差、依存、競合範囲、必要な資源または未確認事項。
- 次の有限な検証と、結果により採用・修理・保留・棄却のどれを選ぶか。

候補は `unverified`（問いは残るが実測なし）、`ready`（条件と権限が揃い着手可能）、`active`、`result-retained`（結果は保存、親の問いは未達）、`blocked-with-reason`、`rejected-with-evidence`、`transferred` のように状態を明示する。索引への掲載、Issueの作成、PRのmergeだけで研究結果や完了とはみなさない。類似案は共通仮説の下にまとめても、固有の比較・反例・結果は別々に残す。

### 実行順：入口を直してから、家族単位で収束する

1. **基準を固定する。** 現行 `main` SHA、GitHub Issue/PRの全ページング件数とID集合、スナップショット時刻を記録する。Sparse checkoutでは、作業ツリーに見えないことを削除・欠落の証拠にせず、Git indexまたは対象refのtreeを確認する。
2. **現行の入口を一本化する。** `README.md` → `docs/CURRENT_GOAL.md` → `docs/WORKER_WORK_MAP.md` → family/evidence → 有限な次作業を辿れるようにし、古い入口から正本へのリンクを直す。履歴文書と結果rawは内容を書き換えず、必要な場合は新しいナビゲーションを足す。
3. **アイデアを家族ごとに整理する。** 未分類Issueの固定キューを discovery source として使い、各バッチで live Issue・必要なコメント・正確なPR head・mainの実装・保持証拠を再確認する。共有台帳へ「問い/別仮説・状態・証拠と限界・依存/所有範囲・次の識別作業」を記録する。複数familyの調査は独立範囲で進め、共通indexの編集だけ一人ずつ統合する。
4. **Issueを個別に扱う。** closeはIssue自身の受入条件達成、証拠に基づく棄却、または未解決分を保持した実在後継への移管を確認した場合だけ行う。提案の記録、古さ、未割当、PR merge、件数削減はclose理由にしない。完了しても親のコンピューターコントロール目標が残る場合は親をopenに保つ。
5. **PRと作業場所を別々に収束する。** PRの正確なhead/base、差分、stack依存、独自raw、ローカル検証、作者/保全先を確認する。branch/worktree/artifactを回収する前にtip・利用者・未追跡/ignoredファイル・開いているPR依存・復元経路を確認する。持ち主不明やdirtyな作業物は維持し、所有と保存先が確認できたものだけ整理する。

各バッチは、確認した範囲、保存先リンク、独立した研究結果の有無、未分類残数または次の対象、競合境界を短く記録する。合格はIssue/PRゼロではなく、現行work mapから一意で有限な独立作業を選べ、各未完項目から問い・結果・限界・次の行き先へ往復できることとする。

### Issue・PR・refは別々に判定する

Issueを閉じるのは、受入条件を満たした根拠がある、重複元の固有の残差と結果を保存済みの実在する後継へ移した、または仮説を棄却する観測がある場合に限る。古さ、未割当、文書化済み、PR mergeだけではcloseしない。親Issueは個別の有限結果が出ても上位のコンピューターコントロール目標が未達ならopenのままにする。

PRは正確なhead/baseと差分、既存mainとの重なり、依存stack、意味のあるローカル検証、独自の証拠/raw、現在の作者・保全状況を確認し、「統合」「修理して継続」「固有部分を移管・保全して終了」「根拠付き棄却」「確認待ち」に分類する。CIの状態やdraft/ageだけで判断しない。merge済みPRのbranch、worktree、生成物は、tip・open PR依存・未追跡/ignoredデータ・利用者・rawのcustodyを個別に照合してから回収する。

### 完了の目安と実行順

全件を一度に意味分類する前提にはせず、完全な時点付きmetadata inventoryを起点に、研究テーマ一族ずつ意味を読み、indexとIssue/PRの状態を更新する。共有indexは一人のintegratorが直列に編集し、他のworkerにはIssue/PR範囲・コード範囲・出力先を分けて渡す。分類未完了の集合は、次に処理する明示的な作業キューとして保持する。

整理の合格条件は、現行の未完Issueにそれぞれ研究上の行き先または未分類キューがあり、検証済みの独立成果がmain/保存先から辿れ、PR stackとbranch/worktreeの保全状態が現物確認済みで、次の競合しない有限作業が選べること。open件数が残っていても、この条件を満たすものは「未完了」ではなく意図した研究バックログである。歴史的なraw・条件・第一結果は移動・上書きせず、索引で結ぶ。

## 実行更新 r45 — standard caller結果を統合し、現在のopen-setを再照合

2026-10-18 23:00:51 UTCに再取得した全ページングmembershipでは、main
`33cb7b9368d612494c1b95ee0099335a3b288950`に1,675 Issue / 504 PRがopenで、
両ID集合はr41と同一だった。#9099/#9100/#9101を統合し、#6/#56のfamily記録と
#17のstandard-caller Xvfb結果をmainから辿れる。時点付きhashは[r43](maintenance/repository-inventory-20261019-r43.md)。

PR #9099のhead `8ce4e52a28d393128dc769fc35bcaecd22c94a08`はprivate X.Org
Xvfb run [39174301979](https://github.com/Unjuno/agent-interface/actions/runs/39174301979)
を含む必須check全件成功後、merge commit `33cb7b9368d612494c1b95ee0099335a3b288950`
として統合した。XRes PIDと`/proc` start ticksからのprocess/window generation binding、
standard-callerのKeyPress/KeyRelease、verified neutral release、独立X property
`[1]`、独立keymapのup readback、destroy後のstale alias拒否とquery worker退役を
rawで保全した。七回分のrawとscopeは[結果記録](../research/integration/standard_caller_xvfb_generation_20261019/README.md)。

これは合成アプリと一つのprivate Xvfbに限定したcomposition PASSであり、Issue #17はopen、
releaseは`UNKNOWN`のまま。初期held inputを伴うowner crash、blocked server I/Oのrelease
bound、実アプリの独立task effect、MAP01、general recovery、matched economicsは未検証である。
次の有限な識別作業はstandard caller経由のinitially-held key + owner disconnect + 独立readback。
Issueを閉じず、上位の意味分類も完了とはしない。

## 実行更新 r44 — #6/#56の仮説・結果・未統合PRを分離

2026-10-19に、現在OPENの[#6](https://github.com/Unjuno/agent-interface/issues/6)
と[#56](https://github.com/Unjuno/agent-interface/issues/56)、関連するmerged
PR #7353/#7438、およびopen PR #7616を再読した。既存の[family record](ideas/reactive-macro-symbolic-interface.md)
に#6の広いreactive local-control案、#56のmodel-authored symbolic GUI案、A05/R02/A12–A14の結果と限界、#7616の失敗理由を分けて記録し、
`IDEAS_AND_OUTCOMES.md`とidea ledger/work mapから辿れるようにした。

判定は#6=`open-broad`, #56=`open-result-retained`, #7616=`open-review-pending`。
PR #7616の説明はcandidate/source hash不一致を`FAIL_SOURCE_BASE_LABEL_MISMATCH`
として報告し、candidate終了codeと正確な時刻も未保持としている。成果一式が一意なので、
年齢・CI・題名でclose/mergeせず、次はそのexact diff・FREEZE・candidate・audit・source
blobのread-only照合を行う。candidateは消費済みとして再実行しない。この監査は未実施であり、
PRの統合・棄却をまだ決めていない。

この一族はactive [#9099](https://github.com/Unjuno/agent-interface/pull/9099)の
Xvfb caller repairとは独立する。複数workerは別family・PR・加筆先を使い、共有indexだけ
直列統合する。Issue数を減らす目的で#6/#56を閉じず、完了条件・根拠・次の検証が揃うまで
研究バックログとして保持する。

## 実行更新 r42 — 現行membership差分と最初の修理対象

2026-10-18 22:37:50 UTCに、全ページを読み直してmain
`76ed0ee86dec7e9f8468863eaf9e682abb51d36b`に対するopen Issue 1,675件とopen
PR 505件を確認した。[r42 membership delta](maintenance/repository-inventory-20261019-r42.md)
では、Issue ID集合は[r41 inventory](maintenance/repository-inventory-20261019-r41.md)
と同一、PRは#9099の追加のみであることをハッシュ付きで保存した。これは最新の全件意味分類ではない。

今回の追加PR [#9099](https://github.com/Unjuno/agent-interface/pull/9099) は、
private-Xvfb標準caller実験の新規作業で、`x11-integration` がPython-Xlibの
`display.info.release`属性参照で失敗している。最初のrunとrawを保全し、報告値を
サーバー応答から正しく読む修理を行って再検証する。これは実行中の computer-control
成果として担当と差分を保持し、整理のために閉じたり、整理PRへ混ぜたりしない。

**収束の実行順:**

1. README → CURRENT_GOAL → WORKER_WORK_MAPから、各workerが担当/割当・固定head・
   独立出力先・衝突範囲を記録して、ひとつの有限作業を選ぶ。
2. アイデアはIssue番号でなく研究family単位に読む。まず既存の未分類キューから
   computer-control gateに直結するfamilyを選び、Issue本文/必要コメント、main実装、
   関連PRの正確なhead、既存PASS/FAIL/STOPとraw、証拠限界を照合する。
3. 各familyの固有仮説を既存台帳へリンクし、`ready / active / result-retained /
   deferred / untriaged / transferred / rejected-with-evidence`のいずれかと、次の
   判別作業を記録する。似た仮説だけを理由に独立した反例・結果をまとめない。
4. IssueとPRは別々に判定する。Issueは受入条件・根拠ある棄却・保存済み後継への
   移管が成立したものだけcloseする。PRは差分、stack依存、固有証拠、ローカル検証、
   作者/保全先を確かめて修理・統合・移管・保留・棄却を決める。
5. branch、worktree、artifactは、正確なtip、利用者、未追跡/ignored物、PR依存、
   一意なrawのcustodyと復元先を現物確認してから個別に回収する。

並行可能な作業は別のIssue/PR family、別コード範囲、別の加筆ファイルへ分ける。
共有indexの反映だけ直列に統合する。未分類の残りを明示的キューに保ち、全件分類を
実験再開のゲートにしない。成果判定は件数減ではなく、未完アイデアから根拠・限界・
担当境界・次の有限作業を辿れて、実作業が失われていないこととする。

## 実行更新 r41 — 現行mainに対するIssue/PR完全一覧を固定

2026-10-18 21:59 UTCに、GitHub CLIで全ページを読み、main
`0b452ada10c7c336e0faf89699b17f1507abcd95`を基準にopen Issue 1,675件、open
PR 504件のメタデータsnapshotを保存した。Issue ID集合のSHA-256は
`4D45620D8AAE450E7F37C9C7A0D2B183534C44094C117671362B12BB11751678`、PR ID集合は
`08808AE63A22380EC701F087EDB01B8EFD03A9DA2DDA09D0EC75D44EDFCF74C8`。
[r41 inventory note](maintenance/repository-inventory-20261019-r41.md)には取得方法・限界・CSVの内容ハッシュを記録した。

これはr30から続くIssue集合を再確認し、open PRが511件から504件になったことを固定する
membership更新である。Issue/PRの意味分類、実行所有者、PRの採否、branch/worktreeの保全状態は
判定していない。したがって、件数変化はclose・merge・削除の根拠ではなく、整理計画の意味分類と
family単位の作業キューは継続する。未分類の仕事を止めないという既存方針も維持する。

## 実行更新 r40 — #3のアイデア索引を復旧し研究へ接続

2026-10-19にIssue [#3](https://github.com/Unjuno/agent-interface/issues/3)の本文と最新2コメント、およびmain `b2c5ef9d691242f4874e09c465c19b147cc5b69c`の視覚インターフェースagendaを照合した。IssueはOPENで、merged [PR #8924](https://github.com/Unjuno/agent-interface/pull/8924)の文書化だけで研究メニューから外すのは不適切として再オープンされている。grid専用の実装/結果は確認できず、JSON presentation compositionやstream receiptは別の問いである。

`docs/IDEAS_AND_OUTCOMES.md`に#3の直接項目を追加し、work mapから参照できるようにした。状態はOPEN/unverified。次は、過去のgrid比較・rawの所在とcustodyを調べ、見つからなければno-grid / always-on / model-selectable / coarse-to-fineを比較する条件・fresh case・target score・correctness gate・費用計測の可否を事前固定する。現時点では実験・割当を開始しておらず、Issueも閉じていない。歴史的なr15 coverage countとIssue-index snapshotは変更していない。

## 実行更新 r31 — #9070統合後の現在地と整理の合格条件

2026-10-18 20:11 UTCの全ページGitHub CLI再照合で、open Issueは1,675件、open PRは514件。Issue ID集合はr22 snapshotと同じで、PR集合からは#9064だけが外れた。#9064は19:53 UTCにmerge済み。基準main `92dca0df6022fd50b2b439e6863cf2a4da05851f`には#9068、#9069、#9070も統合済み。詳細と限界は[現在の整理再開点 r28](maintenance/consolidation-status-20261019-r28.md)を参照する。r22 CSVは取得時点の記録として保ち、現行open PR一覧としては使わない。

今回の整理で守る成果は、Issue数やPR数のゼロ化ではなく、全アイデアの出典・仮説・反証/既存証拠・未解決点・依存・次の有限な作業を辿れること、各workerが衝突しない範囲を選べること、根拠のないcloseや証拠・作業の消失を起こさないこと。未検証・未分類の案は状態を明記して台帳に残す。Issueは個別の受入条件達成、重複元から保存済みの後継への移管、または根拠付き棄却が確認できた場合だけ閉じる。PR merge、Issue close、branch/worktree削除はそれぞれ別の判定とする。

次の作業は一族ごとに有限に進める。現在のidea-index coverage gapを入口に、Issue本文と必要なコメント、関連PRの正確なhead、現行source、実験証拠を照合し、テーマ別ledgerへ結果と限界を結ぶ。並列workerには別のIssue/PR範囲・コード領域・出力先を渡し、共有indexの編集と統合は直列化する。古い/dirty/owner不明のbranch、worktree、rawは保全・所有者確認・依存照合が終わるまで移動・削除しない。全Issueの意味分類を研究再開の前提にはせず、分類未完了は明示的な作業キューとして残す。

## 実行更新 r30 — #17 標準MCP callerへowner PIDを接続

現行main `ec4d3f9417c6da2156fa2af79bda9503348c1602`へ、[PR #9068](https://github.com/Unjuno/agent-interface/pull/9068)をmergeした。`OwnedGuardedSessionOwner`はsnapshot内に`owner_process_pid`を保持していたが、必須の`expected_pid`なしでPID-qualified XRes supervisorを呼んでいた。その`TypeError`は`unknown`へ変換され、標準callerからのowner identity照合が常に無効だった。callerは正確なowner PIDを渡し、欠落・不正時はfail-closedする。修正前失敗・修正後成功の回帰テスト、owned-process 10 tests normal/`-O`、CLI matrix・X11・native MCP等のCI結果をPRに保存した。

これはXRes identity observationの標準caller接続を直したもので、queue-drain/server ordering fence、物理release、有限release deadline、独立task effect、bounded recoveryは証明しない。Issue #17はopen、overall releaseは`UNKNOWN`のまま。fresh unused WSLc allocationは確認できず、ライブ実験は行っていない。次は独立したserver-side ordering/fence根拠を検討し、正式なライブ試験は所有者と未消費WSLc枠が確認できた場合だけ行う。

## 実行更新 r29 — #17 XResのresource-base再利用をPID付きで判別

PR [#9064](https://github.com/Unjuno/agent-interface/pull/9064)を、XRes 1.2の`LocalClientPID`とobserver自身のPID namespace照合を追加してmergeした。head `ebe65d4f10ced2b14554ff97973a6355b4293d0b`の専用private-Xvfb run [39160684353](https://github.com/Unjuno/agent-interface/actions/runs/39160684353)ではidle controlと対象ownerのresource baseがともに`4194304`となり、owner PID `2750`終了後に同じbaseを再利用したquery helper PID `2752`をrawで確認した。PID付き判定はowner不在と分類し、8秒後まで遅延入力は観測されず、keymapは各readbackでupだった。raw・条件・適用限界は[保存packet](../research/integration/xorg_xres_disconnect_order_20261019/README.md)に固定した。

これは一つのresponsive X.Org/Xvfb topologyでmeasurement identityの曖昧さを解いた結果であり、過去のbase-only `still_connected`をowner存続証明として扱わない。blocked server I/Oの有限release、standard caller、物理/XWayland、task effect、一般的recovery deadlineは未検証。Issue #17はopen、他topologyのreleaseは`UNKNOWN`。WSLc allocationは使っていない。

## 実行更新 r28 — #9065統合後のopen-set再照合

2026-10-18 19:41 UTCのGitHub CLI再取得ではopen Issue 1,675件、open PR 515件。
r22保存一覧と全ID集合が一致し、追加・除外はなかった。PR [#9065](https://github.com/Unjuno/agent-interface/pull/9065)のmerge状態も確認した。
この確認は一覧の所属だけを更新する。Issue本文の意味分類、担当・branch/worktreeの利用状況、PR固有証拠の監査は未完了であり、open集合が同じことを整理完了とは扱わない。
保存済みr22 CSVは変更せず、この再照合時点と結果を記録する。

## 実行更新 r27 — 最新一覧と次の一族

2026-10-18 19:32 UTCの全ページGitHub CLI readで、基準main `31c338fc8fecf3ef93ad802d2ac7ebee3bb9ff71`に対するopen Issue 1,675件とopen PR 515件を固定した。IssueのID集合はr15と同一で、PRは#9064だけが追加された。全metadataは[r22 inventory](maintenance/consolidation-status-20261019-r27.md)およびリンク先CSVに保存した。これは意味分類や担当確認ではない。

整理の目的は、仮説・アイデア・反例・raw・未解決条件を保持し、別々のfamilyを並行して調査・実装・検証できるようにすること。全Issue/PRの精読完了まで個別作業を止めない。各作業はfamilyと出力先を限定し、共通indexだけを直列に統合する。Issueは固有の完了条件、根拠ある棄却、または実際に継続できる後継への移管が確認できた場合だけ閉じる。

今回の具体的な次対象は、現在の#17 XRes disconnect observation familyである。#9064は全CIが通っているが、保存rawでは独立したidle clientと対象ownerが同じXRes resource baseを使っている。このため死後の`still_connected`が対象ownerを識別する証拠か、再利用されたbaseを後から起動した問い合わせworker自身が占めている結果かを分ける必要がある。現状は調査継続で、PR統合・物理release成功の根拠にはしない。詳細とraw参照は[r27 status](maintenance/consolidation-status-20261019-r27.md)に記録する。

## 実行計画 r26 — アイデアを保全した全体収束

**目的:** Unjuno/agent-interfaceを、複数ワーカーが同じ現在地と証拠を見つけ、独立した作業を選び、衝突なく統合できる状態へ整理する。IssueやPRをゼロにすることは目的にしない。未検証の案、失敗、反例、raw、担当中の作業は失わず、重複・古い案も出典と状態が追える形で残す。

## 2026-10-19 整理の進め方 — アイデアを残して研究を進める

この計画は、コードを動かす入口・研究仮説・実験記録・実装PR・Issue/PR/worktreeの状態を同じ道筋でたどれるようにする。現在ある大量のIssueやPRを一括で閉じたり、全案を一つの親Issueへ移したりしない。まず検索可能な家族別記録を作り、その記録から次の研究または実装を選び、完了条件に達した作業だけを個別に統合・移管・終了する。

| 領域 | 整理するもの | 維持する関係 | 最初の成果 |
|---|---|---|---|
| 利用入口と構造 | README、docs入口、ROADMAP、runtime/research/release/siteの責務と重複 | 利用者向け説明 → 現行実装 → 研究根拠 → 未達条件 | 古い説明と現行状態の食い違いを記録し、現行の正本へのリンクを直す。歴史資料は削除せず履歴として示す。 |
| 研究アイデア | 開いた/閉じた研究Issue、提案、反例、独立仮説 | 出典Issue → family entry → 既存PASS/FAIL/STOPとraw → 限界/依存 → 次の識別実験 | 既存の`docs/ideas/`と`RESEARCH_ISSUE_INDEX.md`を照合し、番号だけの一覧で取りこぼさない。先行バッチ#5305は現行本文・全コメントを照合済み。T0、T1 STOP、後続ポリシー結果、未確認raw custodyを[family entry](ideas/conflict-aware-evidence-ledger.md)に保ち、T0の再実行とIssue closeは行わない。 |
| 実装・証拠 | Open PR、main上の実装、保存済み実験、重複または後継成果 | Issue仮説 → 正確なPR head/diff → テストとraw → 採用範囲 → 未解決の親問い | PRは研究familyごとにmainとの差分と証拠を確認する。独自結果と唯一rawの保全前に、重複に見えるPRも閉じない。 |
| 実行状態 | Branch、Git worktree、ローカルworkspace artifacts、割当/利用中資源 | owner/session → Issue/PR → branch/path → unique output/raw → recovery route | `known / unknown / verified`を分ける。unknown ownerや未照合pathは保持して調査し、確認済み保全先なしに削除しない。 |

各familyの判定は`active / queued / deferred / duplicate-successor / completed / rejected-with-evidence / untriaged`に揃える。`untriaged`は不足を明示する有効な結果であり、`completed`へ繰り上げない。Issueを閉じるときは、Issue自身の完了条件または証拠に基づく棄却を示す。未解決の問いが残るなら、実際に継続できる後継Issue/実験先へ仮説・根拠・次の作業を移す。アイデアの文書化、経過時間、空の担当欄、似たタイトルだけでは終了理由にならない。

研究を止めないため、全件棚卸しと局所作業は並行して進める。各作業の開始時に対象Issue/PR、固定headまたはmain SHA、触る出力、衝突境界を記録する。共有索引はfamily entryを一件ずつ統合する。担当不明を無主物扱いせず、独立した読み取り監査・ローカル検証は確認待ちの間も進める。PRの統合は、現行権限と保護設定に従い、ローカル検証を根拠に判断する。任意CIや架空の必須レビュアー人数を一律の停止条件にしない。

**この整理の出口:** 新しいworkerがREADMEとwork mapから始め、現行ソースと研究familyへ移動し、範囲が競合しない有限作業を一つ選べること。全Issue/PRは最新のページング一覧に対する意味判定または明示的な`untriaged`状態を持ち、各アイデアから証拠・残る問い・次の行き先へ戻れること。未解決研究や固有成果を消さずにこの状態を達成する。

**現在の全体像 (r15 metadata / r20 membership recheck, 2026-10-19 JST):** 2026-10-18 18:59:33 UTCにページングされたGitHub CLI一覧を取得し、origin/main `c2eae1a5aac951eb3560f6d6774fe23ce4fc7128`でopen Issue 1,675件、open PR 515件を確認した。[r20 recheck](maintenance/repository-inventory-20261019-r20.md)でIssue ID集合はr15から不変、open PRには#9057が追加され、r15時点の514件はすべて残っている。最新の全metadata CSVは[r15 inventory](maintenance/repository-inventory-20261019-r15.md)であり、r20は新しい全件CSVを重ねず、membership差分だけを記録する。この確認は一覧/メタデータの更新であり、本文の意味分類、実担当、PR固有証拠、ローカル作業ツリーの完全照合ではない。PR #9049で入った[r15 idea-index coverage audit](maintenance/idea-index-coverage-20261019-r15.md)では、1,675件中491件が主Issue表にない。うち220件はidea family文書にURLがあり、271件は個別family記録で未確認。これはナビゲーション上の欠落であり、意味判定やclose理由ではない。全件意味分類は未完了。過去のスナップショットは取得時点の履歴として保持する。

**次の優先バッチ:** 件数の小さい順ではなく、コンピューターコントロールの未達ゲートに沿って一族ずつ整理する。既存の#17（入力解放と安全制御）、#5（対象同定と視覚フィードバック）、#59（MAP01連続制御と回復）、#57/#2789（統合・独立効果確認・効率）を入口として、各一族から関連する後継Issue、PR、main上の成果、保持rawをつなぐ。各Issueの状態と固有残差は個別に記録し、似ているだけの仮説は統合しない。研究ゴールへの寄与が薄い/不明な残りは`untriaged`または`deferred`に置き、次の適格なワーカー作業を提示する。共有索引の更新は一族ごとに直列化し、別familyの読み取り監査・ローカル検証・独立実装は並行可能な範囲で進める。

**2026-10-19 r33 — #17 input-release family after PR #9047:** PR [#9047](https://github.com/Unjuno/agent-interface/pull/9047) merged at main `34344716c62d04d237a149fb97aabebd56944ca8`. Its standard-caller Fake X regression keeps release `UNKNOWN` after injected owner retirement, XRes disappearance, cleanup readback, and a late queued DOWN. The focused owner/cancel/target-generation tests passed in normal and optimized Python; the retained report links raw logs and hashes. This closes that PR's implementation task only. Issue #17 remains open; its [latest scoped update](https://github.com/Unjuno/agent-interface/issues/17#issuecomment-6253086476) records the result. The regression is an adversarial Fake X composition, not evidence that a live X server schedules the same sequence, and it establishes no physical release deadline, application effect, MAP01 success, or matched efficiency. Continue the next distinct scientific family; do not close the parent or treat the synthetic counterexample as a live-server finding.

**2026-10-19 r34 — #5305 held-out raw custody check:** The source [T1 result comment](https://github.com/Unjuno/agent-interface/issues/5305#issuecomment-5907937584) reports a relative `work/5305-heldout/raw.json` path and SHA-256. A read-only check found no raw at the expected path in the current consolidation checkout, adjacent `agent-interface` checkout, or sibling workspace location; `origin/main` contains only the original T0 raw. This is `READBACK_UNAVAILABLE_IN_CHECKED_LOCATIONS`, not proof of deletion or owner loss. The 4/8 T1 result remains `STOP / incomplete evidence`; no raw hash was independently recomputed, no rerun occurred, and no Issue was closed. The family note records exact scope and next action: recover the owner-attested original or freeze a distinct held-out comparison with a new allocation.

**2026-10-19 r36 — first semantic triage from the missing-row queue (#2):** Re-read current [Issue #2](https://github.com/Unjuno/agent-interface/issues/2) and the result comments on closed [#821](https://github.com/Unjuno/agent-interface/issues/821) and [#823](https://github.com/Unjuno/agent-interface/issues/823). Recorded #2 as **active / keep open** in the existing [safety-control family entry](ideas/safety-control-agenda.md): #821 supports one cleanup-only owner-crash boundary; #823 shows that X-server stall delays backend release confirmation. These scoped results do not close #2's broader architecture-risk register; original raw was not re-audited. No experiment was rerun, no Issue/PR state was mutated, and no historical inventory was rewritten. #2 remains a missing primary-row discovery item by design; this is one semantic triage, not a change to the 491-row snapshot.

**2026-10-19 r37 — visual-grid family crosswalk correction (#3):** Current Issue #3 is open again after its proposal was initially archived by merged documentation PR #8924 and then reopened to keep ideas in the research queue. Inspection showed that the agenda's cited `PRESENTATION_CHOICE.md` and `PRESENTATION_EMISSION.md` describe JSON result composition and stream receipts, not visual grids. Corrected the #3 row to remove that false evidence edge and made the actual next work explicit: locate any retained grid-specific comparison/raw and verify custody; otherwise freeze a matched comparison before execution. No prior result was promoted, no experiment/allocation was run, and no Issue/PR state changed. See the [visual-interface agenda](ideas/visual-interface-agenda.md).

**2026-10-19 r38 — #9050 plan update merged:** The five-document consolidation update in [PR #9050](https://github.com/Unjuno/agent-interface/pull/9050) merged at `f47817cd70949e1a32785cbbe5161b5e8853582c`. Local `git diff --check`, public-navigation validation (26 documents / 2,153 relative links), and the deterministic #3270 scorer replay tests (2/2) passed; GitHub `public-navigation` and `replay-gate` passed, while `formal` was skipped. A post-merge paginated read found 1,675 open Issues and 514 open PRs, with both ID sets and serialized CSV hashes unchanged from r15; see [r17 inventory](maintenance/repository-inventory-20261019-r17.md). No Issue was closed and no experiment allocation was used.

**2026-10-19 r39 — #17 A11 evidence reconciled into the consolidation plan:** The current [safety-control family record](ideas/safety-control-agenda.md) links the retained [A11 WSLc/Xvfb packet](../research/integration/xres_blocked_owner_release_a11_20261019/README.md), which reports 8/8 frozen trials: an owner remained blocked in `XSync` while the responsive Xvfb served an independent XRes observer and KeyRelease connection; owner retirement alone left the key down, and a separate KeyRelease produced immediate and 50 ms key-up readback. This narrows the live-server uncertainty for that fixture and topology. It does not qualify the standard guarded-MCP caller, physical/XWayland input, permanently blocked server I/O, application task effect, general recovery deadline, or efficiency. Issue #17 was still open on the latest read (`2026-10-18T17:44:50Z`). The A11 allocation is consumed; do not rerun it or infer a new WSLc allocation. Next #17 work must compose the retained live-server boundary with the standard caller or otherwise close a distinct remaining gate, only after a fresh allocation is confirmed unused; until then preserve `UNKNOWN` for untested topologies. This updates the next-work map without changing historical inventory snapshots or closing any Issue.

**2026-10-19 r40 — #5 caller evidence connected to its idea family:** Current [Issue #5](https://github.com/Unjuno/agent-interface/issues/5) remains open. Its latest update points to merged [PR #9016](https://github.com/Unjuno/agent-interface/pull/9016), whose report records 31 standard guarded-MCP process-generation/window-lifecycle tests passing in normal and optimized Python. The family record and [worker map](WORKER_WORK_MAP.md) now link that evidence and state its boundary: Fake X construction only; live XRes/PID-namespace trust, native event delivery, atomic check/use, physical release, application effect and recovery remain unqualified. The next target-binding gate is native event delivery plus capture-to-press continuity on an eligible real X target. No allocation was run, no Issue state changed, and no historical snapshot was rewritten.

**2026-10-19 r41 — post-merge open-set membership recheck:** After consolidation PRs #9052 and #9053 merged, paginated GitHub CLI reads at 2026-10-18 18:26:54 UTC found 1,675 open Issues and 514 open PRs at main `678b9285fd6c05de9f1b395c0ef157bc5e3b3e14`. Both ID sets match r15; see [r18 membership recheck](maintenance/repository-inventory-20261019-r18.md). r15 remains the latest full metadata snapshot, so no duplicate CSV was written. This confirms that these documentation integrations did not reduce the open-set inventory; semantic classification and safe disposition remain the work, not count reduction. No Issue was closed.

**2026-10-19 r42 — owned cancel-response timeout repair:** At main `35e5a1c08f6ba604f0f6b2110381c9025784935e`, a new regression reproduced that a missing cancel control response returned `cancel_unconfirmed` while leaving the exact owned process alive. The repair retires that process on timeout, control-pipe closure, and negative acknowledgement; the receipt reports retirement and exit code while keeping release `UNKNOWN`, task success null, replay disabled, and late server requests possible. The regression first failed against the old behavior, then passed. Five targeted modules passed 40 tests in normal and optimized Python. Full `runtime/cli_v1` discovery (421 tests) is not green: 17 errors are caused by absent package paths referenced by existing tests (including `runtime.host_v1`, `runtime.distribution_v2`, `runtime.backends.win32_v1`, and `research.live_control`); five tests were skipped. This repair does not establish physical input release, application effect, live X-server scheduling, or MAP01. WSLc was not inspected or used because #7924 still has no ownership release. Next: review and integrate this narrow repair if repository protection permits; separately restore/resolve the package-path gaps before claiming the broader CLI suite passes.

**2026-10-19 r43 — current membership and X11 ordering boundary:** PR #9055 is merged at `60ba70e5c1b678c56a9da45503cebbfe8c4d9d5f`. A fresh paginated CLI comparison at 2026-10-18 18:42:55 UTC found 1,675 open Issues and 514 open PRs, with both ID sets unchanged from r15; [r19](maintenance/repository-inventory-20261019-r19.md) reuses the immutable r15 metadata. For the #17 server-side queue-drain question, the [X11 protocol specification](https://www.x.org/archive/current/doc/xproto/x11protocol.pdf) guarantees per-connection delivery order while allowing the global serial order to be any shuffle of client streams; [X.Org's XTEST reference](https://www.x.org/releases/X11R7.5/doc/man/man3/XTestFakeKeyEvent.3.html) states a delayed fake event prevents further requests from that client being processed until its event completes. Therefore `XSync` on a separate cleanup client is not itself a cross-client fence. These references do not establish whether a given X server's XRes client-disappearance observation implies every previously buffered request has completed; the protocol does not state that equivalence. This Windows host has no discoverable Xvfb/Xorg/VcXsrv and no `DISPLAY`, so no live-server test ran. #7924 remains STOP/HOLD; no WSLc/Docker call was made. Next useful discriminator is a controlled two-client live X-server test that delays an owner XTEST request, retires its process, observes XRes disappearance, performs independent cleanup, and checks that no queued late input follows. Preserve release as UNKNOWN until that ordering is measured on an eligible server/allocation.

**2026-10-19 r44 — pinned Xorg teardown source crosswalk:** Read-only inspection of upstream `xorg/xserver` commit `0780950beed54305782aff6da81adffb8b628a3c` found that [`ProcXTestFakeInput`](https://gitlab.freedesktop.org/xorg/xserver/-/blob/0780950beed54305782aff6da81adffb8b628a3c/Xext/xtest.c#L379) uses [`ClientSleepUntil`](https://gitlab.freedesktop.org/xorg/xserver/-/blob/0780950beed54305782aff6da81adffb8b628a3c/Xext/sleepuntil.c#L73) for delayed events; that helper stores a per-client resource and ignores the client; teardown in [`CloseDownClient`](https://gitlab.freedesktop.org/xorg/xserver/-/blob/0780950beed54305782aff6da81adffb8b628a3c/dix/dispatch.c#L3521) marks `clientGone`, closes the connection, frees client resources, and removes it from `clients[]`; [`AttendClient`](https://gitlab.freedesktop.org/xorg/xserver/-/blob/0780950beed54305782aff6da81adffb8b628a3c/os/connection.c#L925) explicitly drops requests for a gone client; and XRes [`ProcXResQueryClients`](https://gitlab.freedesktop.org/xorg/xserver/-/blob/0780950beed54305782aff6da81adffb8b628a3c/Xext/xres.c#L217) enumerates `clients[]`. This is source-level evidence that this Xorg revision cancels a delayed, not-yet-executed XTEST request during teardown before a later XRes query can omit the client. It gives a concrete hypothesis for an Xorg-specific disconnect fence, and also shows that #9047's injected post-disconnect DOWN is an adversarial policy model rather than an observed Xorg sequence. It does not prove behavior for the target server/version, hardware delivery, all in-flight request paths, or a bounded physical release; no X server is installed or running here. Next: run the two-client delayed-request/retirement/readback discriminator on the actual eligible server and retain its version, timing, and late-event trace before changing release status.

**2026-10-19 r45 — current open-set refresh and PR delta:** A fresh paginated `gh issue list` / `gh pr list` comparison at origin/main `c2eae1a5aac951eb3560f6d6774fe23ce4fc7128` returned 1,675 open Issues and 515 open PRs. All Issue IDs and all 514 PR IDs in r15 remain; PR #9057 is the sole addition. The dated [r20 membership note](maintenance/repository-inventory-20261019-r20.md) records the capture method and boundary. #9057 is still an open X11 ordering experiment PR; its X11 integration workflow failed at head `632f7ff737d88090460d503bb5836088bd7a8812`, while its other listed checks passed. This census does not disposition that PR or prove active ownership across the repository. No Issue was closed, no PR was merged, and no branch/workspace was removed in this inventory pass. Next: continue bounded semantic review by research family, and review exact PR heads only when their ownership, unique evidence, and local verification are established.

**2026-10-19 r46 — #17 Xvfb failure evidence retained:** Copied the failed [PR #9057 private-Xvfb run packet](../research/integration/xorg_xres_disconnect_order_20261019/README.md) into the repository with its artifact hash. Run 39156382299 on X.Org Xvfb release `12101011` still reported the owner XRes client at ~1.0 s and ~5.0 s after termination; the five-second expected-disconnect bound failed. The test's final cleanup KeyRelease+XSync read both keys up, but post-delay state was not observed. This is one bounded adverse run, not a general Xorg teardown result or a release fence. Issue #17 remains open / UNKNOWN, and no WSLc allocation was used. The owning [PR #9057](https://github.com/Unjuno/agent-interface/pull/9057) remains open with its failing X11 integration check; preserve its current head and record a new discriminator on that branch rather than treating failure as task completion.

**2026-10-19 r47 — #17 second Xvfb run retained:** Preserved CI run [39157339388](https://github.com/Unjuno/agent-interface/actions/runs/39157339388) at PR #9057 head `85dfeae0bfcb398f05c4b519ce515a29c4254038` as a separate raw packet in the existing [family record](../research/integration/xorg_xres_disconnect_order_20261019/README.md). With an 8,000 ms delayed XTEST request, XRes still reported `still_connected` at ~1.0 s, ~5.0 s, and ~9.5 s after owner kill; independent KeyRelease+XSync read both keys up, and they remained up after the delay horizon. The candidate late-press assertion failed. This does not sample after XRes disappearance and cannot determine post-disconnect request behavior. It is a distinct negative bounded result, not cleanup-fence evidence or a general teardown conclusion. Keep PR #9057 open for a corrected discriminator, Issue #17 open, and release `UNKNOWN`; no WSLc allocation was used.

**「クリーン」の完了条件:**

1. 現在の全open IssueとPRのID集合をページング済み一覧で固定し、追加・消失を説明する。各項目に `active / queued / deferred / duplicate-successor / completed / rejected-with-evidence / untriaged` のいずれかを明示する。意味を読んでいないものは `untriaged` と書き、完了扱いにはしない。
2. 各研究アイデアは、出典Issue、独立した仮説、既存のPASS/FAIL/STOPとraw、証拠の限界、依存、次の判別可能な実験または保留理由を一つの検索可能な入口から辿れる。原Issueの固有問いを削らず、未検証の着想を保管だけの理由で閉じない。
3. 各open PRは最新head SHA、差分、テスト/実験、固有証拠、実際の作業者・ブランチ利用状況、base/stack依存を確認して処置する。merge、後継への移管、close、保留を区別し、古さ・draft・空のassignee/reviewer欄だけで決めない。
4. 追跡対象branch/worktreeは所有者と利用中のPR/Issueを照合する。自分が所有し保全済みで不要と確認したrefだけ回収し、所有者不明・変更未保全・他PR依存は残して所在を記録する。
5. 共有入口とリンク検査を通し、新しいworkerが割当を捏造せず、アイデアから現在の証拠・競合境界・一つの次の仕事を選べる。未解決の研究はクリーンさのために削除せず、明示した状態で残す。

6. 実行workspaceもリポジトリ内のbranchとは別の台帳で扱う。未追跡ディレクトリを「不要」と推定せず、owner/session、対応するIssue/PR、唯一のrawや出力、再生成可否、保全先の各欄を `known / unknown / verified` で埋める。`unknown` は保持・隔離対象で、削除対象ではない。

**実行順:**

| 段階 | 作業 | 出力・完了条件 |
|---|---|---|
| A. 基準点更新 | main SHAを記録し、全open Issue/PR一覧をページング取得。ID集合、件数、取得時刻、CSV hash、前回との差分を残す。 | **r13完了**。r12からID集合・CSVは不変、mainは`7c3a746`。件数だけの確認と意味仕分けを分離する。 |
| B. アイデアの地図 | 既存の`IDEAS_AND_OUTCOMES`、idea index、research map、#3/#5/#8、テーマ別agendaを重複と欠落の両面で照合。研究ファミリーごとに独立仮説・結果・残差・次テストを結ぶ。 | canonical idea entryと出典Issueへの相互リンク。アイデアは結果が出るまで残す。 |
| C. Issue disposition | Bのファミリー単位で本文・必要なコメント・後継・実装・結果を確認し、Issue自身の範囲で状態を選ぶ。 | 理由と証拠を添えた追跡可能な状態。close時は保存先、科学的状態、残る問い、実行先を記録。 |
| D. PR統合 | PRをファミリー単位でcurrent mainとの差分とhead固定で比較し、依存stackと作業者を確認。ローカルテストと固有証拠を評価する。 | merge/close/保留それぞれの根拠、解消した重複、保全した唯一成果。main統合とIssue closeを混同しない。 |
| E. refと導線 | Issue/PR/commit/worktree/rawの参照を照合し、保全receipt後に自分の不要refだけを回収。README/quickstart/current goal/work mapを短い入口に整合させる。 | 競合しない作業選択、復元可能なref記録、リンク・索引検査結果。 |

**ワーカー分担:** 大きな全件処理を一人に割り当てず、研究ファミリーまたは番号範囲と出力先を小さく区切る。着手前に対象Issue/PR、編集するファイル、読む証拠を記録し、共有indexは一度に一人が統合する。ほかの人の担当・実験・branchは、確認できないときに無主物と扱わない。調整待ちの間も別ファミリーの読取監査・テスト・分類を進める。

**歴史的なr9の#9039確認:** r9時点ではDraft/openだった[PR #9039](https://github.com/Unjuno/agent-interface/pull/9039)は、head `c6e63f483d81db229f1082006c0dfdc2da726165`から2026-10-18 16:46:31 UTCにmerge commit `5e30a60c179ce56e73c83d0279b6698862709c8f`としてmainへ統合された。r12ではopen PR集合から消えたことを確認した。これは#17のinput-release familyに属し、owned guarded-MCP process、Fake X queued-DOWN反例、XRes観測helperを含む。統合はその限定範囲の証拠であり、live X/Xvfbでの一般保証、標準caller release fence、独立task effect、MAP01を完了した意味ではない。後続のXvfb結果・作業treeのcustodyは当該authorの記録と現物を別途確認する。歴史的な`keep open`判断を現在状態として再利用しない。

**2026-10-19 r27 — first semantic disposition batch (#8681 cleanup identity):** The family record [`cleanup-identity-audit`](ideas/cleanup-identity-audit.md) reconciles the issue's original hypothesis and A01 counterexample with merged implementation PR #8771 and the still-open evidence PRs #8687/#8838. #8681 was closed as completed after a bounded issue review and explanatory comment; this does not close live-control Issue #59. Keep #8687 and #8838 open while their distinct A02–A07 packages lack a verified canonical custody destination. Do not merge their overlapping implementation changes or delete their refs. Source review used current main `4e36e47a690621a658515b5107cce020dfe6df82`, #8771 implementation head `8af95598a2517088203be2696b043ef329ba5b5c`, and current evidence-PR heads recorded in the idea entry. No experiment was rerun.

**2026-10-19 r28 — refreshed open-set baseline:** After #8681 closed, paginated `gh issue list` / `gh pr list` reads at 2026-10-18 16:15:56 UTC contain 1,675 Issues and 516 PRs. Compared with r9, Issue ID set difference is exactly `removed #8681`; PR ID set difference is exactly `added #9040`. The #9040 entry is this consolidation plan's open Draft PR. Current main remained `4e36e47a690621a658515b5107cce020dfe6df82`. CSV hashes and metadata are in [r10 inventory](maintenance/repository-inventory-20261019-r10.md). This is a fresh membership snapshot, not a semantic review of the remaining inventory.

**2026-10-19 r29 — post-merge baseline:** After #9040 merged as `848b417e56c9b024f0717d8149f8d2be5e49ac40`, a fresh paginated read at 2026-10-18 16:18:30 UTC contained 1,675 Issues and 515 PRs. Compared with r10, Issue IDs were unchanged and #9040 was the only removed PR ID. The complete [r11 inventory](maintenance/repository-inventory-20261019-r11.md) is the new point-in-time baseline; it is still metadata, not an all-issue semantic audit.

**2026-10-19 r31 — evidence-admission family:** #5305's main-tree family entry and source Issue were rechecked; #5314 and #5339 were then reconciled against their current Issue bodies/comments and merged evidence packages #5402/#5418/#5347. The new [evidence-admission family](ideas/evidence-admission-family.md) links dependency independence, conflict representation, and trust/coverage as separate stages, preserves each result and audit limitation, and gives a next evidence-custody gate. No Issue was closed, no result rerun, and no allocation was consumed. The three hypotheses remain open; the next useful step is to verify custody of #5305's held-out T1 raw before selecting a genuinely new held-out discriminator.

**次の具体的な整理作業:** [r15 triage queue](maintenance/open-issues-missing-research-primary-row-20261019-r15.csv)から小さく一つのfamilyを選び、現行Issue本文・必要コメント・PR head/diff・raw・担当状態を照合する。family entryを加筆し、結果と限界、依存、次の判別テストまたは妥当な処置を記録する。共有索引はレビュー済みfamilyだけ更新する。意味未確認は`untriaged`として残す。Issueを閉じる場合はIssue固有の完了/棄却か、未解決問いを実在する後継へ移管した根拠を記録する。整理待ちを理由に実験と統合は止めない。

**2026-10-19 r32 — current-main baseline and disposition example:** The fresh r13 snapshot at main `7c3a746526f6e698e595550a417cfd64afd12a4f` found the same 1,675 open Issue IDs and 514 open PR IDs as r12; the serialized metadata CSVs are byte-identical. This does not advance the all-item semantic review. Issue #9004 is a useful disposition example: its frozen synthetic T0 found `NO_INCREMENTAL_AGREEMENT_VALUE`, but the separately stated common-mode error question remains untested, so retain the idea entry and leave the Issue open. Do not rerun its consumed allocation. Next work remains family-by-family semantic reconciliation, then exact-head PR review; no blanket closure or workspace deletion follows from the clean-state goal.

**2026-10-19 r30 — live baseline and idea-catalog seam:** A paginated `gh issue list` / `gh pr list` read at 2026-10-18 16:55:44 UTC against main `5e30a60c179ce56e73c83d0279b6698862709c8f` returned 1,675 open Issues and 514 open PRs. Compared with r11, the Issue ID set is unchanged and PR #9039 is the only removal; the merge is confirmed at this main SHA. Metadata does not establish semantic disposition or active ownership. A `docs/ideas` number-only scan is not a complete coverage test: #5305, for example, has a row in the broader research Issue index and its T0 report on main, while its later held-out STOP and transfer refinements are only in the Issue thread. Added [a linked family entry](ideas/conflict-aware-evidence-ledger.md) preserving distinct outcomes, limits and known raw-custody gap. Do not close #5305 or rerun a consumed fixture as a cleanup action.

**2026-10-19 r26 — workspace custody pass:** A read-only scan of the current local `work` area found 190 top-level directories, 341 top-level loose files, and 8 Git-registered worktrees across the workspace. Six of the 190 directories contain `.git` metadata; 184 are non-Git artifact folders with 5,230 files / 303,118,316 bytes. These counts are local to the captured workspace, not repository contents or a deletion proposal. The [workspace custody census](maintenance/workspace-custody-census-20261019.md) records top-level metadata only. No files were moved or deleted. Next, classify artifact folders in bounded batches by provenance and canonical evidence link; preserve raw/unique results, consolidate only verified duplicates, and remove only items whose owner, active use, custody, and recovery path are all established. This layer is independent of GitHub Issue/PR disposition and the repository's eight registered Git worktrees.

**Execution rule for cleanup batches:** first connect an item to a research family or active work record, then select `retain-canonical`, `retain-history`, `merge-verified-duplicate`, `quarantine-owner-unknown`, `eligible-for-removal`, or `unreviewed`. Record evidence and a hash before changing location. A batch is done when its inventory rows have a disposition and any move is read-back verified; it is not done merely because the folder count fell. No blanket-close of Issues/PRs and no all-at-once workspace deletion.

**2026-10-18 r18 — current-main count recheck:** At 14:52 UTC, fetched
`origin/main` was `e5c5448f9ad035657f212135fa4e95d189acda95`. GitHub's paginated
Issues endpoint returned 2,190 issue-like records, including 514 pull requests;
the separately paginated pulls endpoint returned 514 open PRs, leaving 1,676
open Issues. This was a count-only refresh, not an ID-set comparison, semantic
review, ownership check, or closure decision. The latest full open-item metadata
snapshot remains r8 at 14:25 UTC against
`9ff8ab4df85c2359cf5d2055f54586c7e4fe816e`; it is now historical discovery
metadata. Updated the [worker map](WORKER_WORK_MAP.md) and [current objective
entry](CURRENT_GOAL.md) so navigation no longer labels that old SHA as current.
No Issue, PR, branch, worktree, or historical evidence was changed.

**2026-10-18 r17 — current-main family recheck:** At 14:38 UTC, GitHub `main` was `c72c9b186dac29c57ed0d63d92748bfc7ba4d971`. Fresh paginated endpoint counts were 1,676 open Issues and 514 open PRs; this was a count check, not an ID-set comparison or semantic review. The existing #59 MAP01 packet crosswalk was rechecked against this exact main: all six packet PRs remain open at their recorded heads, with no GitHub assignees, and their heads range from 478 to 857 commits behind current main. Empty assignee fields do not prove that work is released, and old heads do not justify closure. The crosswalk now records current-main distances and keeps each read-only audit scope separate. No Issue/PR state, branch, or historical packet was changed.

**2026-10-18 r16 — cleanup baseline at 14:25 UTC:** At that capture, `main` was `9ff8ab4df85c2359cf5d2055f54586c7e4fe816e`. A fresh paginated metadata snapshot had 1,676 open Issues and 514 open PRs, with no ID changes from r7; the [r8 note and CSVs](maintenance/repository-inventory-20261018-r8.md) were the discovery baseline. This is not semantic review or current ownership proof. Semantic status is established one research family at a time from current Issues, current PR heads, preserved reports, and active worktrees. The cleanup has four independent ledgers: (1) idea/hypothesis and its falsifiable remainder, (2) Issue workflow and actual successor, (3) PR code/evidence/owner custody, and (4) branch/worktree recovery. Each reviewed family must link these ledgers or state which link is unknown. Unverified ideas remain searchable; closure requires verified completion of the Issue's own scope, evidence-based rejection, or a real successor that carries the remainder. PR integration/removal requires current diff, tests, unique evidence, and ownership checks. Repository-wide cleanup is complete only when every current open Issue and PR is either family-reviewed or explicitly marked untriaged in a dated inventory, each retained idea is indexed, and each local/remote ref removed has verified custody. This is a progress criterion, not a requirement to close all Issues or to finish all research before work resumes.

**2026-10-18 r15 — #17 process-fence evidence reconciliation:** The main-tree [#7034 result](../research/concurrency/x11_requested_process_fence_17_4d74_20261003/REPORT.md) already supports requested task-process retirement in its frozen four-cell Xvfb scope: keepalive accepted cancellation before the paused child later injected F9; kill/reap before acceptance prevented that suffix, and the fixed prearmed cleanup path released F8. This result is `SCOPED_REQUESTED_PROCESS_FENCE_SUPPORTED` / `HOLD_RUNTIME_PROMOTION`; do not rerun the consumed producer. It does not integrate the owner into the standard MCP caller, prove public cleanup-scope reconstruction (the distinct #7024 allocation ended STOP/METHOD_FAIL), establish a physical release deadline, or cover an unresponsive X server. The next worker seam is process-owner integration plus independently confirmed cleanup and honest aborted-call reporting, recorded in the [safety-control agenda](ideas/safety-control-agenda.md) and [work map](WORKER_WORK_MAP.md).

**2026-10-18 r14 — #17 cancellation acknowledgement seam:** In the current-main guarded MCP caller, a blocked Fake X writer could acknowledge cancel while `review_required` remained false until its next cooperative cancellation check. The retained red/green regression and normal/optimized related-suite results are in [`cancel_ack_review_fence_mcp_20261018`](../research/integration/cancel_ack_review_fence_mcp_20261018/README.md). The bounded change sets the review fence at cancel acknowledgement. It does not retire a blocked writer, retract queued input, establish native/physical release or a deadline, or verify task effect. Treat this as one caller-family item with its original raw and limitations; keep #17 open. Next gate: single-authority writer retirement/fencing and late-send rejection through the selected caller, then separately qualify native release and task effects. This is a family update, not a semantic sweep of the open Issue/PR inventory.

2026-10-15。対象は `Unjuno/agent-interface` 全体とGitHub Issue/PR。コンピューターコントロールの研究を再び見通せる状態にする。

**2026-10-18 r11 — ユーザー確認済みの整理目的:** リポジトリを、大量のワーカーがアイデアを失わず、互いに衝突せず、個別に着手・検証・統合できる状態へ近づける。Issue/PRを一律に閉じたり、件数をゼロにしたりすることは目標にしない。まず研究上の問いごとにアイデア、出典Issue、反対仮説、既存コード/証拠、その限界、依存、次の判別可能な作業を結ぶ。結果が出ていない案は `unverified` 等で実行候補に残し、実際の重複・完了・根拠付き棄却・実在する後継への移管だけを個別の証拠に基づいて処置する。元Issueと歴史的rawは保持し、要約は索引に留める。

**2026-10-18 r12 — #17 current-main update:** PR [#9027](https://github.com/Unjuno/agent-interface/pull/9027) merged at `ce1a0e93c67fafaf4f05bf25e6b86fbe50196ecc`. The selected guarded MCP caller now requires fresh visual review after `execution_failed`, preventing reuse of a still-live alias after uncertain partial input. Its Fake X queued-press expiry case still delivers an already-queued DOWN only after the fixture resumes; cleanup is then verified in Fake X, not under permanent platform nonresponse. The focused module passes 7/7 and four related modules pass 60/60 in normal and optimized Python. The [safety-control agenda](ideas/safety-control-agenda.md) and [work map](WORKER_WORK_MAP.md) link the retained packet and exact limits. Native X behavior, physical release deadline, task effect and matched efficiency remain open; next caller seam is writer retirement/fencing and late-send rejection.

**2026-10-18 r13 — refreshed orchestration inventory:** On current main `f4cd5577ef57a01d7b25a389d877c9d1b3ab9d21`, a fresh paginated GitHub REST read at 13:50 UTC returned 1,676 open Issues (17 pages) and 514 open PRs (6 pages). Membership is unchanged from r6; zero Issue IDs and zero PR IDs entered or left. The r7 CSVs preserve current titles, timestamps, labels, assignees, and (for PRs) draft, author, head/base and head SHA: [Issues](maintenance/open-issues-20261018-r7.csv), [PRs](maintenance/open-prs-20261018-r7.csv). SHA-256: Issues `80fda3cd11f9abeb2c72ca0aa420fe055efb928ae0b319087608c4e25691680b`; PRs `7d9dc08157e03b437b9c9f09513141c32416a07afe79891dfc3cb76ce78bd1da`. This is a membership/metadata refresh, not semantic review or proof of current ownership. The model-economics first batch is no longer pending: #7521 was closed with #8772 as its named, still-open draft successor. Next, select PR batches by research family and compare exact current heads to main; do not treat age, draft state, or an empty assignee/reviewer field as disposition evidence.

今回の収束作業は、(1) main SHAとページング済みIssue/PR一覧を時刻付きで固定、(2) 仮説と証拠で一族を束ねる、(3) 既存担当・PR stack・資源競合を確認して次の仕事を小さく切る、(4) 一族ごとに必要な実験/ローカル検証と統合を進める、(5) 差分・raw・所有者の保全確認後に限り不要refを回収、の順で進める。各バッチは「何件閉じたか」ではなく、保存されたアイデアから現在の根拠と次の独立作業へ迷わず辿れるかで評価する。全件の意味仕分けを、研究を始める前提条件にしない。

**2026-10-18 r10 現在地:** 13:19 UTCのGitHub Search APIはopen Issue 1,676件・open PR 514件を返した。これは件数確認であり、全件本文・コメント・所有者の意味仕分けではない。mainの#9022は#17に関するFake X caller回帰として、選択writer内でDOWNがserver処理前に停止した後のcancel、同一call custody、解除後のcleanup UP、suffix/replay拒否を追加した。関連Issue #17、[safety-control agenda](ideas/safety-control-agenda.md)、[work map](WORKER_WORK_MAP.md)を一つの入口で結ぶ。証拠はFake X caller範囲に限り、物理deadline・writer/server非応答時のrelease・task effect・efficiencyは未達。次の有限な実装判別は、現在のselected callerでsingle-authority writer retirement/fencingとlate-send拒否を接続し、release不確実性をUNKNOWNのまま維持できるかの確認。これは全件整理の完了ではなく、独立したworkerが選べる研究一族一件の更新である。

**2026-10-18 r9 現在地:** 13:05 UTCのGitHub REST全ページ再取得でもopen Issue 1,676件・open PR 514件で、r8の件数から変化なし。これは一覧件数の再確認であり、Issue/PRの全件意味分類や担当確認ではない。入力解放・割込み一族ではmainに統合済みの#9014がFake Xの別connection UPによるfalse-clear反例を、#9015がguarded MCP callerでのblocked release-sync待ち・同一call custodyを記録する。既存の[safety-control agenda](ideas/safety-control-agenda.md)と[ideas/outcomes index](IDEAS_AND_OUTCOMES.md)へ結果と未解決境界を結び直した。物理解放期限・backend非応答時の成功・task effectは未確認で、#17はopenのままとする。

**2026-10-18 r8 現在地:** `2026-10-18 12:33:06 UTC` にGitHub REST APIを全ページ取得し、open Issue
1,676件・open PR 514件をCSV化した。SHA-256とr5からのID差分は[r6 inventory note](maintenance/repository-inventory-20261018-r6.md)、
個別の一覧は[Issue snapshot](maintenance/open-issues-20261018-r6.csv)と[PR snapshot](maintenance/open-prs-20261018-r6.csv)に保存した。
PRはr5から#9007が一件減り、Issue IDの増減はなかった。これは時点付きの一覧であり、本文の意味分類・担当確認・一括closeを意味しない。

同日12:31 UTCに[#9007](https://github.com/Unjuno/agent-interface/pull/9007)をmerge commit
`7b2d531b305e178d84ab599944758a2202cf647a`で統合した。同期後のheadで9 checksすべてsuccess。
Issue #8914に関する二つの保存済みmethod-failure結果とgzip rawを保全し、候補/監査器の再実行はしていない。
結果は`sentinel_not_reproducible` / `HOLD_AUDITOR_METHOD_FAILURE`であり、科学的な合格・失敗やIssue完了を示さないため#8914はopenのまま。

**2026-10-18 r7 現在地:** `2026-10-18 12:24 UTC` にopen Issue一覧17ページとopen PR一覧6ページを
GitHub RESTから取得し、Issue 1,676件・PR 515件を保存した。metadata snapshotのSHA-256とr4からの
ID差分は[refresh note](maintenance/repository-inventory-delta-20261018-r5.md)に記録した。
これは最新のopen-set inventoryであり、本文の全件意味分類、担当照合、Issueの一括処置を示さない。

同期後のmainは`c95caacce56925a03fb5724b6559506fcdac2050`。#9011/#9018/#9009/#9008を統合し、
PR #9008の現行V39 pair-watermark回帰と43件のSHA manifestを確認した。PR #9009の保存T0結果は
mainへ入り、Issue #9004は`NO_INCREMENTAL_AGREEMENT_VALUE`を残すためopenのまま。#59も
ライブゲーム・入力・効果の証拠がないためopenのままで、いずれもIssue全体の完了とは扱わない。

**2026-10-18 r5 現在地:** `2026-10-18 11:47 UTC` のGitHub Search API `total_count` は
open Issue 1,676件、open PR 519件。これは最新件数の照合であり、全件ページ取得・内容判定・
担当判定ではない。過去のCSVは各取得時点の履歴として保ち、現在の完了数には流用しない。

**2026-10-18 r6 現在地:** `2026-10-18 12:10 UTC` にGitHub RESTのopen Issue endpointを22ページ、
open PR endpointを6ページ取得して再集計した。Issueは1,676件、PRは517件。件数は全件本文の
意味判定や担当確認の完了を意味しない。

**2026-10-18 r6 統合記録:** mainは`5dc27cff7ffed6fb218719ddc53b95a901e03d0c`。
整理計画・アイデア台帳・履歴保全を含む[#9012](https://github.com/Unjuno/agent-interface/pull/9012)
に続き、guarded relayのpackage source pinningと回帰テストを含む
[#9011](https://github.com/Unjuno/agent-interface/pull/9011)を12:07 UTCにmerge commit
`5dc27cff7ffed6fb218719ddc53b95a901e03d0c`で統合した。#9011の14 checksはhead
`62b3d1632e7b2ddd0ec2ecbec957d0a51e16a833`上ですべてsuccess。手元にPython 3.12がなく、
対象の`research/live_control`全体を展開すると大容量の保存rawまで含まれるため、今回の環境では
同じローカル再実行を完了できていない。テスト成功の根拠は当該headのGitHub checksであり、
新しいheadでの再実行やライブGUI/model効果の証拠とは扱わない。

同日、統合済み#9011のsource branchは、merge状態とhead SHAを確認し、open PRのhead/baseに
使われていないことを確認した後にremoteから削除した。整理PR #9017のリンク欠落指摘は
sparse-checkoutの未展開パスを現行treeにないと誤認したもの
だったため取り下げ、実tree上で確認し直した記録を#9012に統合した。誤った指摘は監査結果として
再利用しない。全件の意味分類・PR処置は継続中である。

整理用PR [#9012](https://github.com/Unjuno/agent-interface/pull/9012) は元head
`a8cb43d9179fcef27c77170941de3b38b2a2ac41`、base
`13e0b1c1b622085e0007e3ee52a744d1f2b32977`で、当時mainだった
`befe2de22743cfe4a77f513a2876d204f5cf48d5`との比較でmerge conflict状態だった。
同期候補では`docs/REPOSITORY_CONSOLIDATION.md`、`docs/ideas/README.md`、
`docs/ideas/safety-control-agenda.md`の3競合を、両側の追記内容を保つ形で解消した。
同期候補のGit tree上で計画文書の相対リンク23件は全件解決し、生成済み分析indexは
対象848ディレクトリを順序・一意性・欠落なしで列挙した。
現行mainのリンク14件も全件解決している。Fake X A01の保存監査テストは通常/-Oの各4件が通過。
通常のfilesystem index checkerも起動したが、sparse checkoutでは「stale」と表示した後に
兄弟ディレクトリの欠落判定を省略するため、統合候補に対する完全な検証にはならなかった。
候補headの新しいhosted checksも未実行。
同期候補の検証後にPR headを更新し、履歴保全を維持したまま統合可否を再判定する。

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

**2026-10-18 r4：** 目的はIssue/PRをゼロにすることではなく、研究アイデア・実装・証拠・担当中の仕事の関係を保ったまま、各ワーカーが安全に独立した次の作業を選び、結果を統合できる状態にすること。過去の全件スナップショットは取得時点の資料として扱い、現在数や全件判定の証拠に流用しない。以下の手順で一族ずつ整理し、科学的な問いを閉じる判断とGitHub上の作業状態を分ける。

**2026-10-18の実行記録：** モデル経済性一族で#7521/#8772の現在のPR差分を再確認した。
実装と回帰テストを引き継いだ#8772を後継として残し、重複する#7521はその理由・未解決条件を
コメントして閉じた。#8772はdraft/openでcurrent mainへの追随・再検証が未完、親#57もopen。
実施したのは一族内の重複一件の収束であり、PR全体やIssue全体の整理完了ではない。

## r4 実行計画：アイデアから成果・統合まで

「クリーン」は空のIssue一覧や差分のない作業ツリーではなく、研究の行き先と未解決点が明確で、保存・統合・削除の判断を追跡できる状態と定義する。実行単位は全件一括ではなく、同じ研究上の問いを扱うIssue/PRの一族とする。

| 段階 | 作業 | 残す成果・通過条件 |
|---|---|---|
| 0. 現在地の固定 | mainの基準SHA、最新のIssue/PR一覧、既存worktree/branch、作業中の所有者、無視対象の証拠を時点付きで取得する。古い一覧やassignee欄を現在の割当とみなさない。 | 取得条件とhash付きsnapshot。既存の未コミット変更・原rawを変更しない。 |
| 1. 問いごとの整理 | Issue本文・必要なコメント・関連PR・現行実装/結果を読んで、重複タイトルではなく仮説と判別対象で束ねる。各アイデアに出典、独自仮説、反例、証拠と限界、依存、次の有限な実験、結果による判断、実行先を記録する。 | `docs/ideas/`のテーマ別agendaとIssueへのリンク。保存しただけの案は`unverified`等で残し、研究対象から落とさない。 |
| 2. Issueの状態判断 | Issueを「実行中」「次の検証待ち」「証拠不足/所在調査」「結果あり・親問い未達」「根拠付き棄却」「実行先へ移管」に分ける。完了した作業と上位研究の完了を別に扱う。 | 完了・棄却・実在する後継への移管を確認した場合だけcloseする。後継には残る仮説と次の作業を実際に引き継ぎ、単なる文書保存や古さをclose理由にしない。 |
| 3. PRごとの統合判断 | 各open PRを現在のmerge-baseから比較し、固有差分、mainとの競合、テスト、raw/evidence、依存PR、作者/作業中の所有状態を確認する。stackのmergeとmain統合を区別する。 | 「局所検証後に統合」「修理して継続」「固有部分を移管・保全して終了」「根拠を残して棄却」「所有・証拠確認待ち」のいずれかと、正確なhead/継続先を記録する。重複コードでも独自研究結果は別に保全する。 |
| 4. branch/worktreeの回収 | Issue/PR状態だけで削除せず、現在のtip、追跡外・ignoredファイル、未push commit、原raw、所有者、利用中プロセスを照合する。 | 変更・証拠の保存先と一致を確かめ、使用者がなく、再開先が明示された自分のrefだけを回収する。不明な所有物は一覧化して残す。 |
| 5. 並列作業の入口を整える | work mapに互いに衝突しない有限な作業範囲、根拠、出力先、競合境界を置く。共有GUI/実験資源の排他は実在する取得機構または有効な引継ぎだけで扱う。 | ワーカーが全Issueの精読や中央管理者の応答待ちなしに作業を始められる。実際の保護設定を超える必須レビュアー数・投票・全員待ち・新しいロックを追加しない。 |

### 一族バッチの標準レコード

整理する一族ごとに、次を短く残す。Issue本文やコメントをagendaへ丸ごと複製せず、原記録へのリンクを保つ。

1. **問いと価値**：解決したいコンピューターコントロール上の失敗と、別の問いとして残す理由。
2. **仮説・対立仮説**：何が変われば成功か、単純な代替説明や反例は何か。
3. **既存成果**：mainに統合済みのコード、候補実装、保存結果、ライブ結果を区別し、source SHA・環境・監査・rawを辿れるようにする。
4. **残差と依存**：未達の性質、必要な資源/権限/別チーム依存、判別できない条件。
5. **次の一手**：有限なテスト/実験、比較対象、事前の合否/HOLD、結果で変える判断、担当中ならその実在する所在。
6. **Issue/PR処置**：open継続、実装統合、移管、棄却、closeの根拠。閉じる場合は残る問いと次の実行先も記録。

### 優先順位と最初のバッチ

一族の順番は、(a)主要ゴールへの寄与、(b)既存成果の再利用可能性、(c)最小の作業で仮説を判別できる度合い、(d)依存・実行可能性、(e)大量ワーカー間の競合を減らす効果で決める。古さ、Issue/PR数、レビュー待ち件数は優先度や棄却理由にしない。

最初のモデル連携・比較評価バッチは実施済みである。PR #7521を、未解決の実装・評価を引き継いだopen draft #8772へ理由を記録して移管した。親Issue #57と#8772は未完了として残る。次は最新一覧から一つのPR/Issue familyを選び、本文・必要なコメント・正確なhead差分・証拠・担当中の作業を照合して、処置または次の独立作業を決める。直近のr7一覧は候補発見用であり、全件本文確認済みとは扱わない。既存成果がある一族も、親Issueの問い全体が達成したとは推定しない。

### 全体完了の判定

- 最新時点のopen Issue/PR一覧に対し、**未評価・評価中・処置済み**の件数と取得時刻が一致し、未評価を未評価と表示している。
- 全ての処置済み研究アイデアから、出典、証拠、残る問い、次の実行先または棄却根拠へ辿れる。
- 処置済みPRから、mainに入った変更または証拠の保全先、正確なhead、ローカル検証と限界が辿れる。未解決PRの理由も具体的である。
- 消したbranch/worktreeに未保全の差分・raw・所有権が残らない。確認できないものは削除せず記録する。
- work mapに独立した開始可能な仕事があり、架空の人手ゲートや一つの巨大Issueへの集約でワーカーを停止させない。

この判定は研究ゴール達成や全アイデアの実験完了とは別であり、未達の仮説は整理後も実行対象として残す。

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
| 入口とオーケストレーション | README→現行ゴール→work mapから、対象範囲・既存Issue・現行成果・未達・次の有限な仕事へ辿れる。古い割当や必須レビュー人数を新しい開始条件にしない。 | #9027/#9028の結果を現行mainで照合済み。r7 inventoryを追加。次は各themeの次の独立仕事と衝突範囲を定期的にmain基準で更新する。 |
| 研究アイデアとIssue | 各テーマの独自仮説、反例、出典、依存、既存成果、最小検証、実行先が結ばれる。保存しただけの未達は未達と分かる。 | 視覚・安全制御・モデル比較などの既存agendaを維持。未評価を明示しつつ、work mapのtheme単位で本文/コメントを読み、独自の残差を検証へつなぐ。全件を一つの親Issueへコピーしない。 |
| PR | 全open PRに、採用候補・修理・証拠保全・後継へ移管・根拠付き棄却の処置がある。統合/終了の正確なheadと継続先を辿れる。 | r7の514件から一族ずつ意味仕分けする。最初の現行例は#59のMAP01 six-packet family crosswalk。各packet監査後、exact head・固有raw・所有・current-main差分を確認し、そのpacket単位で継続/統合/移管/終了を判断する。 |
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

既存の`docs/IDEAS_AND_OUTCOMES.md`、`docs/RESEARCH_MAP.md`、`docs/RESEARCH_ISSUE_INDEX.md`、`RESEARCH.md`を入口として、次のテーマに研究項目をまとめる。

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

**2026-10-17 catalog branch integration:** The #9012 branch now incorporates #9005 head `880c6b63036fa297d4a5c0a68498edf94e1b48d4`. The shared indexes were resolved by retaining disjoint issue rows, selecting the fuller #59 evidence summary, combining the complementary #6468/#6284/#5521 outcomes, and removing repeated rows and page links. Local audit found 525 primary Issue rows with no duplicate IDs, 122 distinct idea-page links, and 283 resolving relative links; the research index check passed with 845 retained result/failure directories. This is a reviewable PR-branch integration, not a merge to `main`; hosted checks and review remain outstanding.

**2026-10-19 r35 — refreshed idea-index coverage:** At main `6c5e5df2909de10cdf12f442015160199f3d661b`, the open set remained 1,675 Issues and 514 PRs, with both ID sets unchanged from r14. The historical primary table in `RESEARCH_ISSUE_INDEX.md` has 1,729 rows; 1,184 of the current open Issues occur there, while 491 do not. Of those 491, 220 have an exact Issue URL in an individual `docs/ideas` family file and 271 are referenced only in the summary idea indexes. The [coverage audit](maintenance/idea-index-coverage-20261019-r15.md) explains the parser boundary, and the [491-row queue](maintenance/open-issues-missing-research-primary-row-20261019-r15.csv) marks every row untriaged. These are navigation measurements, not semantic dispositions. No Issue or PR was closed or merged and no evidence was rewritten. Next, review a coherent family from the queue against current source evidence, then update its canonical family note and shared indexes.

**2026-10-19 r48 — #17 observation-only Xvfb run retained:** The test at PR #9057 head `4ffa711d6bf4a5e60f18109dc779ed753eff4f88` now treats either measured keymap as a valid outcome; the report records whether a late input appeared without making that hypothesis a pass condition. Dedicated run [39157580185](https://github.com/Unjuno/agent-interface/actions/runs/39157580185) passed and measured the 8,000 ms horizon: XRes remained `still_connected` in all probes through ~9.5 s after owner kill, both keys remained up after independent cleanup and at the horizon, and `late_input_observed=false`. The separate raw packet is in the [family record](../research/integration/xorg_xres_disconnect_order_20261019/README.md). This is a valid bounded negative observation, not a post-disconnect sample, release fence, standard-caller validation, or general Xorg result. Keep PR #9057 open pending its complete check set, Issue #17 open, and release `UNKNOWN`; no WSLc allocation was used.

**2026-10-19 r49 — #9057 integrated with scoped result:** PR #9057 squash-merged as `6d91411cf8b90d514ac0d05a68009e6667113d7e` after all ten reported checks passed, including its observation-only private-Xvfb job. The family packet preserves the prior failed late-press assertion run and the later passing observation run as separate raw. Neither observed XRes disappearance; both keys remained up in the bounded horizon. This integrates a measurement harness only. Keep Issue #17 open and release `UNKNOWN`; no WSLc allocation, standard-caller proof, post-disconnect ordering, task effect, or physical deadline is established.

**2026-10-19 r50 — post-integration membership recheck:** At main `baec61784825f2fa841a63b07df017ab238fc74d`, paginated GitHub reads at `2026-10-18 19:18:20 UTC` found 1,675 open Issues and 514 open PRs. Both complete ID sets are identical to r15; the [r21 membership note](maintenance/repository-inventory-20261019-r21.md) records count, method, main SHA, and sorted-ID hashes. #9057 and #9060 entered and left the open-PR set between snapshots. This does not update full metadata, semantically classify each item, or verify worktree owners. No Issue was closed.

**2026-10-19 r51 — #17 extended Xvfb horizon retained:** Merged [PR #9062](https://github.com/Unjuno/agent-interface/pull/9062) adds a bounded 10 s XRes poll after the 8 s delayed-event horizon. CI run [39158398302](https://github.com/Unjuno/agent-interface/actions/runs/39158398302) still reported `still_connected` 18,511.3 ms after owner termination; the extended keymap remained up and no disconnect was observed. The [family packet](../research/integration/xorg_xres_disconnect_order_20261019/README.md) preserves raw/hash. This narrows the observation window, not the post-disconnect safety claim. Keep #17 open, release `UNKNOWN`, and do not infer physical release or WSLc status.

**2026-10-19 r52 — repository-cleanup plan aligned to current main:** The local `main` checkout is clean at `c58cea752834a8998764abb655d6173e204d4e98`, and `origin/main` resolves to the same SHA. The checkout has sparse mode enabled; several nested evidence/idea paths are omitted locally even though they exist in the Git tree. Therefore absence from this worktree is not a missing-file or deletion finding. A fresh paginated GitHub CLI read at 2026-10-18 20:58:22 UTC returned 1,675 open Issues and 514 open PRs; sorted ID hashes match the prior r23 membership snapshot. The new [r24 check](maintenance/repository-inventory-20261019-r24.md) records the current main SHA and this scope. The five direction Issues #5/#17/#57/#59/#2789 were individually confirmed open; no Issue/PR status or branch/worktree was changed. The plan above now makes the cleanup sequence explicit: fix the navigation baseline, classify idea families without merging hypotheses, disposition Issues by evidence, review PRs by exact diff and custody, then recover only verified-unused workspaces. The finite next step is to take one disjoint family from the frozen discovery queue and record its live status, evidence links, unresolved question and next test; no global close or bulk file movement is authorized by a clean-state goal.

**2026-10-19 r53 — blocked release-helper recovery composed through standard MCP:** PR [#9077](https://github.com/Unjuno/agent-interface/pull/9077) squash-merged as `9bfacb2a388f549e64ff0a62b25e0738691bb4bc`. The added Fake X standard-caller regression blocks owner I/O after a key-down obligation is published, supplies a controlled `disconnected` fixture result, and runs a separate synthetic release worker that blocks under the real process supervisor. The caller returns under the test's 3 s bound with helper `supervision_timeout`, retired helper, release `UNKNOWN`, no task success, and replay disabled. The owned-process, transport-cancellation, and XRes supervisor suites pass 42/42 in normal Python 3.12.14 and 42/42 under `-O`. [Issue #17 comment](https://github.com/Unjuno/agent-interface/issues/17#issuecomment-6255142547) preserves the result and limits. This advances bounded local recovery only; XRes is controlled, and it proves no live server disconnection, physical release, physical deadline, queue drainage, MAP01 completion or independent task effect. #17 remains open and release remains `UNKNOWN`. A paginated membership check at approximately 2026-10-18 21:06 UTC found 1,675 open Issues and 514 open PRs at this SHA; both ID hashes match r24. The merge occurred between those snapshots, so #9077 is absent from both open-PR sets. See [r25](maintenance/repository-inventory-20261019-r25.md).

**2026-10-19 r54 — consolidation entry points refreshed after #9078:** PR [#9078](https://github.com/Unjuno/agent-interface/pull/9078) merged at `48acb8a6aa56c763d08fa31c63be58d47a63f7de`. A follow-up paginated GitHub CLI read at approximately 2026-10-18 21:10 UTC returned 1,675 open Issues and 514 open PRs; both sorted-ID sets and hashes match r25. The new [r26 membership record](maintenance/repository-inventory-20261019-r26.md) is linked from `CURRENT_GOAL.md` and `WORKER_WORK_MAP.md`, whose baseline now matches this main SHA. This is a freshness/navigation update only: it does not semantically classify the 491 historical primary-row gaps, change any Issue/PR state, or establish PR readiness or worktree custody. The next convergence work remains family-by-family review with evidence and ownership checks, not bulk closure or artifact deletion.

**2026-10-19 r55 — #8860 audited, integrated, and indexed:** After the documentation baseline refresh [#9079](https://github.com/Unjuno/agent-interface/pull/9079) merged, PR [#8860](https://github.com/Unjuno/agent-interface/pull/8860) merged at `44665b08c1cdff3a5b49e6c7a3cfa3394c174262` after its frozen raw/result packet passed the required replay-gate and an independent local post-run audit. The local auditor verified the manifest, frozen sources and inputs, decoded RGB digests, captured event rows, transcript/result equality, authority boundary and run receipt; both immutable post-run tests passed. The saved result supports only a narrow construction boundary: distinct adjacent frames with unchanged typed health/ammo preserve a pending answer through the selected monitor/admission path; no executor/input authority was granted. No WSLc allocation was rerun. The result and limits are indexed under scoped visual invalidation in [IDEAS_AND_OUTCOMES.md](IDEAS_AND_OUTCOMES.md); parent Issue #59 remains open, with live threat semantics, independent effect, recovery and MAP01 success unresolved. The [r27 membership record](maintenance/repository-inventory-20261019-r27.md) records 1,675 open Issues and 513 open PRs after the merge.

**2026-10-19 r56 — #8863 composition audited, integrated, and classified:** PR [#8863](https://github.com/Unjuno/agent-interface/pull/8863) merged at `09a064739895f6bbcdd14210dd492f8804d98f99`. Its required replay-gate passed; the formal workflow was skipped. An independent local audit verified frozen source blobs, candidate/auditor hashes, raw stdout/stderr, paired outcomes, cancel/release order and the explicit authority limits; the single composition test passed. The preserved result distinguishes soft ammo 8→4 (pending answer/fire key remain active under the authored cover contract) from hard 8→0 (monitor invalidates, Executor cancellation precedes planner interruption, owner receipt verifies empty). The synthetic immediate-action threshold 5 is only a contrast and does not govern the existing cover. WSLc reported swap-cgroup limits unavailable, so requested memory is not claimed as enforced. No live game/model/input, task effect, or MAP01 result is established; no WSLc allocation was rerun. Both this result and #8860 are separately indexed in `IDEAS_AND_OUTCOMES.md`; #59 remains open. The [r28 membership record](maintenance/repository-inventory-20261019-r28.md) records 1,675 open Issues and 512 open PRs.

**2026-10-19 r57 — keep membership snapshots separate from content baselines:** A fresh paginated read at main `958cf28e32a153d14badd4826370088e73ffff19` again found 1,675 open Issues and 512 open PRs with the same ID-set hashes as r28. [r29](maintenance/repository-inventory-20261019-r29.md) records this snapshot after documentation-only PR #9081, so the current-goal and worker-map pages now name a dated, reproducible membership read instead of implying that their pinned SHA must always equal a later documentation commit. The 491 historical research-index gaps remain discovery work, not untriaged evidence of non-research or grounds for bulk closure.

**2026-10-19 r58 — #8847 A08–A13 owner-close packet integrated with scoped A13 result:** PR [#8847](https://github.com/Unjuno/agent-interface/pull/8847) merged at `d8937346a331c0c69c4b8668efc9423e79725b24`. Its replay-gate passed; the formal workflow was skipped. Independent verification checked all 67 files across six `SHA256SUMS` manifests and reran only the A13 raw-only auditor against the frozen candidate, raw and freeze; A13 returned `PASS_METHOD_SCOPED`. The chain remains explicit: A08/A09/A10/A12 STOP, A11 NOT RUN, A13 one-key synthetic Xvfb close with KeyPress/KeyRelease, observed key-up, verified empty terminal owner receipt, stopped thread and Xvfb exit 0. No WSLc allocation was rerun. This does not establish physical release, app consumption, a general deadline, recovery or MAP01 success. The [idea index](IDEAS_AND_OUTCOMES.md) preserves the separate result under open Issue #59, and [r30](maintenance/repository-inventory-20261019-r30.md) records 1,675 open Issues and 511 open PRs.

**2026-10-19 r59 — #8790 public-packet custody recheck; retain unmerged:** PR [#8790](https://github.com/Unjuno/agent-interface/pull/8790) remains open at its recorded head. The public A13 summary supports the reported timing HOLD and right-censored recovery, but `A13_RESULT.md` places the full event stream/images and `A13_TREATMENT_AUDIT.json` under a `results-local` allocation directory absent from both the PR diff and this checkout. Public JSON's `independent_audit_pass` boolean is not a substitute for hash-bound raw/audit receipt. The review thread's final correction says the earlier `key_state_errors` false-acceptance concern used an impossible source-conforming receipt and is not evidence that a retained cancellation was misclassified; the actual raw rows remain unavailable for independent reconstruction. Keep A12 STOP, A13 HOLD, and the PR unmerged pending owner-attested custody or equivalent reproducible evidence. Do not rerun either consumed allocation. This scoped absence finding does not establish global raw loss and changes no Issue state.

**2026-10-19 r60 — #8759 A10 public STOP retained; raw custody remains unverified:** The open Draft PR [#8759](https://github.com/Unjuno/agent-interface/pull/8759) publishes an A10 STOP summary and a later cancellation reconciliation, while retaining the original audit FAIL. The public report states 13/13 cancellations are accounted after reconciliation and records zero hard-health exposures/useful events during pending inference; the episode ended in death without a MAP01 exit. The exact execution freeze, first audit and raw/manifest are explicitly local-only, and the exact `results-local` directory is absent from this checkout. Merged [#8763](https://github.com/Unjuno/agent-interface/pull/8763) repairs the controller cleanup receipt but does not alter the historical A10 outcome. Preserve STOP/FAIL, do not rerun, and keep the draft unmerged until exact raw/freeze/audit custody can be verified. No Issue state changed.

**2026-10-19 r61 — #8782 A11 public HOLD preserved; execution custody not independently available:** The open PR [#8782](https://github.com/Unjuno/agent-interface/pull/8782) reports one 32-decision episode (2 kills, no deaths, no MAP01 exit), with no hard-health guard, useful scorer feedback during inference, or bounded recovery. Its public reconciliation reports 32/32 cancellations accounted (six token-bound owner releases and 26 verified-empty terminals), preserves the original audit **FAIL**, and classifies the allocation **HOLD**. The report says the 6,369-file raw allocation and exact freeze/audit remain under a host-local `results-local` path; that path is absent from this checkout and the PR contains aggregate projections rather than the raw events and per-key identities. Therefore this review verifies the published scoped interpretation and its preserved FAIL/HOLD labels, not the underlying raw custody or reconciliation. Keep the PR unmerged pending verifiable custody or reproducible raw-backed audit; do not rerun consumed A11. This does not establish global raw loss, experiment efficacy, MAP01 completion, or a change to Issue #59.

**2026-10-19 r62 — #8749 A09 raw packet independently checked and integrated:** PR [#8749](https://github.com/Unjuno/agent-interface/pull/8749) was merged after the public archive SHA-256 matched the result record; all 2,258 public-manifest entries matched, all 63 frozen source-file hashes matched the recorded source commit, the frozen runner/auditor hashes matched, and raw cancellation reconciliation independently returned 10/10 accounted with the guard's explicit same-token empty release. Its three cancellation regression tests passed locally; the replay-gate passed. The original frozen audit remains **FAIL** and the additive allocation result remains **HOLD**: the episode had no useful scorer event during pending inference and no MAP01 exit. The immutable A09 allocation was not rerun. The host-path preflight's default-path test is tied to the original macOS mount and POSIX guest mapping and is not a Windows portability test; the two host-independent cases passed on this checkout. The [idea index](IDEAS_AND_OUTCOMES.md) now records the result and limits under open Issue #59.

**2026-10-19 r63 — #8731 exact-source V39/V15 regression packet integrated:** PR [#8731](https://github.com/Unjuno/agent-interface/pull/8731) was merged after local reproduction of its audit against the frozen Git blob closure and logs: `PASS_SOURCE_AND_LOG_RECONCILIATION`, 73 source files, 107/107 normal and optimized. The seven modules were rerun from the exact frozen commit in a temporary tree on local Python 3.11.9; both modes passed 107/107 (the original evidence records CPython 3.12.14). The package manifest matched all ten entries. No production source changed from the named baseline, and no game, GUI, model, OS input, or live allocation ran. This is regression evidence only; it does not upgrade A09/HOLD or establish live control. The [idea index](IDEAS_AND_OUTCOMES.md) records the result under still-open #59.

**2026-10-19 r64 — #8768 A09 reconciliation hardened and independently rerun:** After A09's raw packet [#8749](https://github.com/Unjuno/agent-interface/pull/8749) was integrated, stacked PR [#8768](https://github.com/Unjuno/agent-interface/pull/8768) was retargeted from its retired experiment branch to `main`, marked ready after audit, and merged. The V2 auditor binds expected cancellation IDs to the archive report and fails closed on duplicate, missing, unmatched or unexpected cancellation/release/terminal identities. Local normal and optimized runs passed all 12 combined V1/V2 regression tests; the raw-archive audit returned `PASS_CUSTODY` for 10/10 expected cancellations, no duplicate IDs, and the exact saved V2 result. The original frozen audit **FAIL** and allocation **HOLD** remain unchanged; no live experiment was repeated and no task-effect claim was added.

**2026-10-19 r65 — #8769 journal-wire custody packet rescued onto current main:** Draft PR [#8769](https://github.com/Unjuno/agent-interface/pull/8769) was reviewed as an additive evidence rescue, marked ready, and merged after replay-gate, native-MCP and research-workspace-index checks passed. Independent verification matched all four package manifest entries and all 54 decompressed UTF-8 member byte lengths/SHA-256 values; no embedded helper was executed. The saved local-CI log records 43/43 steps without failures and 35 passing tests, but was not represented as a new source or native run. The packet's own boundaries remain: n=1 observer-enforced conditions, possible data-custody interleaving only, no external authenticity for private-original hash declarations, no outer-auditor capture, no raw peer stdout custody, and no real Codex/task effect or production adoption. The [idea index](IDEAS_AND_OUTCOMES.md) keeps the nested-data question under active #5884 separate from closed historical #7048 and open parent #59.

**2026-10-19 r66 — #8800 A14 public result preserved; raw-backed addendum remains unverified:** Open PR [#8800](https://github.com/Unjuno/agent-interface/pull/8800) reports one 12-decision A14 episode, zero preregistered hard-health guards, no useful scorer event during model intervals, 2 kills and no MAP01 exit. The original audit remains **FAIL** and the allocation remains **HOLD**. Its post-hoc reconciliation reports two distinct max-decrease action rejections followed by an admitted fresh plan, while explicitly separating these from the preregistered hard-health recovery endpoint. The reconciliation reads the local-only `episode/report.json`; the exact `results-local` path is absent from this checkout, and the PR publishes aggregate rows plus a report hash rather than the report/raw protocol/images. Keep the PR unmerged pending reproducible raw-backed verification; do not rerun consumed A14. This absence is scoped to the current checkout and does not establish global raw loss or change Issue #59.

**2026-10-19 r67 — #8810 A15 result and #8818 custody manifest integrated with limits:** PR [#8810](https://github.com/Unjuno/agent-interface/pull/8810) retains A15's public `HOLD` and original audit `FAIL`; [#8818](https://github.com/Unjuno/agent-interface/pull/8818) adds the full 3,859-entry path/size/hash manifest and hash-bound author-side readback, without copying raw prompt/image/protocol contents. Independent metadata checks verified manifest SHA-256, unique safe relative paths, declared 119,669,935-byte total, and the tracked A15 public-summary digest at exact #8810 head; the raw files themselves are absent here, so the local `PASS_A15_RAW_CUSTODY` claim is not independently reproduced. Four verifier mutation tests pass. Before merge, the package checksum list was cleaned to exclude two non-delivered `__pycache__` hashes; all eight delivered entries match, and the updated PR checks passed. The #8810 suite rerun on Windows passed 27 host-independent tests; its two host-root/POSIX-path assertions are tied to the original macOS runner and fail under this Windows checkout. Preserve that portability limit, do not rerun the consumed allocation, and keep #59 open.

**2026-10-19 r68 — #8817 strict recovery-classifier method review integrated:** Draft PR [#8817](https://github.com/Unjuno/agent-interface/pull/8817) was marked ready after local inspection and merged as an additive auditor-method result. The three frozen A16 code/test copies match their pinned source commit byte-for-byte. Its strict classifier and frozen-test harness pass 11/11 in both normal and optimized Python 3.11.9; the replay-gate passed. The finding is limited to fail-open semantics when `model_action_discarded` is absent/non-boolean and the need to check admission independently. The retained A16 allocation exposed no qualifying guard and had no episode report, so the method review cannot classify its recovery or change its existing STOP; no allocation was rerun. The idea index records that boundary under still-open #59.


**2026-10-19 r69 — owned close-timeout cleanup integrated:** PR [#9095](https://github.com/Unjuno/agent-interface/pull/9095) adds a regression for the owned-process `close()` lock-timeout path. After exact child retirement, the caller now re-reads the checksummed held-input obligations and performs the existing PID-qualified disconnect-gated bounded release attempt; the result still reports release `UNKNOWN`, task success null, replay disabled, and possible late server requests. The regression failed before the patch; `runtime.cli_v1.test_mcp_owned_process` passed 17/17 in normal and optimized Python 3.11.9, with `py_compile` and `git diff --check` also passing. This is local Fake X/process-composition evidence only: it does not establish physical release, blocked-server-I/O release, queue drainage, application effect, MAP01, or a hard OS scheduling bound. No WSLc allocation or live GUI was used.


**2026-10-19 r70 — remaining owned close-retirement branches integrated:** PR [#9097](https://github.com/Unjuno/agent-interface/pull/9097) extends PR #9095's close-timeout recovery receipt to an unavailable close RPC response and a child remaining alive after a close receipt. Cleanup is cached and attempted at most once after confirmed retirement; unconfirmed retirement does not issue the independent release request. Two regressions failed before the patch. `runtime.cli_v1.test_mcp_owned_process` passes 19/19 in normal and optimized Python 3.11.9; `py_compile` and `git diff --check` pass. This remains local Fake X/process evidence only and does not establish physical release, blocked-server-I/O release, application effect, MAP01, or a hard scheduling bound. No WSLc allocation or live GUI was used.

**2026-10-19 r71 — #7616 retained failure integrated and membership refreshed:** PR [#7616](https://github.com/Unjuno/agent-interface/pull/7616) merged at `512905853b5af1f39306038bc1ac5244915d1c70` as a retained #57 offline compiled-graph/pixel-handle composition package. Its original `FAIL_SOURCE_BASE_LABEL_MISMATCH` remains the disposition: the candidate labels source `41df296...` while `FREEZE.json` pins `9dc383a...`, and the candidate exit code/exact timestamps were not retained. A read-only audit matched four relevant runtime module blobs to both cited commits and verified the two package checksum sets after a path-specific no-text-conversion rule preserved original bytes. The saved candidate was not rerun; matching modules and manifest integrity do not waive the frozen source-label failure. This is not live GUI, application-effect, or efficiency evidence and does not resolve #6/#56. The r44 paginated open-set read at main `512905853b5af1f39306038bc1ac5244915d1c70` records 1,675 open Issues and 503 open PRs, exactly r41's Issue set and r41's PR set minus merged #7616 ([r44 inventory](maintenance/repository-inventory-20261019-r44.md)). No Issue was closed. The current worker map and #6/#56 family entry now point to the retained result; broad semantic classification and custody review remain unfinished.

**2026-10-19 r72 — post-#9103 membership recheck:** At `2026-10-18 23:17:37 UTC`, complete paginated reads at main `9817a98b1df376615f503a8cd62183f2d4fd7855` found 1,675 open Issues and 503 open PRs. Sorted numeric-ID hashes match r44 exactly; PR #9103's create-and-merge cycle left no open-set change. The [r45 inventory](maintenance/repository-inventory-20261019-r45.md) is the new current membership pointer. This is a membership/freshness update only; semantic classification remains unfinished and no Issue was closed.

**2026-10-19 r73 — local worktree custody recheck:** At `2026-10-18 23:20:43 UTC`, the repository worktree registry contained 12 checkouts: 11 clean and one dirty only because of two untracked Edge profile directories. The dirty checkout's branch tip is the head of merged PR #7856; no current open PR head matched a registered worktree branch name. Each profile contains 47 files, together 3,030,147 bytes, with last-write metadata from 2026-10-05. A process command-line scan found no non-audit process naming either directory, but owner, session, and evidence role remain unknown. The [worktree custody recheck](maintenance/git-worktree-custody-recheck-20261019-r01.md) records all 12 branch/tip/status entries and the limits. No worktree or artifact was removed. Next: identify the profile owner/raw role, then check base-branch dependencies and custody for the remaining clean worktrees. Open membership at main `237915de7886535a599343c9cd8331787d556c50` remained 1,675 Issues and 503 PRs, with r45's ID hashes unchanged. The [r46 inventory](maintenance/repository-inventory-20261019-r46.md) captures this read; no Issue was closed.
