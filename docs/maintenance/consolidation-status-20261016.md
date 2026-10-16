# 現在の整理状態と次の実行順

2026-10-16 JST。基準main `1ece47014d05db898bf73afcd722a14524462e15`。
目的は、多数のワーカーが研究内容を失わず、独立した仕事を選び、検証済み成果を統合できる状態にすること。
整理全体は未完了であり、全Issueを閉じることを完了条件にしない。

### r15：4件の既存成果を確認して索引の未確定表現を修正（2026-10-16）

Issue #7475/#7462/#7458/#7436の全コメントと関連PRを再照合した。#7475は未統合Draft PR #7480の
合成カード整合性のみ、#7462はmerged PR #7523の有限DSL比較結果、#7458はDraft PR #7464の
`FAIL_REDUNDANT`、#7436はA01 setup failureとmerged PR #7460の別A02 method PASSとして索引化した。
人間の解釈・承認やGUI/controllerの効果へ外挿していない。関連PR状態も再読時点で明記した。

### r14：#8638の統合結果を反映し、A01証拠refは保全（2026-10-16）

索引の#8638は以前「未検証案」のみとしていたため、IssueのA02結果と関連PRを再読して訂正した。
PR #8740はOPEN / DIRTYで、12 synthetic profiles・192 rows、3組すべての順位反転を独立監査した
`PASS_METHOD_SCOPED`を記録している。コンテナを使わないmacOS network-deny実行であり、GUI/製品の
情報価値や実運用への外挿はない。Issue #8638 A01のmissing-raw custody問題はA02と別の結果として残る。

未参照branch `research/8638-split-control-voi-a01-20261008`を再取得すると、mainにない唯一の差分は
A01 candidate/auditor sourceを含む`experiment.mjs`だった。A01 raw custody問題の再構成に必要なsourceで、
A02 PR #8740では代替されないため削除せず、監査CSVで固有証拠refとして保持理由を明記した。

### r13：4件の研究Issueを証拠範囲つきで索引化（2026-10-16）

Issue #7970/#7732/#7707/#7487の本文・全コメントを照合し、関連するPR #8123/#7744/#7507の現状態と
記録範囲を確認した。#7970はplacement仮説の測定なしと共有WSLc運用逸脱、#7732は未検証の最小証拠束提案と
#6774のcustody不確実性、#7707は候補rawなし・監査未実施の一回限りの実行記録、#7487は20件のsynthetic
provenance判定に限定した方法結果として索引に加えた。人間・実GUI・本番・速度・移行への主張は加えていない。
四つともIssueはOPEN。今回、新しい候補、コンテナ、モデル、GUIを起動していない。

### r12：superseded design-only refを回収（2026-10-16）

`research/8185-transform-graph-a02-20261005`をliveで再照合した。Tipは
`c0f8e1b690d86a7ff10cecf47d9bb16fcd79d053`で、唯一の未統合差分は
`research/analysis/epoch_transform_chain_8185_a02_20261005/DESIGN.md`（blob
`84a151d3d5e495fdb3c7cc9d2cca5860fe8c1df5`）。ファイル自身が未凍結の設計記録と明示し、
同じIssueの後継A02実験と最終プロトコルはmerged PR #8211でmainに存在する。
全状態のPR head/baseを照会して参照0、branch protectionなし、全worktree一覧でcheckoutなしを確認した。
このため、tip固定の`--force-with-lease`でremote refのみ削除し、remote readbackで不在を確認した。
履歴SHA・唯一のパス・削除理由は`unlinked-branch-review-20261016.csv`に保持した。
削除後のlive readbackはremote branch 587本、open PR 518件。直前の監査でPR参照なしだった31本から
この1本を除いた30本が残る見込みで、各refの内容・所有・worktreeを引き続き個別照合する。

### r11：次の4件のIssue証拠を分類して索引化（2026-10-16）

Issue #7955/#7790/#7773/#7741をGitHubから再読し、既存の先行・後続Issue、正式コメント、関連PRを照合した。
#7955の合成rank-uncertaintyとminimax fallback、および未検出のoutside-set miss、#7790のchoice-opportunityとscope条件を
満たす行動由来preference evidence、#7773のmodel-visible candidate-list consumer未発見、#7741の複数allocationを
分けて`docs/IDEAS_AND_OUTCOMES.md`に記載した。#7741のT0dは32/32のsynthetic seed cellsを通過したが、
過去T0群の結果も別に残し、現実のadoption/production/user結果へ広げていない。Issue状態はいずれもOPEN。
本ターンは索引・状態の読み取りのみで、候補やモデル、GUIを実行していない。

### r10：4件の過去Issueを成果境界つきで索引化（2026-10-16）

Issue #8421/#8341/#8185/#8032の本文・コメントと関連PRをGitHubから再読し、
`docs/IDEAS_AND_OUTCOMES.md`へ追加した。#8421はmerged #8430の三つの合成会計ケースに限定したPASS、
#8341は50行の形式上のPASS記録を保ちつつ、position-control cue長不一致とpost-formal auditor importの
逸脱により受入条件が未確立である状態、#8185は不成立のA01証拠と後継#8201の別A02合成結果、
#8032は参加者なしの方法・検出力パケットとして区別した。各IssueはOPENで、関連PR状態は索引に記した。
新しい割当、候補、GUI、モデルは実行していない。

共有インデックスの状態凡例も、記録されたhold/failureラベルがその証拠の説明に限られ、
無関係な作業の割当・停止を意味しないと明確化した。これは過去の結果ラベルを変更するものではない。
Public Navigationは26文書 / 2,140 repository-relative linksで成功。現在の部分チェックアウトには
Research Workspace Index checkerとreplay-gate対象が存在せず、両者はローカル実行できなかった。

