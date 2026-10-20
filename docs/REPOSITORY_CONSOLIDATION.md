# リポジトリ全体の整理計画
実行手順は[リポジトリ整理の実行計画](REPOSITORY_CLEANUP_PLAN.md)を参照。Issueは意味と仮説を正規カタログに整理し、根拠・後継・再開条件をIssueへ戻してから個別に処遇する。件数を減らすこと自体は完了条件ではない。

**最新の完全membershipポインター (r126, 2026-10-21):** main `d3439cb9adee0bd64492d5378c05568357d38d56`を完全ページングし、前後SHA一致でIssue 1,655件/PR 463件を確認した。Issue ID setはr120と同一、PR setはr120から#8716/#8733/#8841/#8844のみ除外。詳しくは[r126 inventory](maintenance/repository-inventory-recheck-20261021-r126.md)。r125のPR差分説明にあった#9303はr120の全PR exportに含まれず、r126で訂正した。最新の全体整理目的・実行順・完了条件は[repository cleanup plan](REPOSITORY_CLEANUP_PLAN.md#current-cleanup-objective-2026-10-21)を参照。r119の223 exact-URL semantic routesは未分類のままである。#8641、#8620、#8636 A04はcanonical recordを整えたが、各々の別個の研究上の問いはopenのまま。D01–D11 receiptsは保存済み。意味分類、exact-head PR処遇、branch/worktree/evidence custodyは未完了で、次の整理バッチで有限の範囲を選ぶ。

**Bounded family update (2026-10-21):** [Issue #8641's canonical record](ideas/uncertainty-intervention-decomposition.md) preserves its `H_FAIL_NO_ADDED_DECISION_VALUE`, exact evidence, and the out-of-protocol candidate-invocation note. PR #9293 merged the 27 unique evidence blobs byte-exactly, and the original #8733 was closed as superseded after exact readback. Issue #8641 remains open for its unresolved transfer question.

**履歴ポインター (2026-10-20):** mainはPR #9285のsquash commit `2c29aee34e258053670fa7df9108889f35aecef2`。現行の四レーン、完了条件、次の順序は[repository cleanup plan](REPOSITORY_CLEANUP_PLAN.md#current-checkpoint-after-pr-9285--2026-10-20)を参照する。#9285後のcount-only GraphQLは1,655 open Issues / 467 open PRs。r119の完全ページングmetadataは最新の保存済みmembershipだが、現在の集合や状態変更根拠ではない。D01–D11で265件の候補をすべてルーティングし、個別結果に基づき17件を完了処理、残る248件をopenとして保持した。残る仕事は223件のsemantic routes、全open PRのexact-head disposition、branch/worktree/artifact custody、および入口文書と履歴の収束。D01–D11 receiptsは履歴として保持する。件数減少や新規snapshotを目的化せず、IssueやPRのstate変更前に対象を再取得する。

**Issue family disposition D05 (2026-10-20):** [D05 receipt](maintenance/idea-family-triage-r119/D05.md) reconciles 25 candidates against B07–B08. One bounded caller-source publication request (#3382) was closed after verifying merged PR #3420 and preserving limits in its Issue comment; 24 remain open. Aggregate after D01–D05 is 1,656 open Issues / 468 open PRs, not a paginated audit. D06–D10 remain unreviewed.

**Issue family disposition D06 (2026-10-20):** [D06 receipt](maintenance/idea-family-triage-r119/D06.md) reconciles 25 candidates against B08–B10. All 25 remain open; no state changed. Aggregate after D01–D06 is 1,656 open Issues / 468 open PRs, not a paginated audit.

**Issue family disposition D07 (2026-10-20):** [D07 receipt](maintenance/idea-family-triage-r119/D07.md) reconciles 25 candidates against B10–B11. #6990 alone closed for the bounded T8 offline receipt-schema audit; separate STOPs remain. #6767, #6875, #6932, and #6957 were clarified while preserving real task/resource boundaries.

**Issue family disposition D08 (2026-10-20):** [D08 receipt](maintenance/idea-family-triage-r119/D08.md) reconciles 25 candidates against B11–B12. All remain open and unassigned; no state changed. Method-scoped outcomes, failures, STOPs, and proposals remain separate.

**Issue family disposition D09 (2026-10-20):** [D09 receipt](maintenance/idea-family-triage-r119/D09.md) reconciles 25 candidates against B12–B16. All remain open and unassigned; no state changed. Separate method results, STOPs, integrity holds, unrun proposals, and WSLc ownership boundaries remain explicit.

**Issue family disposition D10 (2026-10-20):** [D10 receipt](maintenance/idea-family-triage-r119/D10.md) reconciles the final 25 queue rows against B16–B17. All remain open and unassigned; no state changed. The #8595 A01 result and post-freeze literature note are reflected in the catalog. #8619's Dockerless WSLc policy remains distinct from resource authorization. All 265 r119 candidate rows across D01–D11 are routed; 17 bounded closures and 248 open candidates are documented. The remaining cleanup includes 223 idea-document semantic routes, 468 open PRs, and branch/worktree custody.

**Historical full row-level metadata r114 (2026-10-20 10:39 UTC):** main `270e886685f3814f053824a5110e9226b1b3f5a5`でopen Issue 1,672件・open PR 468件。[r114 inventory](maintenance/repository-inventory-recheck-20261020-r114.md)。r119 is the latest full metadata at main `666888468e81b3c3c2c1e4103df549afcaf23822`; both snapshots are membership metadata, not semantic triage, per-PR review, or owner/custody proof. Re-fetch the exact item before a state change.

**Historical membership r106 (2026-10-20 06:33 UTC):** main `6eaade1b9129d1ab8b8a87ea9ec2763c5d334959`でopen Issue 1,672件・open PR 470件。[r106 inventory](maintenance/repository-inventory-20261020-r106.md)。#8840はr106時点でopenで、r107までにopen setを離れた。

**Historical membership r96 (2026-10-19 15:22 UTC):** main `b0e47dd4f67a57db5c530d19251ad172e29554d7`でopen Issue 1,673件・open PR 479件。[r96 inventory](maintenance/repository-inventory-20261019-r96.md)。歴史的なr96/r95集合比較であり、最新membershipではない。

**Open PR disposition audit r01 (2026-10-20):** nine PRs (#8702, #8832, #8836, #8840, #8841, #8843, #8844, #8845, #8848) were audited against main `c2f0cd874ce50af310a071b3df98ca52eba7b057`. None is recorded as merge-ready: the batch contains raw-custody holds, two LF/CRLF manifest defects, one report checksum/index failure, a nonportable test fixture, stale bases, and scoped HOLD/FAIL results. The [audit receipt](maintenance/open-pr-disposition-audit-20261020-r01.md) gives a no-rerun, evidence-preserving next action for each. This is a bounded sample, not all-open-PR triage; it changes no Issue/PR state and does not justify bulk closure.

**Issue family disposition D01 (2026-10-20):** [D01 receipt](maintenance/idea-family-triage-r119/D01.md) reconciles 25 previously routed candidates against their current catalog rows. #163 and #177 were individually closed after preserving the retained failure report and the 13/13 scoped offline binding result, respectively; their comments link the exact reports and delimit remaining questions. The other 23 remain open. GraphQL aggregate after these changes: 1,668 open Issues / 468 open PRs. No new paginated membership census was created; use the last exact ID-set checkpoint above and refresh before further state changes. D02–D10 remain unreviewed.

**Issue family disposition D02 (2026-10-20):** [D02 receipt](maintenance/idea-family-triage-r119/D02.md) reconciles 25 candidates against B03–B05 and the current catalog. #249 and #273 were closed only after their merged result reports were verified in current main and linked from individual Issue comments; no claim of complete raw-archive custody is made. The other 23 remain open with distinct outcomes and custody limits. Aggregate after D01/D02 is 1,666 open Issues / 468 open PRs; this is not a complete paginated audit. D03–D10 remain unreviewed.

**Disposition follow-through r02 (2026-10-20):** the #8832 fixture defect was repaired in current-main successor PR #9217, with its exact 15-file research package preserved and catalogued; Issue #8574 was closed only after its scoped result and successor were linked. The separate #8843 A10 construction packet is preserved under `research/doom/v39_authored_pair_cancel_composition_a10_20261012/`, with its seven CRLF-derived digests corrected against exact retained Git blobs and the saved non-executing audit independently reproduced in a temporary copy. Its 19 original package blobs and saved result remain unchanged; the packet is catalogued separately from live-allocation A10 and strict-release A10. Current-main successor PR #9218 merged at `bb4bf3f4b14247aa718f765736e6d920fd8e85d4`; stale Draft #8843 was closed as superseded with a pointer to the preserved successor. Issue #59 remains open because live release, task effect, recovery, and MAP01 gates remain unresolved. This follow-through covers two sampled records only; r96 remains a historical membership snapshot and the full open-PR/Issue disposition is still outstanding.

**Disposition follow-through r03 (2026-10-20):** Original Draft PR #8848's A12 soft-ammo feedback packet was preserved in current-main successor [#9234](https://github.com/Unjuno/agent-interface/pull/9234), merged at `6eaade1b9129d1ab8b8a87ea9ec2763c5d334959`. Exact Git-blob verification found seven CRLF-derived SHA256SUMS entries; the successor updates only those digests, adds a custody repair receipt, and indexes the scoped result. All saved experimental raw, frozen source, test, and audit files remain byte-identical. Replay-gate, public-navigation, and research-workspace-index passed; no WSLc construction or saved audit was rerun. #8848 was closed with a successor link, while scientific parent Issue #59 remains open. The complete paginated membership baseline is now r106; this is still one sampled PR disposition, not full open-PR/Issue triage or workspace custody closure.

**Disposition follow-through r04 (2026-10-20):** Original PR #8840's A03 packet was preserved in current-main successor [#9236](https://github.com/Unjuno/agent-interface/pull/9236), merged at `92fddaffbe43a4a984f54690473511f744784ae3`. The exact 2,231-file, 63,489,719-byte first-outcome archive matched every internal-manifest path, size, and SHA-256; all 17 package checksums matched Git blobs. The analysis-index failure was a missing generated directory entry, now repaired. The candidate/auditor and consumed allocation were not rerun; `HOLD_UNCERTAIN` is unchanged. A new [#31/#8636 family crosswalk](ideas/relative-view-rotation-features.md) keeps A01–A05 outcomes and the next finite discriminator separate. #8840 was closed as superseded, while #31/#8636 remain open. The complete membership baseline advanced to r107; this remains one sampled PR disposition, not full Issue/PR/workspace-custody completion.

**Aggregate recheck (2026-10-20 04:53 UTC):** GitHub GraphQL reports 1,672 open Issues and 476 open PRs after the #8574 closure and #8843 supersession. This is an aggregate count only, not a paginated membership or semantic audit; r96 remains the latest retained membership snapshot, and each record still requires individual review before state changes.

## 2026-10-19 全体整理の実行計画 — アイデアを保存して作業面を収束

### 目的とゴール

Issue/PR数をゼロにするのではなく、研究アイデア・反証・結果・未解決点を失わず、次の担当者が一つの独立した仕事をすぐ選べる状態にする。進行中のコンピューター制御研究ゴールは維持し、そのゴールに関係する証拠・実装・残差は研究系譜から外さない。整理完了時には、各open Issueに「実行する理由と次の判別試験」または「担当・依存・保留解除条件」があり、アイデアだけの項目は正規カタログから元Issueへ戻れる。各open PRには現head/base、固有の差分・証拠、依存、所有状態、ローカル検証、次の処置がある。

**最新の完全row-level metadata r85 (2026-10-19 09:22–09:25 UTC):** main `b1bff75ffa5d06f6d2c7d10bc7a89b1ab2dbdc16`でopen Issue 1,673件・open PR 482件の完全なrow-level CSV、PR head/base、review/merge state、check rollupを取得した。[r85 inventory](maintenance/repository-inventory-20261019-r85.md)。r70からIssue集合は不変、PRは#9171追加・8件close/merge。詳細のworktree artifact custodyは[surface map](maintenance/repository-surface-map-20261019.md)。

**最新のmembership snapshot r86 (2026-10-19 10:59 UTC):** main `f08f60fa3be0612632d768689d23cd2d88a45c41`でopen Issue 1,673件・open PR 480件を完全ページングし、GraphQL総数と照合した。[r86 inventory](maintenance/repository-inventory-2026-10-19-r86.md)と[Issue CSV](maintenance/open-issues-2026-10-19-r86.csv)、[PR CSV](maintenance/open-prs-2026-10-19-r86.csv)。r86はr85より新しいmembership記録だが、PR check rollup・本文コメント・意味上の処遇は含まない。r85は引き続きchecksを含む最後の詳細スナップショット。各状態変更の直前に対象を再取得する。

**最新のmembership snapshot r87 (2026-10-19 11:15 UTC):** main `4d95015b8a6f64e1cef9736ce8f8b984d9eb2cfa`でopen Issue 1,673件・open PR 479件を完全ページングし、GraphQL総数と照合した。[r87 inventory](maintenance/repository-inventory-2026-10-19-r87.md)と[Issue CSV](maintenance/open-issues-2026-10-19-r87.csv)、[PR CSV](maintenance/open-prs-2026-10-19-r87.csv)。r86からIssue集合は不変で、PR #9171をmainへ統合した結果を反映。r87もPR check rollup・本文コメント・意味上の処遇は含まない。各状態変更の直前に対象を再取得する。

過去の完全なrow-level metadataは[r70](maintenance/repository-inventory-20261019-r70.md)（2026-10-19 05:13:23 UTC、main `e83e52dc0eda4c3ebc5f54f676971ce9e71a6006`、open Issue 1,673件、open PR 489件）である。05:27:38 UTCにmain `95386ee7e10e7ffc7422bd473f4db29991bd28b6`を基準に完全ページングを再実行したところ、ID集合とr70のIssue/PR取得metadataは一致した。詳細は[r74 reconciliation](#実行更新-r74--入口の整合とworktree-custody棚卸し)。新しいmetadata CSVは重複を避けて作らず、r70をimmutableなhistorical snapshotとして保持する。r52 coverage auditは全Issueの索引経路を確認したが、歴史的な研究選定表にprimary rowがない項目の意味分類とPR・担当・worktreeとの結合監査は未完了である。membershipは状態の時点記録であり、状態変更前にはその時点の現状を再確認する。

**最新membershipの再確認 r54 (2026-10-19 02:02:31 UTC):** main `289a0c19ab85581cb3414b01d92f2f887ae0c60b`で完全ページングを読み、open Issue 1,673件、open PR 502件を確認した。sorted ID set hashesはr53と完全一致するため、CSVの重複生成はせず、[r54再確認記録](maintenance/repository-inventory-recheck-20261019-r54.md)だけを追加した。semantic triage、個別PRのレビュー/検証、担当・worktree custodyは別作業であり未完了。

**最新membershipの再確認 r55 (2026-10-19 02:16:48 UTC):** main `0d022b76b6f940638da86c1ea4f71930c8df1626`でIssue/PR一覧を完全ページングし、open Issue 1,673件・open PR 502件を再確認した。ID集合のSHA-256はr53/r54と一致するため、CSVを重複生成せず、[r55再確認記録](maintenance/repository-inventory-recheck-20261019-r55.md)を追加した。これはmembershipの確認であり、意味分類、PR差分/検証、担当・worktree保全は未完了。

**最新membershipの再確認 r56 (2026-10-19 02:25:07 UTC):** PR #9135統合後のmain `39e7bdfc729b392985295048e89b8003acf77c36`でIssue/PR一覧を完全ページングし、open Issue 1,673件・open PR 502件を再確認した。ID集合はr53/r55と一致するためCSVは再生成せず、[r56再確認記録](maintenance/repository-inventory-recheck-20261019-r56.md)を追加した。membership以外の意味分類・所有・PR評価は未完了。

**最新membershipの再確認 r57 (2026-10-19 02:37:22 UTC):** PR #8854統合後のmain `d25b497cc8a05d45158a81c038ee15e03aabdddc`で完全ページングし、open Issue 1,673件・open PR 501件を確認した。Issue ID hashはr53/r56と一致し、PR countは1減少した。r53 CSVがrow-level exportでない不具合を発見したため、r57では正しい完全row-level exportを新規生成し、履歴snapshotは上書きしない。これはmembership/filer-integrityの再確認であり、意味分類・所有・残りPR評価は未完了。詳細は[recheck r57](maintenance/repository-inventory-recheck-20261019-r57.md)。

**最新membershipの再確認 r58 (2026-10-19 02:42:33 UTC):** PR #8853統合後のmain `91d8859530e9c65e7f24fb4843d4cbeef3a9ece6`で完全ページングし、open Issue 1,673件・open PR 500件を確認した。Issue ID setはr57と同一、PR setはr57から#8853だけを除いた500件だった。新しいID hashと完全row-level CSVは[recheck r58](maintenance/repository-inventory-recheck-20261019-r58.md)に記録した。

**最新membershipの再確認 r59 (2026-10-19 02:49:49 UTC):** PR #8893統合後のmain `5d5b121ca3c0c922c6eff36793fbdffe5104c42d`で完全ページングし、open Issue 1,673件・open PR 499件を確認した。Issue集合はr58から不変、PR集合は#8893だけ減少した。[r59 recheck](maintenance/repository-inventory-recheck-20261019-r59.md)に完全CSVとhashを記録した。

## 実行更新 r84 — 現行membershipを再照合し最初のidea familyを監査

2026-10-19 07:50 UTCにGitHubの完全ページングをmain `9a91dd2f24193831b6320f24278f5e8d8a1048e2`で確認した。open Issue 1,673件はr70と同じID集合、open PR 484件はr70から#8794、#8798、#8803、#8811、#8825が減り追加なしであり、r83のmembership記録を新しいmain SHAで再確認した。全rowを再保存せず、[r84 recheck](maintenance/repository-inventory-20261019-r84.md)に結果を記録した。

最初の意味監査ではlive #6/#56と[reactive-macro/symbolic-interface family](ideas/reactive-macro-symbolic-interface.md)を照合した。既存ページは広いreactive-control案と絞られたplanner-authored symbolic-interface仮説を区別し、A05/R02/A14/#7616の結果と限界を保ち、実験・統合が未完であることを正しく示す。両Issueをopenで維持し、新規Issueや重複ideaページを作らない。次はwork map上の別familyを一つ選び、質問・証拠・担当/依存・有限な次試験を一緒に分類する。Issue closureはidea保全とsourceへの再開リンクを個別確認した後にだけ行う。これはmembership更新と一familyのread-only意味監査であり、repository-wide triageやcleanupの完了ではない。

### 整理原則とIssueの処置

- **まずアイデアを整理し、その後にIssueの状態を決める。** アイデアは仮説単位で正規の研究familyページへまとめる。元Issue番号・URL、異なる仮説、既存の肯定/否定/保留結果、raw/source、最強の単純な比較対象、未解決の反証、次に結果を変える有限の試験を結び付ける。短い索引やfamily agendaを入口にし、実験raw・歴史コメント・先行結果を移動・上書きしない。
- **Issueの分類は意味で行う。** 各項目を研究案、実行中/割当済み、結果統合待ち、実装課題、証拠/所有保全、共有運用欠陥、完了、重複/後継あり、保留/対象外のいずれか（必要なら複数）として記録する。assignee空欄やopen状態だけで担当不在と判定しない。
- **アイデアだけのIssueは、アイデアを正規カタログへ移し、元Issueにそのリンクと「カタログ化・未実施」を記録した後なら、保留/研究候補として個別に閉じてよい。** これは研究が成功・解決したという意味にしない。未検証の実験、未達のユーザー目標、現行作業、未解決のデータ/所有問題、必要な統合判断を追うIssueはopenのまま残す。重複は独自の問いと結果をfamily記録へ統合してから後継へ誘導し、結果を消さない。
- 各Issueの最終処置は `keep-open/actionable`、`keep-open/blocked-with-exit-condition`、`catalogued/deferred`、`superseded`、`completed-scoped`、`out-of-scope` のように理由を明記する。閉じる場合はIssueに根拠・保存先・後継/再開条件を残してから閉じ、単なる件数削減・古さ・コメント欠如を理由にしない。

### PR、branch、worktreeの個別処置

PRはIssueと別々に、最新head/base SHA、全差分、必須保護条件、ローカルで必要な検証、固有のコード/証拠、stack/後継依存、作者と現在のworktree/出力所有を照合する。処置は `merge-ready`、`needs-local-fix`、`stack/retarget`、`evidence-custody-hold`、`duplicate/superseded`、`owner-confirmation-hold`、`close-after-preservation` に分類し、理由を残す。技術的に独立した修正・限定結果・有用な失敗証拠は適用可能なローカル確認と実際の保護条件を満たせば進める。FINAL v5にない一律の非作者レビュー人数や承認投票を追加しない。任意CIが遅いこと自体は待機条件にせず、欠陥・必須check・権限条件は無視しない。

branch/worktreeはPRのclose/mergeだけで削除しない。exact tip、mainへの内容保全、未追跡/ignoredデータ、raw、依存branch、現担当・実行プロセス、復旧可能性を確認する。所有者または保全先が不明なものは残し、照会と判定を記録する。GitHubのmerge/close、ref削除、ローカル作業ツリー削除はそれぞれ別の操作として照合する。

### 並列化の境界

同時に進める作業は、異なる研究familyまたはPR/Issueの非重複集合と専用出力先へ割り当てる。shared index・worker map・この計画への変更は一度に一つの統合担当に集約する。担当者は対象Issue/PR、正確なhead、触るファイル、依存、出力先、次の有限な判定を記録する。レビュー人数や他人の到着待ちを作業開始の条件にしない。共有資源・ライブ環境はコード編集の並列性から推測せず、実験前に所有・未消費枠を別途確認する。

### 実行フェーズと完了条件

1. **基準線を更新する。** 完全ページングでIssue/PRのID集合、PR head/base、main SHAを取得し、前回からの差分だけを履歴化する。既存worktree一覧・研究証拠所在への入口も確認する。検索上限や未取得ページは欠落の証明にしない。
2. **アイデアをfamily単位で編集する。** B01–B20はnavigation routing完了であり、意味のトリアージ完了ではない。未分類489件と既存family内のopen候補を、独立した問いごとの小バッチに分ける。各バッチは元Issue/PRを読み、既存のコード・結果・反証・raw参照を照合し、family agendaと `IDEAS_AND_OUTCOMES.md` に差分を統合する。新しいIssueは異なる科学的問い・統合判断・実証済みの共有欠陥がある場合だけ作る。
3. **Issueを一件ずつ処置する。** familyバッチごとに分類、次の作業、所有/依存、閉鎖根拠を表にし、案のカタログ化と実験の解決を明確に分ける。まず作業を妨げるfamilyから処理し、完了・カタログ化できるものはリンクと再開条件を付けて個別に閉じ、残る実証作業は小さく具体化して維持する。
4. **open PRを一件ずつ収束させる。** live exact-headとstack関係を再確認し、上記PR分類を付ける。独立成果は小さくローカル検証し、stackは依存順を保ち、未保全raw・所有不明・未解決の必須条件があるものはhold理由と解除条件を記録する。merge後はremoteの確定状態を確認し、任意CI未実行と必須条件を区別する。
5. **重複と構造を最後に整理する。** family記録が定着した後にだけ、重複ページ/索引、古い入口、不要と所有確認済みのbranch/worktreeを整理する。短いナビゲーションと正規ページを優先し、一括移動・改名は避ける。
6. **再監査して引き継ぐ。** 全open Issue/PRが最新inventoryから一意に追跡され、意味・証拠・所有/依存・次の処置を持つこと、閉じたIssueの案/結果/後継が保全されること、merged/closed PRの固有内容がmainまたは明示した保管先に残ることを照合する。main clean、全PR merge、全Issue close、全研究PASSは完了条件にしない。

各familyバッチは、対象範囲、live参照時刻、既存成果/反証、アイデア索引の変更、Issue/PR処置、ローカル確認、未確定点、次の有限作業を短いreceiptに残す。保存済みFAIL/HOLD/STOPや消費済み実験は書き換えず、正式実験を整理目的で再実行しない。

### 着手順

1. r52からのlive membership差分と、現在のopen PRのexact-head/base/stack状態を更新する。
2. first batchは、同じ共有resourceを使わず、既存のfamily/成果で確実に片付けられる小さな集合を選び、アイデアの保存先とIssue処置を同時に実証する。
3. 同じ記録形式を他familyへ適用し、各workerが別familyと専用pathを選べる状態にする。
4. high-riskの実験・ライブ資源所有問題・一意なraw保全問題は低件数の一般整理キューに混ぜず、元の専用familyに残す。

この計画は作業を開始するためのチェックポイントであり、整理完了の宣言ではない。計画自体に追加の人手承認数や全体停止条件を設けない。上位の権限・FINAL v5・実在のGitHub保護・既存の有効な実験割当は引き続き適用する。

## 実行状況 r01 — r53基準線、30件PRトリアージ、限定証拠の統合

2026-10-19 01:51:04 UTCに[r53](maintenance/repository-inventory-20261019-r53.md)を取得した。open Issue 1,673件（r52と同一ID集合）、open PR 502件（#8910統合によりr52から1件減）である。CSVとID集合のSHA-256はr53スナップショットに記録した。

[open PR triage receipt r01](maintenance/open-pr-triage-receipt-20261019-r01.md)は最近更新された30件をread-onlyで初回分類した。1件（#8910）はcurrent mainとの衝突なし、7 checks成功、保存JSONとのNode再実行一致を確認して有限モデルの**限定証拠**として統合した。merge commitは`b65dfc88c0cfe8a36e72c7d4906c7be355021b3d`。PRの初回ready化後にreplay-gateが再実行中だったが、同一headで先行成功があり、mainに保護/rulesetがないこととローカル再実行を確認して統合した。Issue #8909はGitHub上で同時にcompletedとして閉じられたが、元の研究案はカタログ未登録で、PRもモデル限定と明記していたため再openし、未解決の研究課題として記録した。実際の結果は仮説・runtime/GUI効果・効率主張へ昇格していない。

残り29件のreceipt上の処置候補は、限定証拠の統合候補、著者修正、conflict/stack/lineage確認、custody hold、preserved FAIL/HOLD/STOPに分かれる。#7760と#7087のPR-local複数人条件は一人の作業開始・無関係な統合の必要条件にしない。一方、独立scorer等が実験の測定定義そのものなら、その科学的要件は保持する。次はreceiptのmerge候補をexact-headで再照合し、独立した小さい証拠から個別に統合しながら、489件のうち一つのfamilyを意味分類まで完了する。これは全502件のPR監査や全Issueトリアージ完了を意味しない。

## 実行状況 r02 — r57の正規inventoryとPR #8854の限定統合

2026-10-19 02:37:22 UTCのmain `d25b497cc8a05d45158a81c038ee15e03aabdddc`で完全ページングを再取得し、open Issue 1,673件・open PR 501件を確認した。Issue ID hash `4ca4576b8a328d9f41b862a3c7ad3793edd9ddd085bb127d708796e9b6082dd6`はr53/r56と一致する。PR ID hashは`b989d5a16e7347304e7f60adc5d8a6767e1967976735b1f92fde425aa1feba70`。r57 CSVは各object一行で再生成し、行数とnumeric-ID hashを読み戻し確認した。

この時点で旧r53 CSV pathがPowerShellのarray metadataだけを含むことを発見した。履歴pathは書き換えず、旧CSVを正本として扱わないことを[r57 recheck](maintenance/repository-inventory-recheck-20261019-r57.md)に記録した。既存familyにすでにあるA01–A13 live packetの一つへ混入させず、別の合成/source-level証拠としてPR #8854を整理した。exact head `37c6f27c33c4de6d555aacab1f74225567de4e22`、main base、17/17 SHA manifest、Windows Python 3.11.9 normal 8/8、`-O` 8/8、独立audit 34/34、GitHub replay-gate PASSを確認し、2026-10-19 02:35:29 UTCにsquash mergeした。merge commitは`d25b497cc8a05d45158a81c038ee15e03aabdddc`。#59はopenのまま、Issue stateやallocationは変更していない。

この統合はrepository-wide semantic triageではない。残る501 PR・1,673 Issuesの意味/依存/custody確認、保全されたアイデアの個別disposition、残worktreeの所有確認は未完了。次の有限作業はr57 inventoryから一familyだけ選び、source Issue・family idea・実際の結果/後継を照合したreceiptを残してから、可能なIssue処置へ進むこと。

## 実行状況 r03 — stale-action A14の証拠統合とr58基準線

PR #8853をexact head `6a9a7694942e2a566e7b7f51b2abb9ec1b8ed26d`で再確認し、A14 packetがconflicted PR #8842の差分に含まれないことをtreeで照合した。保存済みWSLc結果は再実行せず、Windows Python 3.11.9のsource tests 2/2（通常・`-O`）、独立audit、22件のSHA manifest、GitHub replay-gateを確認して2026-10-19 02:42:19 UTCにintegrateした。merge commit `91d8859530e9c65e7f24fb4843d4cbeef3a9ece6`。#8854とは別の「新しい観測で古いplanner応答を拒否」predicateとして、[MAP01 family crosswalk](ideas/map01-live-guard-evidence-family.md)と[worker map](WORKER_WORK_MAP.md)へ登録した。

同commit上のr58 complete inventoryはopen Issue 1,673件、open PR 500件。Issue hashは不変、PR ID集合はr57から#8853だけ除外された。残り500 PR/1,673 Issuesの意味分類・依存・所有証拠が必要であり、repository-wide clean完了とは宣言しない。次は既存idea catalog内で独立した一familyを選び、open Issueの現本文/コメントと結果・後継を突合し、アイデアだけの重複または未実行案を個別dispositionする。

## Historical discovery checkpoint — r51/r52 navigation queue and disjoint work batches

At that time, the complete live membership read was [r52](maintenance/repository-inventory-20261019-r52.md), captured 2026-10-19 01:35:59 UTC against main `00640a3143ff426d259dcc85793aec26d974043c`: 1,673 open Issues and 503 open PRs. The [r52 coverage audit](maintenance/idea-index-coverage-20261019-r52.md) finds 1,184 open Issues with primary rows in the historical research selection and 489 without. These are exactly the r51 missing-row queue minus #104 and #1798, now closed; all remaining Issues have routes through the completed B01–B20 receipts. A strict cross-index check found 38 r51 items without a standalone first-column row in `IDEAS_AND_OUTCOMES.md`; 30 already had issue/family/successor cross-links, and eight lacked a URL in either index. A routing-only appendix adds links for those eight without inventing outcomes. The r51 queue and receipts remain immutable historical discovery aids, not semantic classifications or closure instructions. Workers should use current evidence and take disjoint families/output paths in parallel; only edits to the same shared index/map need a single integrator at a time. Preserve ideas and source history, and close only on each Issue's evidence-based disposition.

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

### B09 bounded intake — computer-control direction, evidence custody, and runtime integration

The [B09 receipt](maintenance/issue-discovery-b09-20261019.md) routes rows 201–225 and adds five missing direct outcome summaries. It preserves prior allocation HOLDs and source-publication gaps, distinguishes synthetic/scoped results from caller-visible computer-control evidence, and records #5280's direction without treating documentation as task success. Thirteen cited PRs are merged except #8271, which remains Draft. All 25 Issues were open and unassigned at intake, with no status or experiment changes. B10 is next; disjoint worker paths remain available in parallel.

### B10 bounded intake — oversight studies, control interfaces, and operation policy

The [B10 receipt](maintenance/issue-discovery-b10-20261019.md) routes rows 226–250; all 25 Issues already had curated direct index entries, so no duplicate outcome rows were added. It preserves method-scoped results, an open Draft package, and separate source/publication corrections. Fourteen cited PRs are merged except #7940, which remains Draft. The review of #6767 found no worker-exclusive or reviewer-count gate: its body permits parallel authorized work, but “retain recovery responsibility” during external waits lacks an expiry/discharge condition and could impose indefinite personal duty. The repository record recommends bounded ownership, a next check, accepted handoff, and explicit stop/expiry; no Issue or policy was edited in this intake. No status or experiment changed; B11 is next.

### B11 bounded intake — coordination, review-count, and object-memory gates

The [B11 receipt](maintenance/issue-discovery-b11-20261019.md) routes rows 251–275; all 25 items were already represented in the curated index. It preserves scoped outcomes and confirms #7359 is merged while #7940 remains Draft. It found issue-local two-human-approval conditions in #6875/#6932 that could prevent a single worker from completing a bounded task, although `main` has no branch protection/rulesets and both associated implementation PRs are closed unmerged. Clarifying comments now allow one worker to complete scoped testing and an independent raw audit, while preserving actual permissions and integration checks. A third comment on #6957 clarifies that its coordination record does not freeze disjoint work. No Issue status, PR, or experiment changed. B12 is next.

### B12 bounded intake — control methods, human-facing proposals, and environment holds

The [B12 receipt](maintenance/issue-discovery-b12-20261019.md) routes rows 276–300 and adds one direct entry for #7705; the other 24 ideas already had curated entries. It preserves finite method results, source/build STOPs, open Draft evidence, and the #7430 no-WSLc-owner restriction. Merged package validation remains distinct from user benefit, live GUI transfer, or a fresh resource allocation. B13 is next; no experiment or Issue state changed.

### B13 bounded intake — effect, recovery, and resource-ownership evidence

The [B13 receipt](maintenance/issue-discovery-b13-20261019.md) routes rows 301–325 and adds the missing #7889 direct summary while preserving the canonical T0 failure, the later local duplicate attempt, and its incomplete audit. It also keeps #7921's wrong-input STOP and #7924's explicit WSLc ownership hold intact; no runtime command was issued. Merged results remain method-scoped; open Drafts are visible in the receipt. No Issue state or allocation changed. B14 is next.

### B14 bounded intake — observations, recovery, and runtime eligibility

The [B14 receipt](maintenance/issue-discovery-b14-20261019.md) routes rows 326–350; all 25 entries already had curated outcome rows. It preserves separate MAP01 chronology auditor STOPs, finite decision-value and scheduling results, duplicate-attempt ownership corrections, and the no-WSLc ownership gate at #7970. The linked Drafts remain explicit; no runtime query or allocation was made.

### B15 bounded intake — retained method outcomes and runtime gaps

The [B15 receipt](maintenance/issue-discovery-b15-20261019.md) routes rows 351–375; all 25 entries already existed in the curated outcome index. It preserves non-conclusive and synthetic-only outcomes separately from live runtime questions, records duplicate-allocation and auditor stops without promoting their payloads, and keeps #8252's remaining text-prefix counterexample visible. Referenced PRs were checked for merged, open-Draft and closed-unmerged distinctions. No Issue, PR, raw packet, allocation, or WSLc status changed. B16 is next.

### B16 bounded intake — finite models, audit stops, and runtime limits

The [B16 receipt](maintenance/issue-discovery-b16-20261019.md) routes rows 376–400; all 25 entries already had curated outcome rows. It separates finite-method results from candidate/auditor failures, duplicate allocation, unverified proposals, and live recovery limits. It records WSLc construction replay only as post-result construction evidence and preserves #8562's explicit #7924 ownership hold; no runtime operation was made. Referenced PR state was checked, without changing Issue/PR status or allocation. B17 is next.

### B17 bounded intake — evidence custody and independent result limits

The [B17 receipt](maintenance/issue-discovery-b17-20261019.md) routes rows 401–425; all 25 entries already had curated outcome rows. It records review-discovered method-gate and freeze issues even where a PR later merged, and separates integrated evidence custody from a successful candidate result. It preserves the #7924 resource conflict at #8604, the recorded prior WSLc invocation at #8619, and the concurrent-allocation collision at #8624; no WSLc command, allocation, or Issue/PR status change occurred in this intake. B18 is next.

### B18 bounded intake — workflow custody and scoped results

The [B18 receipt](maintenance/issue-discovery-b18-20261019.md) routes rows 426–450; all 25 entries already had curated outcome rows. It captures PR-state corrections for linked evidence, retains the nonpositive method results and custody limits, and separates WSL3 readiness policy from authorization to use a specific WSLc allocation. No Issue/PR state, experiment allocation, or WSLc state changed during intake. B19 is next.

### B19 bounded intake — recent proposals, literature scope, and preserved failures

The [B19 receipt](maintenance/issue-discovery-b19-20261019.md) routes rows 451–475; all 25 already had curated outcome entries. It keeps comment-free proposals unclassified, narrows novelty claims using the cited literature, preserves #8888's implementation-audit STOP, and distinguishes #8902's transition/occupancy estimand from #8068's recovery-history estimand. No Issue/PR state, experiment, or WSLc allocation changed. B20 is next.

### B20 bounded intake — final r51 navigation slice

The [B20 receipt](maintenance/issue-discovery-b20-20261019.md) routes the final 16 rows (476–491); all have existing curated outcome entries. The full immutable r51 queue is now routed: 20 batches cover 491 items, with 25 each in B01–B19 and 16 in B20. This closes the queue-routing task only. It does not semantically resolve the 491 items, refresh the historical 1,675-Issue/503-PR inventory, or authorize closing proposals. #8913's read-only WSLc calls remain a recorded process deviation under an unresolved ownership gate, and #9004's integrated synthetic result remains `NO_INCREMENTAL_AGREEMENT_VALUE`. Next, refresh the live Issue/PR inventory and reconcile current families, open PR dispositions, and worktree owners.

### r52 live inventory and exact cross-index coverage — 2026-10-19

The [r52 snapshot](maintenance/repository-inventory-20261019-r52.md) refreshes membership after PR #9131: 1,673 open Issues and 503 open PRs. Compared with immutable r51, #104 closed with `HOLD_GRID_TOO_COARSE` still intact, and #1798 closed with its scoped durability request complete while #1769 remains open. The [r52 coverage audit](maintenance/idea-index-coverage-20261019-r52.md) confirms 1,184 open Issues have a primary row in the historical research selection and 489 do not; those 489 are exactly the remaining r51 queue items. Eight Issues absent from both indexes now have routing-only links, and the union of the research index and idea-index issue links covers all 1,673 open Issues. This is route coverage, not semantic resolution or a basis for mass closure.

The [r02 worktree custody audit](maintenance/git-worktree-custody-recheck-20261019-r02.md) found 12 registered worktrees including this main checkout. A clean detached #7370 review tree exactly matches a merged PR and is a strong cleanup candidate, but its owner is not known; retain it pending owner confirmation. Other checkouts have raw logs, unique committed tests, untracked profiles, or unresolved ownership. No branch or worktree was deleted. Next: establish owner-approved recovery for the #7370 checkout and build an exact-head inventory/individual disposition queue for the 503 open PRs; preserve open PRs with unique work or evidence until their actual owner and dependency are resolved.

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

The 2026-10-20 read-only crosswalk is recorded in
[the family disposition receipt](maintenance/issue-family-disposition-visual-multiview-20261020.md)
and the [visual-interface family record](ideas/visual-interface.md). It found
that #1981's formal/audit pass is narrower than #1946's full fixture gate, while
#1983's broader 24-row result is `HOLD_NO_FORMAL_CONTAINER`; therefore #1946
stays open pending a full eligible container-backed run and independent audit.
#2031's `1/8` per-arm score is invalid as pure accuracy because of the response
schema/scorer mismatch; its auditor-cap deviation and 113/114 manifest match
remain explicit. No old call, audit, or allocation was repeated. Next for #7:
preregister the fixed-budget held-out set comparison only after fixing its
independent task oracle and response schema. Keep #7's selection question
separate from #8's encoding comparison and #4's broader thesis.

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

**2026-10-19 r74 — current membership and #17 offline discriminator:** A fresh complete paginated read at main `289a0c19ab85581cb3414b01d92f2f887ae0c60b` found 1,673 open Issues and 502 open PRs. Sorted ID-set hashes exactly match r53; see [r54](maintenance/repository-inventory-recheck-20261019-r54.md). No redundant metadata export or Issue/PR state change was made. For #17, a deterministic offline framing model reproduced that the frozen A03 broad predicate would select a same-PID pre-press identity reply, and a connection-plus-sequence-plus-action policy model passed 7/7 tests in normal and optimized Python. The additive packet is [here](../research/integration/offline_proxy_reply_framing_20261019/README.md). This does not identify A03's actual held reply, establish blocked-I/O release, or change the immutable A02/A03 outcomes. No allocation, WSLc, Docker, GUI, or live X server was used; #17 remains open with release/task `UNKNOWN`. Next: inspect whether a real proxy/caller trace can bind reply connection, sequence, request role, peer PID and KeyPress action before considering a new live run. Whole-repository semantic Issue/PR classification and worktree custody remain incomplete; preserve evidence and decide each family item individually rather than bulk-closing ideas.


**2026-10-19 r75 — #17 source-call-chain crosswalk and reply target:** Current bridge/backend source plus the frozen A03 `python-xlib==0.33` pin establish the candidate ordering: the guarded press rechecks process identity through a TargetQueryWorker thread that opens a separate X connection in the same owner PID; input then sends XTEST `FakeInput(KeyPress)` and `Display.sync()` waits for `GetPointerControl` (core opcode `106`). A03's client relay forwards requests opaquely and its server relay gates every type-1 owner-PID reply, so it cannot isolate that reply. The [offline model packet](../research/integration/offline_proxy_reply_framing_20261019/README.md) now classifies these request frames, associates only the immediately following sync on the input connection, and passes 8/8 tests in normal and optimized Python; the same-PID identity reply with a colliding sequence is forwarded. This source crosswalk supports the circular-gate explanation but cannot identify the missing A03 reply sequence or retroactively change its first failure. No WSLc, Docker, live X server, GUI, or OS input was used. Issue #17 remains open and release/task remain UNKNOWN. Issue #7924 still reports STOP / HOLD for WSLc client ownership (latest update 2026-10-12); no fresh unused allocation was verified. Next: implement and offline-test a new proxy candidate that records connection IDs, per-connection requests, XTEST QueryExtension negotiation, and the action/keycode-bound GetPointerControl reply; only then consider a new live candidate on a verified unused allocation. Repository-wide semantic Issue/PR classification remains incomplete; retain ideas and outcomes rather than bulk-closing.

**2026-10-19 r76 — offline stream-parser candidate and post-merge membership:** PR #9135 merged the X11 source crosswalk and first connection/sequence/action model; its post-merge full membership read [r56](maintenance/repository-inventory-recheck-20261019-r56.md) matches r53 exactly. The additive [proxy candidate parser](../research/integration/offline_proxy_reply_framing_20261019/proxy_candidate.py) now parses fragmented X11 setup/request/reply streams, negotiates per-connection XTEST opcode, and selects only the action/keycode-bound GetPointerControl after an independent receipt is supplied. Its 19 normal and 19 optimized tests cover same-PID sequence collisions, endianness, fragmentation, mismatched receipt, malformed framing, and fail-open sequence ambiguity. This is a parser candidate only: no socket relay, X server, GUI, OS input, WSLc, or Docker was used. A02/A03 remain immutable; their first outcomes and UNKNOWN release/task are unchanged. #7924 remains STOP/HOLD. Next: connect the parser to an isolated fake-upstream socket relay; bound buffer growth, disconnect, EOF, relay backpressure and owner-retirement behavior before any live allocation. The whole-repository semantic Issue/PR disposition remains incomplete; keep idea families and outcomes distinct.

**Follow-up to r76:** the parser-to-fake-relay/caller step was later merged in PRs #9136 and #9153. See the current r77 update below and the linked Fake X test packet; this supersedes only that historical next-step statement. The original r76 result and boundaries remain unchanged.


## 実行状況 r05 — #8879 A01の失敗証拠を保全してr60基準線へ

PR [#8892](https://github.com/Unjuno/agent-interface/pull/8892)のexact head `60e1c8de887708da0ab432c46b017eaead15a9c2`を確認し、READMEが「未実行」と書いている一方でDISPOSITION/resultは初回の`FAIL_AUDIT_CONSTRUCTION`を記録している不整合を発見した。candidate/auditorはどちらも同じhistory-containment predicateを逆向きに使い、planted violationを見落としたため、auditorはassertでexit 1となった。再実行せず、READMEを初回失敗とno-retryに整合させた更新head `da3b91e142030cc0592f6f35617f3e2130cbaf50`でReady化し、analysis-index/replay-gate pass後、2026-10-19 02:58:08 UTCにmergeした（`24f84931b6f4a5efce82888703dda21e8e74994c`）。これは失敗証拠の保全で、method PASSでも科学的支持でもない。#8879はOPENのまま。canonical idea pageとoutcome indexに失敗、境界、新allocation+independent oracleという次条件を記録した。

r60はopen Issue 1,673件、open PR 498件。CSVは1,673/498行、sorted-ID hashesはそれぞれ`4ca4576b8a328d9f41b862a3c7ad3793edd9ddd085bb127d708796e9b6082dd6`と`ee48b38748932af291a16c7337dff39a6095cd332a922dadb2e612a8dd96dc29`。Issue集合はr59と同一、PR集合は#8892だけ減少した。依然として数百PRと1,673 Issueの意味・依存・所有・処置が未完了であり、repository-wide clean完了ではない。


## 実行状況 r06 — WSLc process-deviation recordの区別とr61基準線

PR [#8906](https://github.com/Unjuno/agent-interface/pull/8906)は一つのREADMEのみを追加し、明示的なowner releaseなしに実施された一回限りのWSLc CLI smokeとglobal container inventoryをprocess deviationとして開示する。READMEはcached image、exact command、成功marker/exit、cgroup/swap warning、Ubuntu起動失敗、4個の既存停止container、owner-scoped cleanup不在を記録し、performance/memory/parityの主張を避けている。既存replay-gate成功を確認し、追加WSLc操作をせず、2026-10-19 03:03:09 UTCにmergeした（`38f27e2dcaf3bd9f665ff1fa4f91cc17c983ec9f`）。これは既存gate違反の履歴を保全するもので、現在のlane releaseではない。#8685はOPENのまま。read-only callsの#8913とは別の実行であり、#8913もOPEN。

r61はopen Issue 1,673件、open PR 497件。CSVは1,673/497行、sorted-ID hashesは`4ca4576b8a328d9f41b862a3c7ad3793edd9ddd085bb127d708796e9b6082dd6`と`03bd6c9ef402dd4670557cf3217c780fc945d13e7b0fa5030b9f794adc4cbe93`。Issue集合はr60から不変、PR集合は#8906だけ減少した。残るIssue/PRのsemantic triage、dependency、custody、個別dispositionは未完了であり、repository-wide clean完了ではない。

## 実行状況 r07 — current inventory、PR batch、#8687証拠custody

[r62 inventory](maintenance/repository-inventory-20261019-r62.md)を2026-10-19 03:21:18 UTCにmain `3cf520498beb886750b9de8499890dfebb0ea209`で取得した。open Issue 1,673件・PR 497件でr61からID集合の増減はない。PR head/base metadataを再取得したが、これは内容・所有者の意味判定ではない。

[直近PR batch監査](maintenance/recent-pr-triage-20261019-r01.md)の15件をlive stateに照合し、6件がmerge済み、9件がopenと確認した。openのうち#8701はtested-stack/head照合、#8678は有限STOP記録、#9006はnative-win32失敗とfixture修正、#8842/#8756はconflict解消、#8855/#8849/#8861は作者がdraft解除前に範囲と根拠を補う必要がある。#8687は#8771へ重複実装を入れず、証拠PRとして保全判定を続ける。

Issue #8681は閉鎖済みで、その実装PR #8771もmerge済みだが、#8687 head `6195600931fa6de4ecf1a5012cb83b549addb5af`のA02–A05資料47ファイルはmain treeにないことを直接比較で再確認した。これらは同PR headに存在し、複製・変更・再実行はしていない。#8687を閉じる前に、凍結パッケージだけでなく、各freezeが参照するsource/test blobの再構成可能性を含む正規保全先を作る。担当不明のPRを自動でcloseせず、次の整理作業はこの証拠専用移管の固定範囲を策定すること。

Issue/PR全体の意味分類、担当・PR・branch/worktree間のlineage、未追跡証拠のcustodyは未完了。全件closeや全PR mergeを完了条件にせず、familyごとに再開可能なアイデアと証拠をつないで継続する。

## 実行状況 r08 — #8687 A02–A05証拠のbyte-preserving rescue

PR #8687のコード差分を再適用せず、A02–A05の47ファイルをそのまま取得し、原freezeが参照するsource/test blob 2件も別ディレクトリへsnapshotした。各packageのSHA256SUMS 51エントリすべてが一致し、source snapshotは元PR head `6195600931fa6de4ecf1a5012cb83b549addb5af`のblob ID・byte長・SHA-256に束縛される。candidate/auditor/testは実行していない。

これはmainへの統合前の保存候補であり、#8687を閉じる根拠はまだ満たさない。証拠専用PRを検証・統合した後、current mainで47ファイルと2 source snapshotを読み戻し、#8687の重複実装以外に未移管の固有差分がないことを確認してから、closeとremote-ref処置を別々に判断する。#8838、他のPR、Issueの状態は変更しない。

## 実行状況 r09 — #8687 custody complete、current inventory r63

PR [#9142](https://github.com/Unjuno/agent-interface/pull/9142)はmain `9ad2614e8ad329e2aaa90487c28859718f84f647`にmergeされた。A02–A05の47ファイルとsource/test snapshot 2件はmain上にあり、main treeと保存済み検証commitのパス差分は0。元manifest 51項目はmerge前にすべて一致した。#8687の残る2つの実装/テスト変更は、main #8771のより強いduplicate/invalid/mismatched identity拒否と同等以上のfocused test coverageであることを差分・テスト名・27件のnormal/-O実行で確認し、#8687をsupersededとしてcloseした。作者・open-PR依存・登録worktreeを確認した後、保全済みの元branchも削除した。#8838は別のA07証拠としてopenのまま。

PR #8687のclose後に[r63 inventory](maintenance/repository-inventory-20261019-r63.md)を取得した。Issue 1,673件はr62と同じ、PRは497から496へ減り、取り除かれたIDは#8687だけ。これは一つの証拠custody/duplicate-implementation familyの完了であり、残るopen Issue/PRの全件意味分類や全体整理完了を意味しない。


## 実行状況 r10 — #8838 evidence custody、r64 inventory

PR [#9144](https://github.com/Unjuno/agent-interface/pull/9144)を2026-10-19 03:44:32 UTCにmainへsquash mergeした。#8838 head `810fdcfe558ad700f779aaa66c111a4cc19eb9e4`のA06/A07資料32ファイルを原パスのまま移し、SHA256 manifest 30項目と32 Git blobすべてを移管前に照合した。merge後も32 blob全てが原headと一致することを読み戻した。候補、runner、auditor、テスト、allocationは再実行していない。

#8838はparent #8681が閉じ、実装#8771が統合済みで、diff全体が上記証拠資料だけだった。作者は認証済みrepository ownerと一致し、他のopen PRのhead/base依存と登録worktreeがないことを確認後、03:45:47 UTCにsupersededとしてcloseし、remote branchも削除した。A06は有限alphabet/length内のparser結果、A07は歴史的sourceへのfocused testsである。A07はWSLc実行前のmount失敗後、resource confinementなしのUbuntu WSLへ移った。いずれも物理release、GUI/game、effect、bounded recovery、live controlを証明しない。詳細は[custody review](maintenance/pr8838-evidence-custody-20261019.md)と[cleanup identity audit](ideas/cleanup-identity-audit.md)。

[r64 inventory](maintenance/repository-inventory-20261019-r64.md)をmain `f5b164f3baccf8e7b0e593c5e90739cb667cdc72`から2026-10-19 03:47:14 UTCに取得した。open Issueは1,673件でr63からID集合不変（SHA-256 `4ca4576b8a328d9f41b862a3c7ad3793edd9ddd085bb127d708796e9b6082dd6`）。open PRは496から495へ1件減少し、除かれた唯一のIDは#8838（SHA-256 `1260dc6655c85bf66a296311df39ea33a970de8bee5badda1c2a168027a0b472`）。これはcleanup-identity evidence custodyの一区切りで、リポジトリ全体のIssue/PR semantic triage、依存・担当・worktree custody完了ではない。次は既存のPR batchとアイデアfamilyごとに、実装重複・独自証拠・未完了の科学的問いを分けて分類する。


## 実行状況 r11 — #8678 A01/A02 tracked custody、r65 inventory

PR [#9146](https://github.com/Unjuno/agent-interface/pull/9146)を2026-10-19 03:55 UTCにmainへsquash mergeし、#8678 head `7551424026375469f609754140250f89bf09cad4`の全29 Git-trackedファイルをそのまま保全した。merge後、main SHA `69deb9e40aaa5104b2c57f12acc0577874593399`の29 blob全てを元headと比較した。#8678のA01はmodel/game前のPRELAUNCH_STOP、A02は四turn後のcleanup terminal failure。空keymap報告だけではrelease/cleanup完了とせず、hard guard、bounded recovery、task successも主張しない。候補、audit、test、model、game、allocationは再実行していない。

#8678のSHA256 manifestは976項目のignored output bundleを指すが、PR本文記載の`results-local/doom/map01-v39-live-threat-guard-a02-20261009/`はcurrent checkoutと登録15 worktree rootで見つからなかった。このホスト範囲で完全raw image custodyを確認できず、移管はtracked diffに限定する。この制約をclosure commentにも残した。作者は認証済みrepository owner、他のopen PR head/base依存とregistered worktreeなしを確認後、#8678をcloseし、remote branchを削除した。#8701のA03–A07は別allocationであり統合・終了していない。Issue #59はopenのまま。親Issueには[comment #6259320132](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-6259320132)で今回の限定結果とraw-custody gapを記録した。詳細は[MAP01 evidence-family index](ideas/map01-live-guard-evidence-family.md)と[custody review](maintenance/pr8678-evidence-custody-20261019.md)。

[r65 inventory](maintenance/repository-inventory-20261019-r65.md)はmain `69deb9e40aaa5104b2c57f12acc0577874593399`を2026-10-19 03:56:42 UTCに取得した。open Issue 1,673件はr64とID集合不変（SHA-256 `4ca4576b8a328d9f41b862a3c7ad3793edd9ddd085bb127d708796e9b6082dd6`）。open PRは494件でr64から#8678だけが減少（SHA-256 `a8c6ffbcbd8cf1bbda094c07a47a1ee9ae966d87c92955c8fe03d17fad7977e6`）。これは一つの#59 tracked-evidence/branch loopの整理であり、外部raw出力custodyまたはリポジトリ全体のIssue/PR意味分類完了ではない。次はMAP01の#8701および他allocationを結果・audit・custody単位で個別に見て、現在の科学的問いを変える独自証拠を残す。


## 実行状況 r12 — #8701 A03–A07 tracked custody、r66 inventory

PR [#9148](https://github.com/Unjuno/agent-interface/pull/9148)を2026-10-19 04:03:53 UTCにmainへsquash mergeした。#8701 exact head `44f15471bd07705f1bbe565c017b6f9df29e87ec`のA03–A07研究ファイル41件は、main `38845fc83b698f26051477280eb14937b1907315`で全blob一致を確認した。原PRのA09向け`CURRENT_GOAL.md`差分は別allocation #8749の索引済み要約であり、今回のA03–A07 packetには含めず、#8749は既に別PRとしてmerge済みだった。#8701作者、open-PR head/base依存、worktreeを確認後、04:04:58 UTCにtracked packetをsupersededとしてcloseし、remote branchを削除した。

A03–A06は各一回限りのsetup STOP。A07は10 turnのHOLDでhard-health guard/useful scorer条件が発生せず、MAP01 exitなし。v1 FAIL、v2 reconciliation、v3 explicit-transition FAIL、および別系統の`PASS_CUSTODY_RECONCILED_SCOPED`は区別して保持する。custody結果は`formal_pass=false`で、物理key/game effectの証明ではない。PR本文が記す2,358件ignored raw-output bundleはcurrent checkout/登録15 worktreeに存在せず、この移管はtracked 41 filesに限る。Issue #59には[comment #6259414298](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-6259414298)で限定結果とcustody gapを記録し、parentはopenのまま維持する。詳細は[MAP01 index](ideas/map01-live-guard-evidence-family.md)と[custody review](maintenance/pr8701-evidence-custody-20261019.md)。候補/監査/テスト/VM/model/game/allocationは再実行していない。

[r66 inventory](maintenance/repository-inventory-20261019-r66.md)はmain `38845fc83b698f26051477280eb14937b1907315`を2026-10-19 04:06:00 UTCに取得した。open Issueは1,673件でr65からID集合不変（SHA-256 `4ca4576b8a328d9f41b862a3c7ad3793edd9ddd085bb127d708796e9b6082dd6`）。open PRは493件、r65から除かれた唯一IDは#8701（SHA-256 `ca67ca92b1afd8f0b0e75eece8f238afb65b6bd9a3b76f10c700d8cd85c39924`）。これで#59のA01/A02、A03–A07 tracked custody loopをmainに接続したが、各ignored raw bundleは未解決、Issue #59はlive-control gateが未解決のためopenである。次のfamily itemも、各allocationの停止/失敗/限定PASS、独自raw、branch lineageを照合してから個別に処置する。

## 実行状況 r13 — A11 packet integrated

PR [#8782](https://github.com/Unjuno/agent-interface/pull/8782) was squash-merged at `65f3dd3f7aea88af7c249d58f430e72e83a3c92e` on 2026-10-19 04:11:07 UTC. Its 20-file sanitized A11 packet is now on main. The original audit remains FAIL and the allocation remains HOLD; all 32 cancellations are accounted in the additive reconciliation, but the joint live-control gate was unobserved and the episode did not exit MAP01. Public files omit raw transient intent tokens/per-key identities, and the full raw bundle remains local. We did not rerun the allocation. Sixteen portable local tests passed; one host-mount-path assertion is specific to the original POSIX `results-local/doom/a11-source` fixture and did not apply in this Windows checkout. The repository replay-gate was already green on the PR. This packet integration does not close Issue #59.

## 実行状況 r14 — A13 delay evidence integrated、r68 inventory

PR [#8790](https://github.com/Unjuno/agent-interface/pull/8790) was squash-merged at `20a17d8b99879f7804a679d2dc2927d5e6b4cb3a` on 2026-10-19 04:14:58 UTC. All 23 A12/A13 paths matched the original PR-head blobs on main. A13 remains HOLD: the one-second relay delay did not place a useful scorer event inside the controller interval, and no MAP01 exit occurred. The independent packet reports 11/11 cancellations accounted and 35/35 per-key release receipts matched; the original audit remains retained. A12 is a prelaunch STOP. Raw requests/responses and images remain local and were not re-read; no allocation was rerun. The PR replay-gate passed, and 26/27 local tests passed on this Windows checkout; the remaining exact source-mount assertion requires the original POSIX fixture path.

The [r68 inventory](maintenance/repository-inventory-20261019-r68.md) captures main `20a17d8b99879f7804a679d2dc2927d5e6b4cb3a` with 1,673 open Issues and 491 open PRs. The Issue ID set is unchanged from r66; #8782 and #8790 are the only PR removals. Complete metadata is preserved in the [Issue CSV](maintenance/open-issues-20261019-r68.csv) and [PR CSV](maintenance/open-prs-20261019-r68.csv). This remains a membership snapshot, not repository-wide semantic triage.

## 実行更新 r72 — membershipをr69へ更新、#6/#56の処置を再確認

2026-10-19 04:50:37 UTCにGitHub CLIでopen Issue/PR一覧を全ページ取得し、main `e60a7829602212442055f9f7e4e3cec594f85880`にIssue 1,673件・PR 489件を確認した。Issue ID集合はr68と同一、PR集合からは統合済み#8849/#8855だけが抜けている。set hashと取得方法は[r69 recheck](maintenance/repository-inventory-recheck-20261019-r69.md)に記録した。これはmembershipの再確認であり、PR head/base metadata、意味分類、担当、worktree custodyを一括更新したものではない。

live Issue body/commentsを再読した#6はreactive local-controlの広い研究メニュー、#56はplanner-authored symbolic interfaceのcold/warm/repair仮説として区別が保たれている。#56のA05 full-gate failure、R02 REJECT、A12–A14 construction-only結果とA14のblank-image grounding反例は既存[family entry](ideas/reactive-macro-symbolic-interface.md)に記録済みで、今回の確認でも訂正は要らなかった。#7616はmainに統合済みのretained FAILで、候補は再実行しない。#6/#56はいずれもopenで、PR #7353は既にmerged。未解決の科学的問いに対する根拠ある完了・棄却はなく、Issueは閉じない。次はこのfamilyの同じ記録を複製せず、別の未分類familyまたはexact-head PRを一件選び、実行作業へ戻る。

## 実行更新 r73 — 最新のopen PR head/base metadataを保存

2026-10-19 05:13:23 UTCに全ページを再取得し、main `e83e52dc0eda4c3ebc5f54f676971ce9e71a6006`で1,673 open Issues、489 open PRsを確認した。[r70 inventory](maintenance/repository-inventory-20261019-r70.md)は完全なIssue metadataとPR author/head SHA/base/reviewer metadataを保存し、SHA-256を記録する。Issue membershipはr69と同じで、r15からは#104/#1798がopenでなく、Issue追加はない。PR membershipもr69と同じで、r15からopenでなくなった25件に追加はない。これは最新membership/metadata baselineであって、全件の意味分類・所有確認・PR統合可否ではない。Idea-index gapの測定はr52の489件を維持し、全件意味分類の代わりに使わない。次はr52 batch receiptsから1 familyをcurrent Issue/PR/source/evidenceと照合し、固有の仮説・残差・所有・次の作業を家族記録に反映する。Issue/PRの状態は完了、根拠付き棄却、または実在する後継への移管を確認した個別項目だけ変更する。

## 実行更新 r74 — 入口の整合とworktree custody棚卸し

2026-10-19 05:27:38 UTCの完全なGitHub REST読み取りは、現在main `95386ee7e10e7ffc7422bd473f4db29991bd28b6`でopen Issue 1,673件・open PR 489件を返した。ID集合とr70の全取得metadata（Issue title/update/labels/assignee、PR title/update/head ref/head SHA/base ref/labels/assignee/reviewer request）を比較し、差分は0件だった。時刻書式とBoolean casingは同じ値として正規化した。#9154後にmain SHAは進んだが、PR metadata一覧の変化はなかったためr71 CSVは重複作成しない。この独立再確認は意味分類・現担当・PR差分レビューを置き換えない。

同時に`git worktree list`と各treeの通常`git status --porcelain --untracked-files=all`を読み取り専用で照合し、16件のregistered worktree、11 clean、5 changed（合計152 status entries、うち102 untracked）を[worktree custody recheck r03](maintenance/git-worktree-custody-recheck-20261019-r03.md)へ記録した。r70 open-PR head refsと比較したところ、13件のchecked-out local branch名に完全一致はなく、残る3件はdetached HEADだった。これは未使用・所有者不明・削除可能を示さない。ignoredファイル、process/session、PR base依存、実所有者は調べておらず、refやworktreeは削除していない。次はr03のdirty/unknown行を既存Issue/PR/worker-sessionへ一つずつ結び、cleanなtreeもmainへの固有成果とdependentsを確認してから候補を分類する。

同時点のopen PR再確認では、直前の15-PR triage batchの未終了項目が#9006/#8842/#8756/#8861の4件と判明した。#8849と#8855はmerge済み、#8687/#8678/#8701はそれぞれ#9142/#9146/#9148で証拠を保全してからsupersededとしてclose済み。別件#8838も#9144がA06/A07 packetを正確に保存し、依存worktree確認後にclose済みである。次は残る4 PRを同じ一括処置へ送らず、exact headとローカル検証を一件ずつ確認する。

## 実行更新 r75 — 現行入口と3つの独立worker packet

PR #9155は文書差分のローカル検証後、作成時に記録したmain SHAをfirst parentとする通常のmerge commitで統合され、mainは`5efe7301f6e655a41c4653b3c6baf45138ca72f6`になった。PR checksのreplay-gateとpublic-navigationは成功し、formalはこの文書差分に適用されずskipだった。統合後のGraphQL count readはopen Issue 1,673件・open PR 489件を返す。これはcounts-onlyであり、r70の完全row-level snapshotを更新するmetadata取得ではない。

大量workerが同じ共有索引を競合編集しないよう、#17（解放/安全制御）、#5（target binding/visual feedback）、#59（MAP01/A07 custody）の非重複3件を[dispatch packet r01](maintenance/worker-dispatch-20261019-r01.md)として作成した。各packetは別の出力先、根拠・限界・owner/resource unknownの記録形式、Issue/PR/worktree/実験状態を変えない制約を持つ。これは割当やresource grantではなく着手可能な読み取り仕事である。共有の`WORKER_WORK_MAP`、`IDEAS_AND_OUTCOMES`、family agendaと本計画は一人のintegratorがpacket確認後に直列更新する。

packet選定の現況はread-only監査による。#17ではPR #9153までFake X標準callerのbounded local return/child retirementが構成検証されたが、releaseはUNKNOWN、task successはnullであり、実X server/OS key-upは未検証。A11のXvfb結果は別topologyで、再利用allocationsではない。#5では#9099がprivate-Xvfb上で標準caller、合成targetの独立property effect、release readbackを一つの限定結果として示すため、過去の“Fake X only”記述は更新対象だが、product-app semantics、native desktop/XWayland、atomic check/use、task completionは残る。#59のPacket Cは[独立A07 custody cross-check](maintenance/issue-59-a07-custody-audit-20261019-r01.md)として完了した。#8702の四つの追跡ファイルchecksumとraw-manifest digestの一致を確認したが、manifest本体・event streamを追跡済みソースから再検証できないためevidence-custody holdを維持し、PR #8702とIssue #59はopenのまま、A07再実行もしない。owner reconciliationはX11 server-side receiptの範囲に限り、physical key stateやgame effectを示さない。

次は#5の限定Xvfb実証をfamily入口に反映し、#17のstandard-caller/held-input境界を既存根拠から照合する。#59はA07のcustody差分を記録済みで、再開条件は未入手raw一式を変更せず読み取り専用で受領し、checksumと監査を再現できること。各結果を新規researchやIssue closureへ進めるのは、その結果が状態・所有・必要資源を実際に変えると分かった後とする。r70 metadataは不変の完全snapshotとして保ち、membershipの再読だけを理由に新CSVを増やさない。

## 実行更新 r77 — アイデアをファミリーで動かし、IssueとPRを個別に収束する

2026-10-19 05:59 UTCのmainは`168200eb43dd0f9144b3ed4aef551387674c7bfd`
（PR #9156統合後）。counts-onlyのGraphQL確認はopen Issue 1,673件・open
PR 489件を返した。これはr70の完全metadata inventoryを置き換えず、意味分類、担当確認、差分レビュー完了の証拠にもならない。r70/r74の行単位記録は不変の基準として使い、今後の更新では変化した範囲のみを再取得する。

整理の対象は件数ではなく、次の研究判断にたどり着けないこと、重複work、古い入口、担当・証拠保存先・依存が見えないこととする。アイデアは反証可能な問いごとに既存の`docs/ideas/` familyへまとめ、同居する別仮説・反例・失敗は統合せず明記する。各familyには出典Issue、実装とPR、保持結果/rawへの参照、結果の限界、依存と競合範囲、状態（未検証/実行可能/進行中/結果保持/理由付き保留/根拠付き棄却/移管済み）、一つの有限な次の識別作業と、それが変える設計判断を持たせる。優先順位は、残差の重大さ・単純な比較対象・実行前提・他作業を unblock する効果から決める。未確認owner/resourceは`unknown`として、openまたはunclassified queueに残す。

Issueは内容別に処置する。未解決の親研究目標・実行中allocation・task/evidence/owner gapはopenを保つ。達成したscoped contractはそのscopeと証拠リンクを明示して閉じ、広い親目標を別に保つ。重複は独自仮説・結果・失敗・rawをcanonical family/後継へ先に移し、source/backlinkと移管理由を書いた後でのみ閉じる。実験前提がなく保留するアイデアも、canonical familyに提案・保留理由・再開条件・sourceを残してから個別に整理する。大量closeを先に行って後でアイデアを拾う手順は取らない。

PRは一件ごとに正確なhead/base、mainとの差分、stack依存、作者、ローカル検証、固有証拠とrawの保全先を見て、merge・修理継続・内容移管後のclose・根拠付きreject・owner確認待ちに分ける。branch/worktreeはPR stateから削除可否を推定しない。tip、dirty/untracked/ignored data、active user/process、dependents、回復可能な保存先を照合してから対象を回収する。

大量worker向けの標準分割は「別research family + 別コード範囲 + 別additive出力先」。一つのpacketには出典と参照SHA、問い、再利用可能な結果と限界、owner/dependency/resource境界、許される変更、有限のacceptance/stop conditionを書く。family index・`IDEAS_AND_OUTCOMES`・work map・本計画の編集はintegrator一人が直列化し、それ以外の独立調査と実験は並列化する。issue discoveryのnumber-batchesは取りこぼし防止の手段であり、優先順位やsemantic familyを意味しない。

今回の最初の実行は#17の限定Fake X seam: [late-down-after-release packet](../research/integration/standard_caller_fake_x_relay_20261019/late-down-after-release-counterexample-20261019-r01/README.md)。standard callerが合成queue上の遅延KeyPress後もUNKNOWN/unconfirmedを保つことをnormal/-Oで確認した。timestamp同値の初回失敗もrawに保存した。これは保全付きの一つの研究結果で、X server ordering、物理key-up、task effect、WSLc allocationを証明しない。#17はこの結果で解決した扱いにせず、既存familyへ取り込んだ上で、次はserver-side queue orderingを観測できる許可済み環境の準備条件を特定する。#5と#59の別familyは各自の現行証拠と所有状況を再確認してからwork packetにする。

Repository cleanの完了条件は、各active familyの問い・根拠・限界・次の決定が一か所から辿れ、各open Issue/PRの処置先が個別に分かれ、未分類分が明示的な残作業キューにあること。open Issue/PRがゼロである必要はない。次回はfamily indexを二重作成せず、現在のMAP01、#57統合比較、標準caller安全境界のうち一つのdistinct familyを進め、共有索引はこの分割に沿って一度だけ更新する。

## 実行更新 r78 — #5 Fake X check/use counterexampleを保存

PR #9158統合後のmain `0bc669bcad494da450dc36a3d9a5122648db3dfb`から、視覚target family #5の次の有限な識別作業を実行した。[packet](../research/integration/fake_x_window_lifecycle_check_use_20261019/README.md)はFake X標準MCP caller内で、最後のローカルpress checkとrelease obligationのprearm後、最初のXTEST press前にDestroyNotifyを入れ、独立lifecycle queryが先にそれを処理してreaderをretireする順序を構成した。通常/-Oの両方でreader retirement後に一つのKeyPressがemittedされ、その後続pressは拒否された。callerは`execution_failed`、review required、replay denied、`task_success=null`で終わり、Fake X上のprefix release/readbackはverified、down集合は空だった。raw、条件、機械可読receiptとSHA-256 manifestを保存した。ライフサイクルcaller moduleは通常/-Oで各16/16成功。

この結果は構成scheduleにおけるcheck/use raceのcounterexampleであり、X serverの実順序、物理release、アプリ効果やtask successを示さない。Issue #5はopenのまま。次は既存lifecycle契約でordered admission fenceを作れるか、blocked Xlib I/Oを待ってreleaseを遅らせない条件を含めsource/design auditする。リポジトリ全体ではr70/r74が最新の完全metadata基準、open Issue 1,673件・open PR 489件は旧main `168200...`時点のcounts-only baselineであり、全件意味整理・PR収束・worktree custodyは未完了である。保存済み研究項目を消さず、familyごとに処置と有限な次作業を積み重ねる。

## 実行更新 r79 — same-PID identity/input relayを別接続で識別

main `0ded57765d6de80f2c42370a5f1e6454f4959496`のソースを使い、A02/A03を再生せず、既存offline framing candidateへ[test-only two-connection relay discriminator](../research/integration/offline_proxy_reply_framing_20261019/two-connection-r01/README.md)を追加した。identity/inputに別々のsocketpair relayと同じmodeled owner PIDを与え、同じconnection-local reply serial `3`を意図的に衝突させる。押下前identity connectionのreplyはforwardされ、input connectionではXTEST KeyPress後の独立event receiptと一致した`GetPointerControl`だけがholdされ、150 msのsynthetic relay boundでrelease UNKNOWN/replay deniedとしてretireする。protocol/parser/socket suiteは通常/-Oで各28/28、標準caller relay compositionは各3/3。raw、conditions、receiptと19ファイルのsource/result SHA-256 manifestを保存した。

これは別接続のrelay predicateを識別するローカル結果であり、標準callerのtarget-query X protocol exchangeはcomposition試験内で依然FakeQueries stubを使う。次は実際のquery seamを第二socketへ接続し、connection/sequence/PID bindingとlate-request UNKNOWNを一つのcaller fixtureで確認する。物理release、実X server ordering、task success、recovery、効率は未解決。Issue #17はOPEN、#7924は2026-10-12時点の`STOP / HOLD`記録後も現在のWSLc owner/unused-allocation証拠なし。2026-10-19 06:20 UTCのcounts-only readはmain `0ded577...`でopen Issue 1,673件、open PR 489件。r70/r74の完全row-level inventoryを置き換えず、全件意味整理・PR統合・worktree custodyも完了していない。

## 実行更新 r80 — standard callerのidentity queryを第二Fake X接続へ統合

PR #9160統合後main `08922b7c71fd56c9ec0292e549567407b0a25dbb`で、#17のcomposition境界を一段進めた。標準MCP callerが入力中に呼ぶ`TargetQueryWorker.process_identity`をFake X reader adapter経由で別の`FakeSocketRelay`へ接続し、連続したquery/reply sequence 3, 5, 7を入力press前に通した。独立identity connectionのparserはinput targetを持たず、入力側connectionだけが自身のKeyPressとevent receiptに結び付いたreplyをholdする。別caseではsource digestを変更し、identity query replyを経たcallerがstale generationをpress前に拒否した。standard caller suiteは通常/-O各3/3、protocol/parser/socket suiteは各28/28。query adapterは固定64桁generation markerを返すFake Xであり、XResの実request encoding・PID lookup・live X serverを検証していない。blocked-I/Oの解放、物理release、task effect/success、bounded physical recovery、WSLc、efficiencyは依然未解決。初回試行はresponderがidentity query一回だけを返すfixture欠陥で次のcaller queryを待った。連続応答へ直して解消し、失敗と修理後結果の両rawをpacketに保存する。次はXRes-shaped fake replyを実query parserへ接続できるか独立判別し、対象Query/Issueとの重複・割当を再確認する。

## 実行更新 r81 — identity queryの実digest readerをcaller compositionへ追加

r80の試験adapterをさらに置き換え、`X11TargetQueries.read`と`read_linux_x11_process_identity`を実行し、shaped XRes version/client-ID値とsynthetic `/proc/<pid>/stat`を渡す。固定PID 123から計算したdigestがsource observationと入力中の三回queryで一致し、別connectionの合成transaction reply sequence 3/5/7はinput press前にforwardされた。PIDを124へ変えると実digestが変わり、標準callerは`process_generation_changed_or_missing`で拒否、input relay pressなし。focused normal/-O runsとevidence recordsはpacketの`caller-identity-r01/`以下に保存、full suiteは28/28 protocolと3/3 callerを通常/-Oでpass。これはidentity readerの意味論とcaller/query-worker合成であり、socket上のframesは依然合成transaction markerでXRes QueryVersion/QueryClientIdsのwire bytesではない。live XRes/server PID discovery、物理release、application effect、bounded physical recovery、WSLc allocation、matched efficiencyを証明しない。次はXRes request/reply bytesをidentity transportへ繋ぐ最小protocol decoder fixtureを追加し、live blocked-I/O laneは新鮮な割当・owner根拠が得られるまで行わない。


## 実行更新 r82 — A16回復判定修正をmainへ統合

PR [#8825](https://github.com/Unjuno/agent-interface/pull/8825) は当初、既にmainへ入っていた親#8817のブランチをbaseにしていた。親コミットが現行mainの祖先であること、#8825のmainとのmerge-treeに競合がないこと、変更がstrict recovery auditorとcounterexample testの2ファイルに限られることを確認してbaseをmainへ付け替え、2026-10-19 06:57:21 UTCにsquash統合した。branch protection endpointは未設定、rulesetもなく、PRのレビュー判定は空欄だった。既存replay-gateはhead `9a64c2785bbe10c3330209ab5142fb876f58f2d4`でSUCCESS。対象packageの13 testsはPR headと統合後mainのそれぞれで通常Pythonと`-O`がPASSし、`py_compile`と`git diff --check`もPASSした。テストは欠落した中間decisionを`observable_recovery_missed`ではなく`auditor_input_invalid`として識別する。この結果は保存済みA16データの判定修正であり、live MAP01、入力解放、WSLc、物理回復、task successの証拠ではない。allocationは使用していない。

[最新membership recheck r71](maintenance/repository-inventory-20261019-r71.md)では、main `f89e176b43b8db35798d51d887757e2d650e9bb1`に対するopen Issue 1,673件、open PR 488件を確認した。r70からIssue IDの変更はなく、PRは#8825のみopenでなくなった。open PRの442件はdraft、46件はnon-draftで、そのうち4件が`CLEAN`表示だった。これはPRの状態集計であって意味分類やmain統合可否ではない。次の整理は残るnon-draft PRのbase/dependencyをmainとの比較でほどき、個別の差分・根拠・所有を確認すること。Issueはfamilyごとの未解決仮説と後継を照合し、idea文書化だけでは閉じない。

## 実行更新 r83 — A06記録を統合しmembershipを再確認

PR [#8803](https://github.com/Unjuno/agent-interface/pull/8803)を、A05統合後のmain `9d129d347ba83cb1f846ad58ad91b18b7edf6fed`にrebaseし、A06固有の記録とanalysis indexだけを含むことを確認して2026-10-19 07:18:57 UTCにmergeした。通常/-Oのconstruction testsは3/3、31 frozen input hashes・4 code-source hashes・freeze hash・15 output hashesが一致し、analysis indexは854/854でsorted/uniqueだった。A06の結果そのものはrunnerが既存results directoryを検出して候補起動前に停止したHOLDである。candidate/auditor/OCRはすべて0で、再実験も科学的成功の主張もない。Issue #1998は未解決のまま保つ。

main `640dba3eff3dbb5568da0504f8a624ac80f73c1a`でGitHubの完全なopen PR ID一覧とGraphQL countを再確認し、open Issue 1,673件、open PR 484件だった。r70からopen PRでなくなったのは#8825/#8811/#8803/#8798/#8794の5件で、新規open PRは0件。#8825/#8803/#8798/#8794はmerge済み、#8811はA09証拠・hash・indexが既にmainにあることを確認した重複close。Issue membershipはr70/r71から変化なし。詳細は[最新membership recheck r83](maintenance/repository-inventory-20261019-r83.md)。これは件数・ID membershipの記録であって、残るPR/Issueの意味分類、所有確認、worktree回収を完了したことにはならない。アイデアは仮説と既存結果をfamilyへ整理した後に個別判断する。次はopen PRのbase/dependency/head deltaとcurrent worker custodyの再照合を進め、統合可能な独立成果はローカル根拠を揃えてmainへ入れる。全件を一つの巨大な監査にせず、互いに編集範囲が重ならない小さな束に分ける。
## 実行更新 r85 — 最新在庫・worktree lineage・#17 family記録

2026-10-19 09:22–09:25 UTC、main `b1bff75ffa5d06f6d2c7d10bc7a89b1ab2dbdc16`上でGitHub CLIの全ページ取得を行い、[r85 inventory](maintenance/repository-inventory-20261019-r85.md)とIssue/PR CSVを保存した。Issue 1,673件はr70とID集合不変。open PRは482件で、#9171追加、#8825/#8803/#8798/#8795/#8794/#8793/#8788 merge、#8811 closeをID別に照合した。common 481 PR head branch/SHAは不変。base SHA、author/assignee/label、review state、merge stateおよび1,864 check rollupを保存したが、38 PRにfailure/cancelled contextがあり、31 PRにcheck rollupがない。これだけではmerge可否を決めない。

2026-10-19 09:22 UTCのregistered worktree snapshot 21件を[surface map](maintenance/repository-surface-map-20261019.md)へ記録した。r85 open PRとのbranch+HEAD完全一致は#9171だけ。最大5,000行のall-state PR検索ではmerged PR 15件との肯定的lineageも見つかったが、検索上限があり未照合5 worktreeは未解決のままである。46件のroot変更、92件のuntracked browser-profile files、460 ignored files中のXRes WSLc raw logsなどを確認した。owner/process/custody未確認のため何も削除していない。

Issue #17はopen research parent / keep-open actionableとして整理した。family recordとIssue indexに、merged #9168/#9169の訂正済みR02結果 (XRes disconnect後のheld key、別client release、8.5秒内のlate pressなし) と限界を追加した。これは一つのX.Org Xvfb構成に限る。標準caller blocked-I/O統合、独立application effect、bounded recoveryが残り、release/task outcomeはUNKNOWN。#17をcloseせず、別アイデアを重複familyに吸収していない。

この区切りはfresh baseline、local custody snapshot、および一つのfamily updateであり、全Issue/PR semantic triageやrepository-wide cleanupの完了ではない。次は全open PRを意味・依存・所有・ローカル検証で個別dispositionし、Issueをfamily/provenanceへ結ぶ。worktreeをarchivalする前にclosed/merged PR ancestry、Issue assignments、process/session owner、ignored raw manifestを確認する。

## 実行更新 r88 — #17 standard callerへXRes wire transactionを統合

main `fc8d8b0ac67e8086fa53dabace4bfd3322a1b89a`を基準に、#17の既存Fake X compositionに実際のpython-xlib XRes `QueryVersion` / `QueryClientIds` request/reply framingを接続した。[r02 packet](../research/integration/offline_proxy_reply_framing_20261019/xres_wire_socket_r02/README.md)は最初のfixture長さ誤りと修正後結果を保全し、request/reply bytes、条件、normal/-O output、SHA-256 manifestを含む。実MCP callerの別identity socketを通し、caller suite 3/3、独立wire test 1/1、既存XRes client-fence suite 19/19がnormal/-Oでpass。process generation changeはKeyPress前に拒否され、held-reply cancelは`UNKNOWN`/no task success/replay disabledのまま。

これは合成XRes応答と合成PID/`/proc`によるFake X compositionであり、live server discovery、独立application effect、物理release、bounded live recovery、MAP01 task success、matched efficiencyの証拠ではない。初回X11 integration CI run `39246017054`は既存blocked-release caseで`owner_process_retired=false`とexitcode `-15`が食い違い、disconnect/release attemptがskipされてfailした。`_retire`の最終liveness poll後にprocessが終了するsampling raceをreceiptで再調整し、24/24 normal/-Oのowned-process suiteと3/3 normal/-Oのcaller suite、およびregression testを追加した。A02/A03 allocationを使わず、WSLcも使っていない。Issue #7924のowner/unused-allocation STOP/HOLDを越えて新規live attemptを始めない。Issue #17はopenのまま。

## 実行更新 r89 — retirement修正後のXvfb結果を保全し、cleanup計画の線引きを更新

PR #9182の更新後private-Xvfb integration run [39246686502](https://github.com/Unjuno/agent-interface/actions/runs/39246686502)は77/77 testsでpassし、blocked-release caseも安全側のassertionsを満たした。独立した親X clientはowner release workerのreadback後とcancel開始8.5秒時点でkeys upを観測し、遅延`b` KeyPressを観測しなかった。一方caller receiptは`release_confirmed=false`、`cleanup_status=UNKNOWN`、`late_server_request_possible=true`、`task_success=null`であり、review required・replay disabledを保つ。正確なJSONとobservation PNGをr02 packetへ複製しSHA-256対象にした。これは合成app/注入遅延requestを使うprivate Xvfb testで、bounded release objectiveの合格やtask successを意味しない。

この結果を整理計画上では#17 familyの「標準caller cancellation safety: scoped pass」「release certification/recovery: unresolved」と分類する。Issueをまとめて閉じる代わりに、idea familyごとに仮説・source Issue・固有結果/raw・限界・後継/依存・有限な次の判別作業を紐付ける。その後でIssueを個別に維持、証拠付き完了、重複移管、根拠付き棄却、owner/資源待ちへ振り分け、source/backlinkと再開条件を残す。open PRはhead/base・差分・依存・作者/owner・ローカル検証・CI・保存すべきrawを照合し、一件ずつ統合・修理・移管後close・保留へ処置する。worktreeやIssue/PRの件数だけからcleanup/deletionを推定しない。次の有限な整理単位は既存catalogの一familyと、そのfamilyに直結するopen Issue/PRの小束を選び、結果記録を先に確定してから状態処置する。

## 実行更新 r90 — PR統合後のmembership基準線

PR #9182は最新head `026bc4a82c9fdb663bc2d43ac8614780cd6e828f`で全報告checkを通過後、2026-10-19 11:49:21 UTCにsquash mergeされ、mainは`ee496780ee6e0097acb7ead1c62c6a3ee5b69878`になった。merge直後のGitHub GraphQL countはopen Issue 1,673件、open PR 479件。取得はcountのみであり、各項目の意味分類や所有確認を示さない。r87は引き続き最後の完全membership ID export、r85は最後の完全row-level/check metadata exportであり、immutableな過去snapshotとして保つ。次のcleanup batchは、既存family catalogと現在のsource Issue/PRを照合し、固有アイデア・結果・rawを移管した場合のみ個別状態を変える。Issue #17は研究親としてopenを維持する。

## 実行更新 r92 — #6373の合成結果を正規idea台帳へ接続

2026-10-19 12:50 UTC時点で`main`は`629d471ccf8dc6cd2afe4ac55134b30d023f4b43`、open Issue 1,673件、open PR 480件。これはGitHub CLIで全件ページングした件数で、意味上の分類や所有確認の完了を示さない。

Issue [#6373](https://github.com/Unjuno/agent-interface/issues/6373)とmerged PR [#6433](https://github.com/Unjuno/agent-interface/pull/6433)、保持されたcandidate/audit packetを照合し、[context-preserving delegation family record](ideas/context-preserving-delegation.md)を追加した。`PASS_METHOD_SCOPED`は既定のsynthetic T0だけに限定し、未検証のGUI-level discriminator、比較指標、停止条件を明示した。既存のidea/outcome indexから到達できるよう接続した。

このIssueはカタログ化だけを理由に閉じず、具体的なGUI-level残差があるため`keep-open/actionable`とする。候補T0は消費済みであり再実行しない。新allocation/ownerは作成しておらず、Issue/PR状態、experiment raw、worktree/branchの削除・移動は行っていない。この1-family処理は全Issueの意味監査やrepository cleanup完了を意味しない。

## 実行更新 r91 — standard callerへ実XRes target-generation結果を保全

同じprivate-Xvfb CI run `39246686502`のgeneration integration artifactをr02 packetへraw JSONと観測PNGで保存し、SHA-256 manifestへ追加した。独立XRes `QueryClientIds`と`/proc` start-ticksから求めたgenerationがstandard-caller observationのgeneration hashと一致し、synthetic appのindependent property effect `[1]`、KeyPress/KeyRelease、runtime release receipt、別X clientからのkey-up readbackを確認した。対象Window破棄後の入力はdispatch前に拒否された。これは標準caller統合による重要なXvfb結果で、前段のFake X protocol試験とは異なる。

限界として、対象は同一X.Org Xvfb上のsynthetic appで、`task_success` API fieldはnullのまま。テストoracleのproperty assertionはこの合成task内の成功判定であり、MAP01/game success、native desktop/XWayland、効率性の証拠ではない。#17のblocked-I/O cancellation receiptは依然`UNKNOWN`を保つため、正常完了時のrelease receiptと異なる境界として残す。次は、このgeneration/effect contractを実アプリ/MAP01に渡す条件と、safe recovery後の独立task oracleを既存family証拠から結び、allocation HOLDを越えずに未解決依存を一つずつ狭める。

## 実行更新 r93 — #17 missing-cancel-ackの標準caller結果を整理記録へ追加

PR #9192のhead `8b7efe11979e32bccc1ad76074196829d5dc629e` に対するprivate-Xvfb run [39261239773](https://github.com/Unjuno/agent-interface/actions/runs/39261239773) は、ownerのXlib `Display.sync()`を停止したままcancel応答を1秒遅らせるfixtureで、callerが`cancel_unconfirmed`を669.824 msで返し、exact owner終了、XRes disconnect、別workerのrelease readback、独立したparent/horizon keymap readback (`a=false`,`b=false`)を観測した。raw JSON/PNGとchecksumは[#17 r04 packet](../research/integration/standard_caller_xvfb_cancel_trace_20261019/r04/README.md)へ保存済み。

これは250 ms cancel-control response budgetを通した有限なstandard-caller/Xvfb結果である。callerはrelease `UNKNOWN`、`late_server_request_possible=true`、`task_success=null`、replay disabledを維持している。したがって#17はopenのまま、r02 retirement failureとの不整合も未解明として保持する。物理入力解放、server outage保証、独立task effect、bounded recovery、MAP01、効率比較の完了とは扱わない。既存family agenda・idea index・worker mapへリンクを通した。ローカルの完全な`runtime/cli_v1` suiteはnormal/optimizedそれぞれ469 passed・7 skipped、owned-process suiteは各25 passed。Xvfb CIは当該headでpass。PR状態やIssue状態はこの記録だけで変更しない。

## 実行更新 r94 — #9192の検証済みcancel応答修正をmainへ統合

PR [#9192](https://github.com/Unjuno/agent-interface/pull/9192) は2026-10-19 13:38:03 UTCにsquash mergeされ、main commit `3bc02f2b9c7362e743db5f81f3b3d2556038c55f`となった。Xvfb blocked-I/O missing-ack run 39261239773を含む全ての報告checkがpassし、mainの`main` branch protectionはなく、repository rulesetも空であることを確認して統合した。r04のraw JSON/PNG blobはmain上でpacket manifestのsourceとbyte hashが一致する。merge後も結果分類は#17のscoped cancel-response progressであり、caller release `UNKNOWN`、late request possible、task success null、replay deniedを維持する。#17を閉じる根拠、物理解放・MAP01・recovery・効率性の証明ではない。

## 実行更新 r95 — 2026-10-20 #8842の証拠救出と整理順序

現時点でリポジトリ全体の完全なIssue/PR再棚卸しは未実施。r96/r85等の過去membership・row metadataは時点スナップショットとして保持し、今日の総数や担当の根拠には使わない。全体クリーンアップは次の順で進める。

1. **入口を整える。** 現在のmain SHAと完全ページングのIssue/PR membershipを一度取得し、最新の全件一覧を重複保存せず既存r-seriesへ追記する。別途、アイデア索引の未分類gapとopen PR head/base/check/ownerを切り分け、件数だけで意味を推定しない。
2. **Idea family単位で意味を復元する。** 各Issueの現行本文・最新コメント、関連PR、既存idea index/family record、研究raw/auditを照合する。記録する項目は仮説、最も強い比較対象、既存の支持/反証/STOP、未解決残差、依存、実行可能な次試験、再開条件。distinct questionは統合せず、類似Issueも独立仮説を確認する。
3. **PRを一件ずつ処遇する。** exact head/base、author/assignee/reviewer、merge/conflict、差分・依存、必須/任意CI、適切なローカル検証、固有成果/rawのcustodyを確認する。処遇は検証後merge、修理PRへ移管、重複として証拠移管後close、研究候補として保留、または明確な理由付きclose。競合PRの全体mergeやworktree変更だけを目的にしない。
4. **Issueを根拠に沿って維持/終了する。** keep-open/actionable (固有の次試験あり)、keep-open/blocked (owner・権限・資源・依存と解除条件あり)、duplicate/moved (canonical Issueと双方向リンクあり)、evidence-complete、evidence-rejectedに分類する。閉じる前にアイデアと結果を正規カタログへ保存し、Issueへ戻り先・後継・終了理由を記す。計画への転記だけでは科学的完了としない。
5. **workspace/branchを最後に片付ける。** registered/unregistered worktree、PR head/base ancestry、Issue/PR owner、実行中process/session、ignored/raw manifest、未追跡データを照合する。全て復元可能なcustodyを確認してから個別にarchive/deleteを判断する。clean worktreeやclosed PRを未使用の証拠としない。

### 今回の具体的バッチ: PR #8842

PR #8842はopen、non-draft、base `f185a9059d485a4f8d5a65e9e7f6782897f67eae`、head `80b81a53582e877fd9ca51c35999f27aadea7990`、mergeable=false。現行main基点の隔離枝に481個の追加研究ファイルをexact blob一致で複製済み。PR由来の単独回帰テスト1件は、対応する既存backend実装変更を除外しているため、この証拠専用バッチへ入れず、原PRに保持する。#8842の既存ファイル4件の変更のうち、`research/doom/doom_owner_thread_release_batch_backend_v1.py`と`research/doom/test_release_backend_v3_composition.py`のコード変更はこの救出枝へ含めず、統合判断を分離する。既存の`RESEARCH.md`と`research/doom/README.md`にはA10/A11/A15の結果索引のみを追加し、A19–A27のリンクを実在するレポートへ修正した。A26の`REPORT.md`はA25文の重複なので、そのSTOP判定は`POSTHOC_STOP.md`を正として明示した。

このバッチは追加証拠と研究索引の救出であり、原PRをmergeまたはcloseする根拠ではない。A10/A11/A15、A19–A27は元の条件・raw・判定を保つ。特にA19/A20–A23のSTOP/bridge FAIL、A24/A25のscoped pass、A26 procedural STOP、A27の2.229 ms virtual X key-upとanalyzer unmatchedを個別に残し、physical input/MAP01/task successの主張へ拡大しない。A28/A29のpreregistered FAIL、live allocation #7924 HOLDも維持する。次のPR処遇はこのexact-head salvageのローカル検証とPR差分確認後に行い、Issue #59は残る科学ゲートがあるためopenを保つ。

## 実行更新 r96 — #9207証拠移管完了、#8842コード差分を現mainで検証

PR [#9207](https://github.com/Unjuno/agent-interface/pull/9207) was squash-merged at `68fa2bc70b46241c0b6901ddd279fb0c7f771da2` after replay-gate, public-navigation, and research-workspace-index all passed. Readback against merged main verified all 481 preserved package blobs match PR #8842 head `80b81a53582e877fd9ca51c35999f27aadea7990`; no experiment was rerun. The original #8842 remains open because its two backend/composition edits and regression test were not part of the evidence transfer.

Those code edits now apply cleanly on the merged main tip in isolated branch `rescue/pr8842-code-r01`. The first local normal/optimized run exposed an obsolete nested `up_batch` fixture in the old PR test and an assertion that erased a valid per-key X-server release receipt when the enclosing batch was incomplete. After removing the duplicate fixture path, the adapted test retains the observed per-key receipt while asserting `owner_transition_verified=false` and `release_batch_complete=false`. The four new owner-bound admission-link tests plus two composition tests pass 6/6 under CPython 3.13, both normal and `-O`; `git diff --check` passes. This is local contract/composition verification only, not physical release or task-effect evidence. Next is independent diff review and PR checks for the current-main code adaptation; close #8842 as superseded only after all its unique code/tests are verified on main, preserving #59 as open.

## 実行更新 r97 — #8842の証拠/コードを分離統合し、現membershipを再確認

PR [#9207](https://github.com/Unjuno/agent-interface/pull/9207) merged 481 exact research package files and corrected result indexes at `68fa2bc70b46241c0b6901ddd279fb0c7f771da2`; all 481 blobs match the original #8842 head. Its three checks passed. PR [#9208](https://github.com/Unjuno/agent-interface/pull/9208) merged the current-main owner-bound admission linkage, the adapted composition test, and its new regression tests at `f29909378a117eb9b5cb728d99efb593798adac1`; its three checks passed and the formal allocation workflow was skipped. Six focused tests passed on CPython 3.13 in normal and optimized mode. The test preserves observed per-key X-server release evidence while the enclosing incomplete batch remains explicitly unverified.

Original PR #8842 was closed as superseded after the 481 package blobs and code/test paths were checked on main. Its remote branch remains intact pending a separate dependent-PR/worktree/ignored-data custody scan. Issue #59 remains open; no Issue was closed, and no experiment or WSLc allocation was rerun.

The [2026-10-20 count/ID-set recheck](maintenance/repository-inventory-recheck-20261020-r01.md) at main `f29909378a117eb9b5cb728d99efb593798adac1` found 1,673 open Issues (same ID-set digest as r97) and 477 open PRs. It does not include row-level metadata or semantic/owner classification. The next cleanup batch must use a fresh complete metadata view to select one bounded PR/family group, reconcile each unique idea/result/owner/dependency, and only then choose merge, transfer, keep-open, or evidence-backed closure. It must not turn the old r97 inventory into a blanket close/merge instruction.

## 実行更新 r95 — server-stop Xvfb結果を保全し、cleanup計画を更新 (2026-10-20)

PR [#9220](https://github.com/Unjuno/agent-interface/pull/9220) を、最新main上での全報告check通過後にsquash mergeした。新head `4262d979a451266dae79e595aa68dc7ef400331c`、merge commit `de852bf3b65ad5b8debac3b7e0138bcf843e7313`。旧headのX11 integrationは期待値の誤りで失敗し、callerのfail-closed動作（owner disconnectがUNKNOWNならreleaseを開始しない）に合わせてassertionだけを修正した。

Xvfb run [39373461786](https://github.com/Unjuno/agent-interface/actions/runs/39373461786)の`standard-mcp-xvfb-server-stop` raw JSONを[server-stop r01 packet](../research/integration/standard_caller_xvfb_server_stop_20261020/r01/README.md)へ無変更で保存し、SHA-256を記録した。cancelは0.409 sで返ったが、XRes disconnectはUNKNOWN、release attemptは`not_attempted`、runtime cleanup/releaseはUNKNOWN、task_successはnull、replayは拒否。X server再開後も別clientの8.5 s horizon readbackで`a`がdownのため、synthetic task oracleはFAIL。テストfixtureの最後の直接KeyReleaseはcaller成功に数えない。cancel receiptのowner retirementとterminal owner livenessの不一致もそのまま残す。

Issue #17はopenのまま。この結果はprivate Xvfb上のbounded cancel responseと未確認解放のcounterexampleであり、物理release、MAP01、一般的なserver outage recovery、効率を示さない。WSLc/Docker allocationは使っていない。次の有限作業はowner-lifecycle receiptの不一致を再現可能な境界で調べ、server resume後のcaller所有release検証をテストfixtureのteardownと分離すること。2026-10-20 05:13 UTCのGraphQL count-only readは1,672 open Issues / 476 open PRsを返したが、新しい全件membership exportではない。整理計画は[REPOSITORY_CLEANUP_PLAN.md](REPOSITORY_CLEANUP_PLAN.md)を参照。

## 実行更新 r96 — PR #7283の固定レビュー人数条件を撤回 (2026-10-20)

Current main `eca99d0da17938e71707e4530d80e15ed7ca1d35`でPR [#7283](https://github.com/Unjuno/agent-interface/pull/7283)のlive bodyを再確認したところ、2名の非作者承認・候補reviewer席・committee epochを要求していた。この固定人数/席条件をPR本文で明示的に撤回し、作業・実装・validation・PR進行を票数で待たせないと記録した。元の提案メタデータは本文内にhistorical provenanceとして残した。exact source/evidence、current-main composition、platform/owner/cancellation/sole-sender safetyは技術的acceptanceとして維持する。

これはPR説明文の変更のみであり、コード、実験、Issue/PR状態、branchは変更していない。#7283はDraft/open、head `92a610b30507e9ac0c159ca18ac8a8502c8d5b1c`、base `6dee2bff223c7e9643949d2a8ef3acf7e9b007da`、GitHub `DIRTY`のためmerge-readyではない。current-main救済#8368もDraft/open、古いbase `ea2af10f1111ba614311e354dfecde1bbf653981`、`DIRTY`で、別途current-main差分と検証が必要。review-quorum scan r01の39件は文言候補であって39件の実効quotaを意味しない。他のcandidateは個別のlive確認前に変更しない。mainのcount-only readは1,672 open Issues/476 open PRs。全件semantic triage・membership export・owner/custody auditは未完了。


**Disposition follow-through r05 (2026-10-20):** Original Draft PR #8861’s A04 oracle-boundary construction patch was independently reapplied to a temporary copy of the pinned A04 sources and rerun through its guarded verifier. Four focused regressions and 13 applicable existing construction tests passed in normal and optimized Python; the fixed A04 source hashes matched. Current-main successor [PR #9238](https://github.com/Unjuno/agent-interface/pull/9238) merged at `5ce0f2b67d3dafcde70cc84b9832d5f841475210`; replay-gate, analysis-index, public-navigation, research-workspace-index, and three method-contract jobs passed. One other method-contract job remained in checkout, while the same suite passed locally. #8861 was closed with a successor pointer. A04 remains `HOLD_UNCERTAIN`; no candidate/auditor or WSLc allocation was rerun, and Issues #31/#8636 remain open. Complete membership advanced to r108 (1,672 Issues/468 PRs); this is one scoped PR disposition, not full repository cleanup.