### r9：実験ランタイム喪失時のclaim保全案を索引化（2026-10-16）

Issue #8905の本文と関連Issueを確認し、hash/fixity、解釈可能性、raw-only監査、再実行、独立再現を
別レベルに分ける提案として `docs/ideas/claim-preservation.md` に整理した。3種のanalysis-only packageを
offline copyで分類する提案は未実行であり、IssueもOPENのまま。別のホスト監査追試として、保存済みrawに対し
各監査器を1回ずつ実行した。#5749は78行で`PASS_METHOD_SCOPED`、7/7改変拒否、#6530は8行で`PASS`、
#6590は10件の決定論的CPU再フィットと30,720行を確認した後、hash/refit/prediction不一致で
`HOLD_AUDIT_INTEGRITY`となった。#6590はPython 3.14.5 / NumPy 2.5.2上で、packageのNumPy 1.26.4 pinとは
異なる。候補起動や外部モデル実行はしておらず、ネットワーク遮断・入力コピー・5段階分類・fallback評価も
していない。この結果は#8905の当該監査器に限り、他のIssueや実験の割当状態を変更しない。
ページを`docs/ideas/README.md`と`docs/IDEAS_AND_OUTCOMES.md`へ接続した。後続のIssue本文確認で#8846/#8856/#8870/#8872の
4件が既存Markdown未掲載のopen research ideaと分かり、仮説と評価境界を`docs/IDEAS_AND_OUTCOMES.md`へ追加した。
続く本文確認で#8886/#8889/#8898/#8901も未掲載のopen research ideaと確認し、先行・類似案との違いと検証限界を
同じ索引へ追加した。さらに#8902/#8903/#8904の本文を確認し、それぞれの推定対象、比較方法、前提を索引へ加えた。
その後#8638/#8641/#8648/#8651の本文を読み、観測情報の制御分離、feedback、uncertainty source、path dependenceという
別々の問いとして索引へ加えた。
続けて#8596/#8597/#8613/#8614を本文から確認し、確率的進捗境界、decision-opportunity tail、predicate membership、
adaptive cohort reuseを別の研究対象として索引化した。
さらに#8549/#8574/#8577/#8582を本文確認し、人間アラート検出、構造化レビュー、GUI lens-law転送、
human-agent item functioningの4件を別の未検証案として記録した。
次に#8527/#8532/#8533/#8544を確認し、期限内reachability、条件統一したrejection memory、success-cue inoculation、
target–flanker bindingの仮説を各先行Issueと分けて索引化した。
#8498/#8518/#8522/#8526も本文を照合し、retrieval practice、WSLc session reuse、vignette仮定の検証、
path-conditioned read-setという別の問いを追加した。
その後#8618/#8620/#8636/#8675の本文を確認し、cross-task disclosure、execution information、
rotation-invariant visual feature、version-crossing target continuityを分離して索引に載せた。
さらに#8493/#8494/#8594/#8595を確認し、temporal drift、shared-queue synchronization、reverse-stress synthesis、
mediation identifiabilityをそれぞれ別の未検証課題として記録した。
今回#8073/#8166/#8300/#8319も本文から整理し、analogy retrieval、screen-reader handback、external-write journaling、
feedback/update-rule交互作用の違いを追記した。
これで全Issueの分類が済んだわけではない。監査追試の詳細と未実施境界も同ページに記録した。
Public Navigationは26 documents / 2,140 repository-relative linksで成功。PR #9005ではhead
`1313fc6185b4e9ae8af37dc6483cc6da7d50c413`と、4件のIssue索引を含むhead
`7ba4191dd48d4a02f445f33cc9759b0237fb4423`の両方でPublic Navigation、Research Workspace Index、replay-gateが成功した。
変更は既存の [PR #9005](https://github.com/Unjuno/agent-interface/pull/9005) にあり、未マージ。
これは研究ラベル全体の整理完了ではない。次は未整理Issueと未参照branchの実内容・既存証拠・所有を個別に
照合し、意味のない重複記録や安全に回収できるrefだけを特定する。

### r8：アイデア索引と重複branch refの更新（2026-10-16）

基準mainは `1ece47014d05db898bf73afcd722a14524462e15`。全Issueを `research-idea` labelで照合し、
未掲載の #8022/#8024 を `docs/ideas/` と `docs/IDEAS_AND_OUTCOMES.md` に記録した。
#8022は no-human protocol audit のHOLDと倫理条件、#8024は authored fixtureのMETHOD_PASS_SCOPEDと
固定timeoutを上回る価値が未実証である境界を残す。Issueは開いたまま。変更は
[PR #9005](https://github.com/Unjuno/agent-interface/pull/9005) にあり、先行headではPublic Navigation、
Research Workspace Index、replay-gateのCIが成功。今回追記後のheadは別途CI確認する。未マージ。

未参照branch `research/8654-c03-support-sufficiency-20261009` (`e4061a6f0fc9863ed2dbec7e09d3a99b4972685`)は、
無保護、全PR head/base未参照、登録worktreeなし。mainとの差分16ファイルすべてのblob SHAがmainおよび
merged PR #8664と一致し、#8664のC04がC03のpre-candidate STOP履歴を明記していたため、remote refだけを削除し
GitHubで不在を確認した。Issue #8654とmainの証拠ファイルは変更していない。

`fix/8243-verifier-r2p6-20261006` は別途再照合した。8ファイルすべてがopen rescue PR
[#8375](https://github.com/Unjuno/agent-interface/pull/8375) と同一blobだが、merged Issue #8243の公開freeze
コメントが元branch名とtipを引用しているため、このrefは保持する。PR #8375の統合後、または引用を安全に
置き換えた公開記録が確認できた時点で再評価する。

削除後のlive snapshotはremote branch 588本、全PR 6,102件、open PR 518件、PR head/baseに未参照31本。
未参照31本の個別内容・所有確認は継続中。削除は確認できた重複ref一件に限定し、worktreeや固有rawは
対象にしていない。

## 後続の現在地

### r7：マージ済みremote branchの再照合・回収

同日取得した全6,100件のPR記録とremote branch 618本を照合した。#8862のmerged branch
`fix/pr8857-deadline-type-fix`は、main包含、無保護、依存PRなし、worktree未使用を
確認して個別に回収した。618本の一覧では、さらに19本がmerged PR headとtip完全一致、
main祖先、無保護、全PRのhead/base依存なし、確認したlocal worktree未登録の条件を
満たしたため、tip固定`--force-with-lease`で削除した。これら20本はmainから到達できる。

| PR | 削除したremote branch | tip |
|---|---|---|
| #8862 | `fix/pr8857-deadline-type-fix` | `37d6fca43c927de8acc1cbfc3d1a30808377a229` |
| #8821 | `fix/doom-passive-refresh-empty-release-token` | `30ba3a90be112fe6bbcb0ed52e43a4041bea5b6e` |
| #8829 | `fix/issue59-v10-release-rpc-failure-20261009-a01` | `a197e6a87132be5fd29a5a0656edb5b309a2a7b2` |
| #8837 | `fix/v39-windows-appserver-executable` | `7adc0fdc8b191cc139baa30fe7c3bb605c2dab03` |
| #8693 | `fix/59-release-cleanup-lease-identity-a01-20261009` | `cb47c43c97258cd92f3059c22e49eb181dbf2435` |
| #8835 | `fix/59-terminal-release-completeness-20261009` | `c024b41a0aac62a6b3d466e935d77edf477bb3fa` |
| #8813 | `rescue/7321-evidence-only-20261009` | `84d92821780b69f14625542b27725965b2519e50` |
| #8820 | `rescue/8686-currentmain-20261009` | `8bd299a5bc86cf3711ca51fc36a974f433761842` |
| #8815 | `research/a16-result-evidence-20261009` | `2d777d5290a6fded898ca8977ce04f0838ffc55d` |
| #8871 | `research/health-typed-release-delay-a01-20261012` | `18d1fadea3dcad4cffaa743d3480fa309edcf643` |
| #8923 | `research/v10-wslc-app-effect-a35-a36-20261015` | `7f7065a050ad4d9b5dfd89cf2b324ba95309a1cf` |
| #8922 | `research/v39-wslc-app-effect-a34-20261014` | `b1983742ed7e73a5f62e08f8b271d927c0eeb060` |
| #8918 | `research/wslc-typed-guard-replay-a03-20261013` | `580c452ddd0fea55be817f138ad225d2f44de4e6` |
| #8771 | `research/59-cleanup-unknown-key-failclosed-20261009` | `8af95598a2517088203be2696b043ef329ba5b5c` |
| #8690 | `research/59-global-live-gate-scope-20261009` | `7de1969eebef154108d4349d2ba8f9ab00e8f3b0` |
| #8866 | `research/59-health-only-typed-monitor-a01-20261012` | `eb1367cc3ac1184862c454440a418dcf1add9267` |
| #8699 | `research/59-invalidation-recovery-a01-20261009` | `94c3f4c7299c3e5e8c50890071bfcb96a4ae7193` |
| #8696 | `research/59-terminal-custody-order-a01-20261009` | `e991aa78c28b4bbbb55de5599248b26a9e16db8f` |
| #8742 | `research/59-v39-regression-a03-currentmain-ffe5292-20261009` | `fd0f79e1ad36e39fb8e4a435fc0a63650b942170` |
| #8822 | `research/6018-importance-sampling-t0-a01-20261009` | `e3e025c37701717ecfb5263b9ee45bc5051de6a5` |
| #8705 | `rescue/5749-action-only-currentmain-20261009` | `1b438270124f1647e950fd320067a1a078e80e40` |
| #8709 | `rescue/6576-a04-archive-currentmain-20261009` | `7f25e16a6d9356c7dcac49033758433dfb46cb89` |
| #8710 | `rescue/7386-7414-currentmain-20261009` | `0c4dabaaa40d0c681eaa01dc776879e725cc2441` |
| #8884 | `research/wsl3-residual-docker-inventory-20261012` | `d4c726cd7dbb84c2cd7eacd01aef897407ae8c67` |
| #7109 | `research/17-gil-cancel-c01-70ab-20261003` | `8394ab7f4a82cafc29a851c28afd56d7a1c8f804` |
| #8384 | `research/59-interrupt-cancel-compose-a03-20261008` | `fd52341c4686893ff3de8795c9a5b671c7d20f9c` |
| #8874 | `research/59-v39-owner-close-currentmain-a09-20261012` | `6d008b53e23fda4703c8f56c4ea1bd762e5d147b` |
| #8662 | `research/8654-c02-raw-custody-20261009` | `60a726cf744cab1044083ce0af61d7d4acf43adc` |
| #8786 | `test/exchange-presentation-failure-20261009` | `5f8fdedaac8fbdaf820ca26dd7ebc7985dc2305a` |
| #7264 | `feat/finite-role-recovery-2d0b-20261004` | `8fe7c2b7a955187939014aff33cf61ed01ea90e9` |
| #8370 | `rescue/finite-role-recovery-currentmain-20261008` | `9fb4a64d6a86fc2eb01b4e984508e8f320bb3e31` |

The four #8705/#8709/#8710/#8884 tips were not ancestors of main, so their changed files were
compared blob by blob. Every evidence file was already identical in main; branch differences were
stale index deletions or, for #8709, an older archival qualification missing provenance detail
that main already preserves. The closed, unmerged PR heads #7109/#8384/#8874/#8662/#8786 had no
base dependents or local worktrees, and every changed file was byte-identical to main. Their PR
records remain available. The #7264/#8370 finite-role prototype and tests are also byte-identical to main;
their only unique README row is superseded by the current main convergence link. The remaining
branch `research/59-a07-cancel-admission-order-a01-20261009` has 36 A03–A07 files absent from main
and is retained for evidence preservation/integration review. After all 31 ref deletions, the live
remote count is 588 and every deleted ref was verified absent. PR-linkage classification of the
remaining refs is 516 open-PR heads, 10 base dependencies, 29 closed-PR heads, and 33 with no PR
head/base reference in the complete 6,100-PR snapshot. The closed-head and unreferenced groups
still require content/owner review; they are not assumed disposable. The [unreferenced-branch
comparison](unlinked-branch-review-20261016.csv) records exact tips, ancestry, current-main blob
matches, and local-checkout coverage. All 33 are unprotected but diverged, with one or more commits
ahead of main; 32 contain paths absent or different in main. The remaining blob-identical branch
is associated by name with open Issue #8654. No matching checkout was found in the 38 local Git
checkouts scanned. Issue/owner association remains incomplete, so these 33 refs are preserved.

After that snapshot, `research/wsl3-dockerless-doc-inventory-8882` was reviewed separately.
Issue #8882 is closed with an explicit completion record pointing to the superseding inventory
merged by PR #8884; the branch had no current PR head/base reference or matching local checkout.
Its exact tip `76f33cc4b6c7af55074030ddc85857b73aec3117` was deleted with a tip-fixed lease and
verified absent. The current remote branch count was 587 and the no-PR-reference group was 32
at that intermediate capture. The comparison artifact was absent from main; the current census
below replaces it.
Subsequent creation of the current-main Win32 release-test PR #9006 added one open PR head; the
live remote count is now 588 branches and 517 open PRs. The no-PR-reference group remains 32.
The closed #8592 transfer is not a deletion signal for every associated ref: its final comment
explicitly keeps A01/A02 execution STOPs and the superseded A03 freeze in immutable branch history.
Accordingly, `research/8592-dpor-t0-a01-20261008` (`b0951ae1…`) and
`research/8592-dpor-t0-a02-20261008-r1` (`bb195877…`) remain retained as evidence custody.

The separate no-PR rescue branch `rescue/win32-release-retain-7772-currentmain-20261007` also
contains release-custody tests absent from current main, so it is not disposable. Current-main
adaptations are in draft [PR #9006](https://github.com/Unjuno/agent-interface/pull/9006): its five
new pure release tests pass locally and in the native-mcp Win32 module, but CI remains red. The
unchanged native Win32 fixture test returns `release_unverified` when `GetAsyncKeyState` reports
zero; the native-mcp job also has four failures in other test modules. This is an unresolved
release-verification contract and CI baseline, not evidence that the new tests failed. No runtime
code or original rescue ref was changed.

### r6：モデル連携・比較評価アイデアを一族ごとに整理

基準main `1ece47014d05db898bf73afcd722a14524462e15`（2026-10-16）。
[モデル連携・評価agenda](../ideas/model-coupling-and-evaluation-agenda.md)と
[Issue中心の一覧](../IDEAS_AND_OUTCOMES.md)へ、#6001/#6035/#9004を追加した。
これらは同じ結論へまとめない。#6001の合成canary/interference T0とWSLc replay、
#6035の64行合成cross-model method T0は、それぞれの限定根拠と過去のSTOPを分けて記載。
#9004は未検証のまま、Issue本文のfinite CPU-only T0条件と比較対象を整理した。
Issueの状態変更、外部provider/model呼出し、GUI実行は行っていない。

運用記録Issue [#8913](https://github.com/Unjuno/agent-interface/issues/8913)は、2026-10-12の
WSLc read-only事前確認と、#8685のclient/container lane条件を読んだ後に認識した手順逸脱を記録する。
実験・移行結果ではなく、既存allocationも消費していない。この記録が限定するのは当該WSLc
操作だけであり、独立した作業や他の実験レーンの停止条件ではない。

2026-10-16にIssue #8914のオフライン候補を実行したところ、A01/A02とも候補後の独立監査が
sentinel再構成で止まったため、科学的判定なしのraw保全PR
[#9007](https://github.com/Unjuno/agent-interface/pull/9007)を作成した。
branch `research/8914-budgeted-discovery-t0-a01-20261016` はこの未統合PRのheadとして保持中。
同日時点のremote refs 589本・open PR 518件にはこれを含み、削除済み・main統合済みとは数えない。
この保全用branchは独立したWSLc・GUI・ゲーム・model作業を制限しない。

同日にbranch/PR参照を再取得して比較表を[再生成](unlinked-branch-review-20261016.csv)した。
589 remote branch、6,102件のPR参照record、PR head/base未参照32 branchを照合し、32本すべて
unprotectedかつmainとdiverged、合計106 commit aheadで、比較APIが各branchの変更pathを報告した。
32本中6本は監査cloneの登録worktreeにも存在する。各tip・merge base・ahead/behind・変更path・
worktree対応をCSVへ記録した。32本は固有内容と所有者の確認が残るため削除していない。

同じroot cloneのworktree台帳は92件中33件がprunableで、その33パスが実在しないことを確認した。
dry-runが示した欠損metadata 33件だけを`git worktree prune`で除去し、branch refや作業ファイルは削除していない。
59登録worktreeが残り、prunableは0件。read-only statusでは52件clean、7件dirtyだった。
変更path・branch・remote/PR参照の[一覧](dirty-worktree-review-20261016.csv)を保存し、いずれもreset・削除していない。
dirtyなA16 health-zero worktreeの2 tracked変更を含み、raw/evidenceのuntracked項目も現存を再確認して保全した。

同じバッチで、統合済みPR [#8791](https://github.com/Unjuno/agent-interface/pull/8791)
のremote branch `fix/primary-release-array-shape-20261009` を回収した。記録tip
`3884c929435db18855b5ca62e95ca90ceadb52ed` は現行mainの祖先、branchはunprotectedで、
open/closed PRのhead/base依存はなく、確認した69件のlocal checkoutでも未使用だった。
正確なtipへの`--force-with-lease`削除後、remote refの不在を確認した。変更内容は
merge commit `761a26e2cfae611efe97a426ed2555063928b177` とmainに残る。

続けて、merge済みPR [#8784](https://github.com/Unjuno/agent-interface/pull/8784)の
`fix/kernel-stop-release-evidence-20261009`も、tip
`08dd5be82cf9750faca9f9d9d5ba81aaf446bea0`がmainの祖先であること、unprotected、
head/baseとも依存PRなし、確認範囲にlocal checkoutなしを確認して、tip固定で削除した。
PRのmerge commit `b8ab890b03289f9a1303377c26b3cbb41ce7231e`もmainの祖先である。
branch削除後にremote refがないことを再確認した。関連する古いlocal cloneでは、dry-runが
存在しないdirectoryを指すと確認した3件のstale worktree metadataをpruneした。

#8816と#8763は、closed PR #8823/#8787のbaseに使われていたため、今回の削除対象から除外した。

次は#9004の有限合成T0を独立したsource freeze・candidate・raw-only auditとして実行するか、
先にIssue群の依存・実行優先を更新して実行先を確定する。#57の統合効率ゲートを押しのけず、
実モデルT1やremote-model budgetを使わない。並行してPR/branch inventoryを現行状態で再取得し、
完了・後継移管・保全のみ・未判定を判別する。全件の内容精査やref削除はまだ完了していない。

## 前段の進捗履歴

### r5：保全していたV15選択変更を現行mainへ結合

基準main `7aeb6f933c67384ad0e8d3b25e1d68a44ec341a8`。#9001は統合済み、
#8867は[採用先付きで終了](https://github.com/Unjuno/agent-interface/pull/8867#issuecomment-6207033828)。
[V15選択の結合記録](../../research/integration/owned_service_session_20261016/README.md)では、
旧`8a252071...`の変更を現行の計測・プロトコルguardと結合し、原履歴もtreeを変えず保持した。
旧149件の結果を転用せず、通常・最適化各208メソッド/27モジュールを実行、skipなし。
各10 session行、96 parent source pin、99 sourceのraw/LF別凍結を保存した。
別読取は両modeで通り、各reportの15改変を拒否。所有子56 PIDは確認時点ですべて不在だった。

起動/終了の原本・失敗・出版衝突・初回の解放失敗を残し、後のcleanup成功で昇格させない。
V15オプション試験のbase.mainはスタブで、実wrapper/backend試験はFake Xと所有Python子による。
実session/controller死亡、native解放、環境応答、task effect、matched economicsは未達。
この結合後は旧選択branchを新しい未着手仕事として案内しない。次の整理はモデル/比較評価一族。

### r4（履歴）：#8867の計測変更を現行経路へ収束

基準main `5abbc37e7674d52ef452f08f64bce3b8cb82fd0b`。
#9000はこのmainへ統合済み。#8874は原29ファイルの保全先とログ欠落を示して
[終了](https://github.com/Unjuno/agent-interface/pull/8874#issuecomment-6206880752)した。
元PRを直接mergeした扱いや、#59の研究完了にはしない。r3の517件は処理前の一覧。

#8867の[計測収束記録](../../research/integration/v39_event_timing_convergence_20261016/README.md)では、
ログ開始とstdout受渡しを区別し、controllerのparse/queue/monitor時刻を現行経路へ接続した。
移植時のreader衝突は、現行の重複JSON拒否とcontrol-boundary失敗拒否を残して解消した。
通常・最適化Python各70メソッド/10モジュール、各7保存行、59凍結sourceを確認。
別読取処理も両modeで通り、各reportの11改変を拒否した。実ゲーム/GUI/providerの時間測定ではない。
旧PRの6ファイルは原バイトで残し、追加テスト・現行guard・採用sourceとは区別する。

V15選択branch `8a252071ea7fb5281b9ecc154fa1640136d5345c` は引き続き未統合。
session/controllerの同じファイルが今回変わるため、以前の149件の結果を新mainへ自動転用しない。
取り込み時に正確な差分を結合し、影響する検証と証拠読戻しを行う。
次の整理対象はモデル連携/比較評価のアイデア一族。実制御ではV15選択と実session/controller死亡、
環境応答・タスク効果・matched economicsの不足を残す。

### r3（履歴）：全体整理を優先

基準main `4c63725565f4dea433c49213b8d068c4c762f9bf`。
[r3取得条件](inventory-20261016-r3.json)、[open Issue 1,678件](open-issues-20261016-r3.csv)、
[open PR 517件](open-prs-20261016-r3.csv)。r2から#8876がopen一覧を離れた。
これは全件精査済みという意味ではない。#8876の公開候補と古いRPC境界は
[既存の収束記録](../../research/integration/crash_owner_convergence_20261016/README.md)へ接続する。
一覧は本バッチ公開前の非原子的スナップショット。

[全体計画](../REPOSITORY_CONSOLIDATION.md)に、入口・アイデア/Issue・PR・branch/worktree・
採用実装のそれぞれの完了条件と実行順を追記した。次はモデル連携/比較評価のアイデア一族と
#8867の計測差分を別々の有限なバッチとして読む。Issue数ゼロを完了条件にしない。

#8998/#8999で独立cancel laneと選択backend/Executor custodyはmain統合済み。
[現行adapter証拠](../../research/integration/owned_backend_adapter_20261016/README.md)へwork mapを更新した。
V15/controllerの選択経路はローカルbranch
`work/owned-service-session-selection-20261016`、commit
`8a252071ea7fb5281b9ecc154fa1640136d5345c`に保全してあり、このmainには未統合。
149メソッドの再検証と原rawはローカル専用出力
`new-chat-2/outputs/repository-consolidation-20261015/owned-service-session-final-r2-*`に保持。
単独実行でのimport復元問題を修理したが、正式証拠パケットの読戻しと統合は残る。
このbranchを不要物として削除しない。

#8874の[保存専用照合](../../research/integration/owner_close_a09_preservation_20261016/README.md)では、
公開headの29原ファイルを同一バイトで保全し、元manifestが要求する
`RUNNER/BUILD.log`の欠落を記録する。当時のraw限定監査と、証拠パケットの完全性は別判断。
WSLc/producerは再実行せず、現在source・実機・task effectの成功へ読み替えない。
元の科学的問いと不足は#59で継続する。

以下r2以前の件数と「次」は各時点の履歴として読む。

### r2（履歴）

基準main `8a70a77fc6542d49b03de2f1403b3fd8bcd00397`、取得時刻は
[inventory r2](inventory-20261016-r2.json)。[Issue 1,678件](open-issues-20261016-r2.csv)、
[open PR 518件](open-prs-20261016-r2.csv)を取得した。明示上限未到達・番号重複なし。
非原子的な案内用スナップショットであり、全件の内容・担当・採否を確認した件数ではない。
以前の524件から除かれた6件を[APIで照合](pr-convergence-20261016-r2.csv)した。
6件とも元PR自体はmergedではなく、次の保全・採用先へ収束した。
APIのmerge_commit欄が非nullであってもmerged=falseを覆さない。

| 元PR | main上の実行・保全先と残る問い |
|---|---|
| #7264 / #8370 | #8986、[finite role convergence](../../research/integration/finite_role_recovery_convergence_20261016/README.md)。同一prototypeと独自README文脈を保持。実callerの文書効果adapterは未達。 |
| #7954 | #8985、[callback convergence](../../research/integration/compiled_callback_convergence_20261016/README.md)。post-input verifier/journal例外のprefix・解放・原因保全を修理。耐久的な公開保証とは別。 |
| #8786 | #8987、[presentation convergence](../../research/integration/primary_presentation_convergence_20261016/README.md)。効果後のreply失敗で再送を拒否。実アプリの成功判定は未達。 |
| #8792 | #8988、[saved recovery correction](../../research/integration/v39_hard_recovery_convergence_20261016/README.md)。初期normal/-O記録の回復source不足とv1 false passを保持・訂正。 |
| #8812 | #8967、[saved regression convergence](../../research/doom/v39_saved_regression_convergence_20261016/README.md)。初回FAILと後続CPU結果を原本のまま保全。現行ライブ検証ではない。 |

続く#8989/#8990/#8991/#8992は現在V39 helper→Executor pipe→選択backend/ownerへ
構成確認を接続した。最新の[結合記録](../../research/integration/v39_selected_backend_recovery_20261016/README.md)は
15メソッドを通常/-Oで確認したが、Fake X・注入HUD・制御されたterminal待機に限定される。
次は実session/controllerの死亡時に入力責任が残る境界と、独立したtask effectの検証である。
#8876の保存済みcrash recovery候補を照合する際、古いheadと新mainの全体差分をそのまま採用しない。

[worker work map](../WORKER_WORK_MAP.md)は7つの独立した選択範囲と次の有限な成果へ短縮した。
従来本文は[Git原文のまま保存](../WORKER_WORK_MAP_HISTORY_20261016.md)。
ROADMAPの古いexperiment-first優先指定も現行ゴールの整理・統合優先へ揃えた。
既存の研究Issueの問いは残し、今回新たなIssue closureや実機操作は行っていない。

以下の棚卸し・終了先は先行する時点の履歴である。上のr2を最新の一覧入口として使う。

## 今回確認・訂正したもの

- [全open Issue](open-issues-20261016.csv)：1,678件。番号の重複なし。
- [全open PR](open-prs-20261016.csv)：524件。head SHAとbase branchを保持。
- [前回openだったPRの終了先](pr-convergence-20261016.csv)：14件。APIで直接merge 7件、mergeせず終了7件を確認。
- [取得条件と原export hash](inventory-20261016.json)：Issue取得上限5,000件、PR上限1,000件に達していない。
  最初のIssue exportは1,677件。下記の#5訂正後に1件をAPIから追加し、GitHub検索の1,678件と照合した。
  取得は非原子的。CSVは入口であり、本文・全コメント・担当確認の代用ではない。

[#5](https://github.com/Unjuno/agent-interface/issues/5)は未完了とする最新コメント・agendaに反して
completedで閉じられていたため再オープンした。#8937はFake Xのprocess identity接続の一部を検証した成果であり、
visual addressing/feedback全体の完了ではない。原議論と既存agendaを継続先として維持する。

## 終了したPRの移管先

| 対象 | 処理・現在の実行先 |
|---|---|
| #6934 | #8965で固有のWin32 custody修理と184原証拠ファイルの保全を照合。旧PRは後継へ収束。native操作の合格ではない。 |
| #7109 | #8953へ証拠を収束。過去のblocked-I/O/GIL境界の結果を現行の物理解放保証へ読み替えない。 |
| #7296 / #8764 | #8764をmainへ統合し、#7296を終了。wake-pipe証拠と独自差分を保持。 |
| #7981 | mainへ統合。FAIL_CROSS_CLIENT_ISOLATIONを維持。 |
| #8384 | #8956へ15原ファイルと監査修理を収束。構成PASSをライブPASSにしない。 |
| #8723 / #8707 | #8701のstackへmerge。**#8701はopenでmain未統合**。A07原rawの保管元監査が残る。 |
| #8801 / #8814 | #8933で共有rawと各独自追試を保全して終了。 |
| #8834 | Windows匿名pipeの修理をmainへ統合。GUI実行ではない。 |
| #8839 | #8946で現行launcherへ収束。古い実装で後続修理を上書きしない。 |
| #8866 / #8871 | mainへ統合。typed healthの早期検出・解放の条件と限界は各packetに保持。 |

個別merge/終了時刻・元headはCSVから辿る。終了件数だけを採用成果やmain反映件数に換算しない。

後続の[#8812収束記録](../../research/doom/v39_saved_regression_convergence_20261016/README.md)では、
A11の初回FAILとA12の保存済みCPU結果を原48ファイルのまま保全した。
当時のsource 34件中11件は現在の基準mainから変わっており、現行制御の検証として再利用しない。
保存結果の別監査と改変拒否を使い、消費済みのproducerは再実行しない。

## 実行する整理バッチ

### 後続の統合・証拠所在の照合

後続のmain `de7bcbf86316b312e3a34c9b15b07336caaa14ff`では、#8971の保存専用X11候補保全、
#8972の割込み時cleanup、#8973のMCP割込み証拠、#8974の同一backend内session回復custodyを統合済み。
各packetのFake X・単一process等の限定を維持し、実機の有限解放やtask effectの達成とはしない。
このmainで14作業ツリーの追跡変更・未追跡ファイルがゼロであることを確認したが、
無視対象・他者の所有権・リポジトリ全体の整理完了を証明するものではない。

[caller一族の現行照合](../../research/integration/caller_current_main_convergence_20261016/README.md)では、
#7289/#7310はclosedで、両headと合成commitがこのmainの祖先であることを確認した。
PR自体のmergeとは区別し、現行callerで19モジュール・76テストを通常/-Oで実行、
各221保存行の会計・完了prefix・未検証効果の整合を別読取処理で確認した。
古いcaller合成待ちやレビュー人数待ちは現在の不足ではない。#57はアプリ効果・実provider会計・
同条件比較と移植の未達を維持し、新たなIssue closureは行わない。

main `2b9df51535c7662d76ac29477bb14e2219eb9865`までに、次の有限な整理を進めた。

| 対象 | 現在の処理と残差 |
|---|---|
| #8812 / #8967 | 保存済みA11初回FAILとA12 CPU結果を原48ファイルのまま収束し、#8812を後継付きで終了。現在sourceで当時の結果を更新しない。 |
| #8968 / #8969 | 公開guarded MCPと選択MAP01/V12のwindow lifecycle経路を別々に構成検証してmainへ統合。#8969の保存済み通常・最適化各58モジュール/427メソッドには各12 skipがある。実機・task effectの合格ではない。 |
| #4008 | 本文と全3コメントを照合。36ケースの結果報告と217ファイルのローカルpackage検証はあるが、予定packetはこのmainにない。元branchの現remote refも取得されず、Issue番号検索で出版PRを特定できなかった。別名・未公開原本の不在は証明していない。公開・読み戻しが未完了なのでopenを維持する。 |
| #8701 | source head `ce6724b870696916d8d421e20d9bcd18362af88c`のopen PRを再確認。v2/v3はstackに保存済みだが、元A07の2,358ファイルと保存済みepisode監査の照合が残る。synthetic結果だけでmainへ統合しない。 |

#8969統合後のprimary mainは上記SHAへfast-forwardし、14作業ツリーは追跡変更・未追跡ファイルともゼロだった。
この整理作業自身の統合済みfeature/integration refだけを、tip・main包含・open head/base依存・作業ツリーを確認して除去した。
他者のbranch・無視対象・保全候補は保持する。以下の全件CSVは取得当時の履歴であり、上記変更後のlive件数ではない。

既存の[作業マップ](../WORKER_WORK_MAP.md)のテーマを使う。新しい調整Issueやサービスは作らない。
各バッチは「対象を読む → 固有の残差を抽出 → 必要なローカル検証 → 統合/終了 → 参照を戻す」で一巡する。

| 順 | 対象・編集先 | 終了条件と次の作業 |
|---|---|---|
| 1 | 未統合PRの一族、上記PR CSV | 元head・固有差分・原証拠・依存を照合し、現在mainへ採用する部分を局所検証して統合。重複は保存先と残る実行先を示して終了。まず#8701の保管元raw、既存保全commitの世代/scorer差分を照合。 |
| 2 | #3/#5/#8、`docs/ideas/visual-interface-agenda.md` | 仮説ごとに既存結果・残差・次の判別を更新。次は同processでのwindow再利用とsubscription coverageの境界。Fake X構成とライブ資格を区別。 |
| 3 | #2/#10/#14/#15/#16/#17、`docs/ideas/safety-control-agenda.md` | process/backend間の未解放入力custodyとblocked native I/Oを既存の修理・反例へ接続。有限回復や物理解放時間を未測定のまま完了扱いにしない。 |
| 4 | #57/#59/#2789とドメイン別の関連Issue | 観測・環境応答・task effect・回復・比較会計を分け、同じ問いの実行記録は親へリンク。Calcの保存済み4ケースとmatched economicsの不足を区別。 |
| 5 | 残りのIssue、`docs/ideas/`と研究map | 一つのテーマずつ本文/コメント/関連PRを読み、固有仮説・結果・依存・次の検証を整理。タイトル分類だけでcloseしない。 |
| 6 | branch/worktree、既存custody記録 | 最新tip・固有commit・dirty/ignored/raw・利用者・head/base依存を確認。保全済みかつ不要と確定したものだけ削除し、読み戻しとmainの状態を再確認。 |

バッチ1と2〜5は独立したファイル・問いを選べる。同じ索引や共通runtimeを編集する場合だけ重複を調整する。
文書の共有ファイルを全員で変更することや、全体整理完了を各ワーカーの着手条件にしない。

## 「クリーン」の完了確認

- [ ] 現在の入口から、各研究テーマの仮説・採用実装・保存結果・未解決点・次の実行先へ辿れる。
- [ ] open Issueごとに、未完了の問いか具体的作業がある。完了/重複/移管済みは根拠と継続先を残して閉じる。
- [ ] open PRごとに、固有差分・統合先・必要な局所検証・残る阻害条件を判定済み。古いbaseから新実装を消す統合がない。
- [ ] 不要なreview人数や全員待機を要求する現行案内がない。実際の権限・protectionと変更に必要な確認を使う。
- [ ] 未保存変更や唯一のrawがなく、削除したref/worktreeには保全・未使用・依存確認の記録がある。
- [ ] primary mainと作業終了ツリーがクリーン。統合内容に応じたローカル検証が成功し、未検証境界を明記している。

「作業ツリーの変更ゼロ」「全成果の整理完了」「コンピューター制御の研究達成」は別々の状態として報告する。
新規allocationや実GUI操作は今回の整理では実行していない。

## #8876 crash-owner candidate convergence

[The preserved candidate and counterexamples](../../research/integration/crash_owner_convergence_20261016/README.md)
retain all614 published changed-path head blobs plus seven dependencies without
adopting the old runtime. Exact codec/client AST drops current process/window
sources and permits a new down send after timeout, wrong-ID reply or malformed
record failure. The selected current Fake X owner refuses the decoded lease;
original bound-lease admission/release is the positive control. Three methods /
seven rows per normal/-O mode and saved readback are local construction only.
A35 identity/hashes match; A36/A37 keep their allocation-ID STOP. Continue current
service authority/quarantine and session-death integration under#59; no old
allocation was replayed, and native/game/task-effect qualification remains open.

## Current-owner RPC v2 repair boundary

[Real private sockets plus current strict owner on Fake X](../../research/integration/current_owner_rpc_v2_20261016/README.md)
now preserve source binding and permanently refuse new sends after unknown
replies. Normal/-O each41 methods across5 modules retain26 rows and46 source pins;
blocked release stays unverified. This is an explicit library, not the default
MAP01 owner: external service process/durable receipt, backend custody adapter,
parent cancellation/telemetry and actual session/controller death remain under#59.
The unsupported window observer transfer is refused rather than downgraded.

## Owned process continuation

[Owned service v3](../../research/integration/owned_owner_process_v3_20261016/README.md)
adds the explicit spawned service and exclusive file-fsynced recovery/finish
receipts. Normal/-O each55 methods preserve13 process/inert rows and26 RPC rows.
Client death releases through EOF; unresolved release retains the service even
on publication failure; file success alone never replaces owned-process exit.
The preceding RPC paragraph records its earlier boundary. The remaining#59 work
is selected backend/Executor custody, cancellation/telemetry and actual session
death. This is Fake X construction, with no native/task-effect qualification.

[The actual selected backend/Executor comparison](../../research/integration/owned_owner_executor_boundary_20261016/README.md)
now rejects metadata-only RPC substitution: parent cancellation releases the
local owner during a paused worker, but remote input remains pressed in the fixed
diagnostic window until the worker sends again. Both final cleanup and ordinary
remote completion succeed, which does not repair independent cancellation.
Three cells normal/-O,49 source pins and nine saved-record negatives per mode
preserve this distinction. Next implement the independently serviced intent-bound
cancellation/cause relay, then explicit backend selection under#59.

[The independent cancellation lane](../../research/integration/owner_cancel_relay_20261016/README.md)
now repairs that explicit relay boundary: actual backend/Executor receives the
matching parent-lease release cause while the worker is paused or an ordinary
reply is in flight. Normal/-O each70 methods retain the original counterexamples,
11 new cancellation rows,51 parent pins and frozen loaded sources. First failed
release outcomes remain unverified after late cleanup; wrong generation/control
loss retires admission. Default backend selection is unchanged. Next connect the
production backend custody adapter, preserving first control failure and original
source/cause, then qualify controller/session death and native/task effects.

[The selected-backend owner adapter](../../research/integration/owned_backend_adapter_20261016/README.md)
now connects explicit owned service selection to the actual process-identity
Backend/Executor. Inherited binding reads validated remote geometry, source is
frozen before sends, and whole-program capability checks precede input. A first
unverified control result remains failed through late successful service exit;
the original Executor and a replacement Executor both refuse new authority.
Normal/-O each106 methods across13 modules pass. Parent capture PNG/.ait and child
raw are retained, with independent PNG reconstruction/source/custody readback.
Default V15/controller selection and controller/session death cleanup remain the
next#59 integration; no native input/task/economics qualification is implied.
