> Start with [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for project goals and gate order; use [PROJECT_STATE.md](PROJECT_STATE.md) for detailed result status. This plan tracks inventory, family triage, and evidence/worktree custody.

## Project-wide cleanup status — 2026-11-23

The repository is not clean yet. Keep product qualification and repository
triage as two linked workstreams: the first protects acceptance gates; the
second reconciles issue/PR meaning and evidence custody without bulk closure.
The latest complete paginated membership baseline is r173 (1,640 Issues / 405
PRs), bracketed by stable main `bc903f77bd69102187329f9e0d020ca5259f88bb`.
Compared with r172, both exact sorted ID sets are unchanged. The prior r172
Markdown receipt contains literal main-SHA placeholders; its JSON is intact,
and r173 records the independently confirmed ref. See the [r173 receipt](maintenance/repository-inventory-recheck-20261123-r173.md)
and [exact-ID data](maintenance/repository-inventory-recheck-20261123-r173.json).
Earlier r168 was count-only. Semantic issue/PR disposition remains incomplete
and must proceed family by family.

**Current-main recheck r171 (2026-11-23; main `953ce41370666c656278f203dc545aa310947ffe`):** Complete pagination still returns 1,640 open Issues and 405 open PRs. The exact sorted ID sets match r170 with no additions/removals, bracketed by the same main SHA before and after. PR #10478 was merged; its appearance and removal happened between complete snapshots, so it does not change the current set. This does not advance semantic triage. See the [r171 receipt](maintenance/repository-inventory-recheck-20261123-r171.md).

**Current-main recheck r172 (2026-11-23; main `b600070965c48cc9449a87ff31264a5b3604c2d8`):** Complete pagination returns 1,640 open Issues and 405 open PRs. Both exact sorted ID sets match r171 with no additions/removals; main was unchanged around the reads. This membership refresh does not advance semantic triage. See the [r172 receipt](maintenance/repository-inventory-recheck-20261123-r172.md).

**Current-main membership recheck r173 (2026-11-23; main `bc903f77bd69102187329f9e0d020ca5259f88bb`):** Complete pagination again returns 1,640 open Issues and 405 open PRs. Both exact sorted ID sets match r172 with no additions/removals; the main SHA was stable before and after reads. This does not advance semantic triage. See the [r173 receipt](maintenance/repository-inventory-recheck-20261123-r173.md).

## Local worktree custody recheck r173

At main `bfddb91a39b4fefeff4a6de22c55fd661936dc62`, the local Git registry contains 22 worktrees: 14 clean and 8 dirty. The dirty set includes a main checkout with 21 changes, several untracked experiment packets, one worktree with a changed test/output, one detached audit with two changed raw logs, and the active preview audit's nested `.worktrees/` residue. Preserve all of them until owner, PR/Issue linkage, exact content hashes, and duplicate status are reconciled. No cleanup or reset was performed. See the [r173 custody receipt](maintenance/local-worktree-custody-recheck-20261123-r173.md) and [exact status snapshot](maintenance/local-worktree-custody-recheck-20261123-r173.json).

**Root worktree blob match audit r174 (2026-11-23; current main `f9042aa3`):** The dirty root `main` checkout is 170 commits behind and has no commits ahead. Three of its 11 tracked modifications are byte-identical to current-main blobs and other registered worktree commits; eight tracked modifications did not match any registered HEAD. The three stale-base markers do not make the root clean; its remaining edits and ten untracked paths are preserved pending ownership/custody review. See [r174](maintenance/local-worktree-blob-match-20261123-r174.md).

### Caller/runtime composition update - 2026-11-23

R01 connects adaptive caller v3, the bounded compiled GUI runtime, and a separate outer task scorer in one synthetic positive/changed pair. It passes the focused composition tests and the related caller/core regression suites in normal and -O. The requirement-to-test crosswalk identifies the exact missing live-v3 repetition before a matched economics allocation. See [the plan and crosswalk](maintenance/issue57-composition-plan-and-requirement-crosswalk-20261123.md) and [R01 packet](../research/integration/issue57_adaptive_caller_compiled_gui_composition_r01_20261123/RESULT.md).

### Product-gate evidence update   -  2026-11-23

R06 and R07 now add two adjacent synthetic App Server-to-ProspectiveRun custody shapes: timeout after observed usage, and explicit interrupted terminal after observed usage. Both retain attempt identity/accounting and fail closed at task projection with dispatch disabled. R07 passes its focused case and all 11 transport tests in normal and -O; its evidence and setup failure custody are in [R07](../research/integration/issue57_v3_durable_appserver_composition_r07_20261123/RESULT.md). These tests do not resolve live provider accounting, matched integrated economics, public recovered-task reliability, Research Preview graduation, or runtime distribution acceptance. Repository organization is still incomplete; this update does not authorize bulk issue closure.

### Current project map

| Workstream | Current evidence | Remaining gate |
|---|---|---|
| Integrated control / #57 | PR #10470 merged; R22 passes 94/94 affected MCP tests in both modes; R23 Fake lifecycle passes 10/10; current-main R03 Fake App Server/public-MCP/Calc composition passes 1/1 normally and under `-O`; R24/R26/R27 are native Win32 expiry/recovery fixtures, with R27 3/3 under exact foreground activation. Historical frozen-source `integrated-efficiency-live-01` is a scoped three-arm pass (6/6 each; task-2 token break-even); PR #10473 retains R24-R27. Synthetic durable provider join R01 passes 2/2; ProspectiveRun boundary R02 keeps four incomplete outcome envelopes at HOLD; R03 passes a synthetic failed-attempt/usage join to registered custody (3/3 normal and `-O`); R04 passes synthetic deferred and unknown-usage cases (4/4); R05 projects one synthetic success/effect row with audited receipts (5/5); R06 audits and projects all 18 synthetic assignments and reaches evaluator `RETAIN` (6/6). | The three-arm result is one older-source allocation, not current-main standard-caller evidence. Source actions remain UNKNOWN after post-expiry effects; no eligible recovered task success or current-source integrated provider comparison. R02 does not use authentic v3 outputs; R03-R05 remain synthetic and cover only one task at a time. R06 closes only offline full-trace composition; its economics are fabricated inputs. Real provider, GUI/task effect, standard-caller recovery/reliability and cleanup remain open. Next verify a fresh exclusive allocation before any live matched run. Keep #57 open. |
| Research Preview / #58 | Runner/setup and archived-source checks are partial; current host doctor/live prerequisites remain unmet. | Supported-host setup/doctor, retained audit, fresh no-retry live run and final live audit. |
| Real-time control / #59 | R153/R154 and R157/R158/R161 contain scoped native Win32 recovery/release/effect evidence; R156 remains FAIL/UNKNOWN and R160 a runner failure. Current-main R01 found no GZDoom in six standard paths, `PATH`, running processes, or uninstall registry; it did not search the full disk or establish IWAD availability. | Reacquire the isolated executable and intended IWAD/map before another live attempt. Preserve #59 priority; do not claim integrated threat exposure or MAP01 completion. See [R01](../research/integration/map01_preinstalled_target_preflight_current_main_r01_20261123/RESULT.md), [R153–R156](../research/integration/map01_recovery_deep_trace_r153_r156_20261113.md), and [R160/R161](../research/integration/map01_recovery_deep_trace_r160_r161_20261113.md). |
| Runtime distribution | Deterministic package/startup and outside-checkout CLI checks passed on declared hosts in retained packets. | Live authority/input behavior and public artifact on declared supported environments. |
| Research ideas | r160 idea-index crosswalk and targeted family reviews exist; they are not current semantic triage. | Refresh membership; adjudicate one family at a time, retaining viable ideas and closing only with evidence-backed disposition. |
| Branches/worktrees/artifacts | Read-only local recheck r169 found 21 worktrees (14 clean/7 non-clean) and 12 files under the workspace-root `outputs/`. Two dirty branches correspond to merged PRs; other dirty trees include main and detached checkouts. | Custody remains unresolved for seven non-clean trees. Identify owners and link changed bytes to branch, PR, issue and hashes before consolidation or deletion; do not clean them automatically. See [r169](maintenance/local-worktree-custody-recheck-20261123-r169.md). |

### Execution sequence

1. Finalize the running scoped experiment and preserve failures. R16 is now
   finalized as a failed broad check in its own evidence packet.
2. R17/R18 isolated and grouped checks passed; R19 reproduced failures on the
   D: temp location; R20 passed the full module on dedicated C: TEMP. Retain
   both failure and success contexts; use the qualified C: path for local
   validation and proceed to public standard-caller recovery/effect evidence.
3. R24-R27 now provide scoped native expiry/recovery evidence; R01/R02 add a synthetic failed-usage join and a fail-closed incomplete-envelope boundary. Do not repeat
   the same delayed fixture. Continue only with an eligible standard-caller task
   outcome or the matched efficiency/accounting seam.
4. Keep #59 live threat exposure in view; the local GZDoom/WAD search was empty
   in the searched roots. No installation/download was performed.
5. Refresh complete Issue/PR membership, then triage families with evidence
   and custody links. r167 is membership only; r160 is an older navigation map.
6. Reconcile worktrees, branches and outputs by path/hash and references;
   remove only exact duplicates with resolved custody. Reassess #58/package
   gates. Keep #57, #58, #59 and the project goal open until proven complete.

**Evidence custody reconciliation (2026-11-23; current main `cd708f52`):** Restored the byte-exact R06/R07/R08 Win32 fixture packets referenced below from a clean tracked worktree after checking each packet's root manifest against its raw files. Current copies verify R06 38/38, R07 23/23, and R08 69/69 entries. R06's working bytes differ from the main index only in line endings (`git diff --ignore-space-at-eol` is empty); preserving the manifest-matching bytes is required for raw custody. No result was replayed or re-scored. A separate current-main local recovery composition result is [R01](../research/integration/standard_mcp_task_ledger_57_v1/current_main_recovered_caller_task_oracle_r01_20261122/RESULT.md); it does not establish public recovery or efficiency. The GraphQL count-only check at 2026-11-22 14:55 UTC returned 1,640 open Issues and 405 open PRs, but no exact-ID or semantic recheck was made; r165 remains the latest full membership receipt.

**Latest membership check r164 (2026-11-22; main `48ef3e498b287a69b68e3e6912a43db2acb3551b`):** Exact paginated ID reads returned 1,640 open Issues and 405 open PRs. Compared with r152/r157, there were no additions; Issues #7748/#7765/#7817 and PRs #7968/#8181/#10227 were removed. This resolves the two-PR delta noted after r163. The full receipt is [r164](maintenance/repository-inventory-recheck-20261122-r164.md). Membership is not semantic triage or a reason to close anything.

**Latest full membership receipt r165 (2026-11-22; main `d5ada452`):** Exact sorted-ID hashes match r164 at 1,640 open Issues and 405 open PRs. Current main subsequently moved to `cd708f52`; a 2026-11-22 14:55 UTC GraphQL count-only check returned the same totals, but did not establish exact membership. Keep r165 as the latest full membership audit; do not imply the live count read completed whole-queue triage.

**Additional linked evidence restored (2026-11-23):** The [R16 packet](../research/integration/win32_native_sendinput_recovery_20261122_r16/RESULT.md) verifies 42/42 manifest entries. The [supplemental Research Preview build packet](../research/integration/research_preview_retained_source_audit_r01_20261122/supplemental-linux-build-r06-20261122/RESULT.md)'s local files verify against its manifest, and a fresh Ubuntu WSL read confirmed the 349,878,418-byte archive has the recorded SHA-256 `73147dc192c7b472a47a4730b7886fe297beb75182cad2f677b368232ae38ef8`; the archive remains in WSL output storage, outside Git. These reads did not replay an experiment or alter its recorded outcome.

**Project status handoff (2026-11-22; main `48ef3e498b287a69b68e3e6912a43db2acb3551b`):** The one-page [project state dashboard](PROJECT_STATE.md)
distinguishes main-verified gates, integrated repairs, live evidence gaps, and
repository custody work. R08 preserves one complete no-provider Win32 public
caller run and an offline measured-run/effect-handoff reconstruction. Three
adapter repairs are now on main via PR #10451; five comparison/effect/owner
suites pass 70/70 normally and under `-O`. This remains one fixture result, not
matched efficiency or recovery evidence.
See [R08](../research/integration/win32_recorded_task_effect_r08_20261122/README.md),
[R07](../research/integration/win32_recorded_task_effect_r07_20261122/README.md),
and the [R02 synthetic adapter result](../research/integration/standard_mcp_task_ledger_57_v1/public_win32_effect_pair_handoff_r02_20261122/RESULT.md).

**Prior whole-repository checkpoint r163 (2026-11-22 JST; main `1afb532ea153f3da3906764753909fac074afce3`):** Complete paginated reads found 1,640 open Issues and 407 open PRs. The later exact-ID r164 receipt reconciles its two-PR count difference. Membership remains distinct from semantic review and custody reconciliation. The r160 semantic crosswalk is still the latest full routing analysis. Issue #57 remains open for matched live efficiency, standard-caller task success/recovery reliability, Research Preview graduation, and distributable-runtime acceptance. See [r164](maintenance/repository-inventory-recheck-20261122-r164.md), the [r163 receipt](maintenance/repository-inventory-recheck-20261122-r163.md), and [r160 crosswalk](maintenance/idea-index-crosswalk-20261121-r160.md).

**Worktree custody recheck (2026-11-22, after PR #10427):** A read-only audit found 15 registered worktrees: ten clean and five dirty. The 70-commit-behind parent checkout contains unclassified changes and output; four other dirty checkouts contain Calc historical results, a WSLc read-only probe, a Research Preview fixture result, or modified audit raw. Root `outputs/` contains 61 unique files, while the 16-file ledger `outputs/` directory matches current-main blobs; attempted removal of that exact duplicate directory was rejected and it remains untouched. No cleanup was performed. Follow the item-by-item custody sequence in [the recheck report](maintenance/worktree-custody-recheck-20261122.md) before deleting branches or files.

**Targeted PR/Issue recheck (2026-11-22):** Draft PR #10144 remains OPEN/Draft at head `a17b7fe8`, base `22362cb7`; it has 44 PR commits against 445 current-main commits from the common base, only `replay-gate` is listed as passing, and mergeability is UNKNOWN. Its stated lifecycle, release, scoring, and matched-trial requirements remain unmet; preserve it as a research prototype, do not merge or dispatch from it. Issue #7773 remains OPEN at `HOLD_NO_CANDIDATE_LIST_CONSUMER`; targeted current-main source search found no candidate-list consumer and the relevant source files are unchanged since the previous HOLD. See the [targeted recheck](maintenance/targeted-organization-recheck-20261122.md). This covers two items only, not the whole queue.

**#58 acceptance runner merged and locally rechecked (2026-11-22; main `d1a92e04c47b4dbf88e4c784c3dfdfea16bb8e10`):** PR #10440 fixes existing-venv reuse and explicit install opt-in; focused suites pass 9/9 normally and under `-O`, while replay-gate passes and formal is skipped. This is a runner repair only. Windows Codex CLI JS and WSL Chromium remain unverified; #58 remains open. See [the retained update](https://github.com/Unjuno/agent-interface/issues/58#issuecomment-7075513226).

**#58 current-main acceptance-runner R01 (2026-11-22):** On the frozen RC1 checkout, current-main runner preflight passed 19/19 and existing venv reuse was recorded without installation; doctor retained 12/15 with the expected Windows CLI JS / Chromium / downstream Codex CLI failures. No live allocation, retained audit, GUI or model call occurred. Evidence and file hashes are under [R01](../research/integration/research_preview_rc1_setup_doctor_r05_20261121/current-main-runner-r01/RESULT.md); #58 remains open.

**#58 current-main prefix R02 and retained-source audit (2026-11-22):** On exact main `10b47b4b4edf283ed2b28f19bbeb9de4b9cf9b51`, official launcher preflight passed 19/19 and setup correctly held for explicit dependency-install opt-in. Supplemental read-only doctor was 12/15; retained audit failed on seven current-source hashes while the retained result remains `RETAIN`. Keep the two prerequisites distinct and preserve the mismatch for source-custody diagnosis; no live action or install occurred. See [R02](../research/integration/research_preview_rc1_setup_doctor_r05_20261121/current-main-prefix-r02-20261122/RESULT.md). #58 remains open.

**#58 frozen-source audit repair candidate `2552fe76` (2026-11-22; main `128c33f2`):** The archive and preregistration verify 29/29 frozen files; seven source files have later content changes after line-ending normalization. The current retained audit passes from the frozen archive; local runtime and bundle-builder suites pass 5/5 normally and under `-O`. Evidence and checksums are in [R01](../research/integration/research_preview_retained_source_audit_r01_20261122/RESULT.md). Keep #58 open for supported-host setup and fresh live acceptance.

**#57 Win32 standard-caller fixture R05 (2026-11-22):** Third fresh scripted task-effect sample completed with verified input release and 2 s late-input horizon; a separate oracle observed the delayed text effect. The caller still returned `task_success=null`, so do not count this as end-to-end task-success or reliability closure. The focused Win32 backend/producer/MCP suites pass 27/27 normal and `-O`. Raw/conditions/hash custody: [R05](../research/integration/win32_current_main_fixture_effect_r05_20261122/README.md).

**#58 local WSLg host prerequisite probe (2026-11-22):** Ubuntu WSL2 has WSLg display/socket, Xvfb, and Python 3.12.3, but no Chromium/Node; apt has no `chromium` candidate, and noninteractive sudo is unavailable. Windows Node and Codex app are present, but the bridge is untested. This is not the frozen setup/doctor gate; no package install or allocation occurred. Record the host-state change (Ubuntu started for the probe), leave the golden gate open, and do not consume a fresh allocation until prerequisites and bridge are verified. Full details are in the [targeted recheck](maintenance/targeted-organization-recheck-20261122.md).

**B13 #7794 evidence custody (updated after PR #10431):** The unique A01/A02 files from Draft #7968 are now on main byte-for-byte with SHA-256 manifests; #10431 merged and #7968 was closed as superseded, with its branch/history retained. A05's byte-bound successor passes its own current-main 12/12 manifest audit; A04's metadata mismatch remains. Keep parent #7794 open at `HOLD_ACCOUNTING` for missing real workload, metered energy, carbon-boundary evidence, and the unresolved comparator distinction. See the [custody audit](../research/analysis/carbon_window_7794_a01_a02_import_20261122/CUSTODY_AUDIT.md) and [B13 crosswalk](maintenance/idea-index-crosswalk-20261121-r160.md).

**Prior full whole-repository checkpoint r160 (captured 2026-11-21 at main `f39e966b6478170a7a91f1eec7859d30046784bf`; crosswalk base `87f1afe2ad2202a3a5200a4add86190e9f6a1496`):** Complete paginated open Issue/PR reads found 1,643 Issues and 408 PRs, byte-identical to r159 with zero additions/removals; PRs #10402/#10403 had already merged. The r160 ID sets remain the frozen baseline. Evidence reviews later closed #7748 at its finite synthetic-method scope and #7765 after its audited held-out `FAIL_NO_GAIN`. The r160 current-main navigation recheck found all 1,643 open Issues linked in at least one of the research-index primary table or `IDEAS_AND_OUTCOMES.md`; 459 lacked a primary research row at that time. The crosswalk's B01–B12 counts and their interpretation are a dated routing snapshot, not current semantic dispositions. See the [r160 receipt](maintenance/repository-inventory-recheck-20261121-r160.md) and [crosswalk](maintenance/idea-index-crosswalk-20261121-r160.md).

**Issue #57 G10 reuse-boundary audit (2026-11-21; based on main `ce6449f38a56e1731f01d1024837fb34c9c759a3`):** The retained Calc G10 archive remains useful as a narrow live positive control. A source-pinned read-only audit checked its 33 declared source hashes and 69 run files; the current comparison adapter rejects the old raw record because it has no reconciled caller receipt/event ledger, and primary provider usage is UNKNOWN. Preserve the record and do not adapt unknown usage into zero. The next comparison must be a fresh matched block through the standard caller, with cold/warm/invalidation/repair and all-attempt usage. See [the R01 crosswalk](../research/integration/g10_current_main_comparison_readiness_20261121/RESULT.md).

**Issue #57 composition evidence custody (2026-11-21; PR #10396 merged):** The packet binds the normal/-O synthetic adapter-to-horizon test, explicit TEMP policy, raw results, and checksums in one directory. It is linked from the current goal and roadmap. The merge integrates this offline check only; keep #57 open for live efficiency, task outcome, and recovery evidence.

**Preference-evidence dependency check (#7790 / #8859; 2026-11-22):** The
merged #7923 A01 is a scoped synthetic admission-method result only. A
current-main source search across `runtime/core_v1`, `runtime/cli_v1`, and
`runtime/guarded_x11_v1` found no preference/personalization consumer; this
search does not establish that no such path exists elsewhere. More decisively,
the linked #8859 agenda requires independently classifiable successful #57
traces before any blinded preference assay, and #57 still lacks its matched
live comparison/task-success/recovery gates. Reuse #7790's audit without
replaying it. Read-only #8859 feasibility audit R01 classified all six calls
in one retained synthetic positive trace as required; there is no comparable
successful pair, and other candidate traces lack complete all-attempt usage or
real provider evidence. Hold a preference study until at least two matched
successful traces satisfy caller/provider usage, effect, and release gates.
See [R01](../research/integration/standard_mcp_task_ledger_57_v1/efficiency_trace_feasibility_r01_20261122/RESULT.md).
No runtime behavior or issue state changes follow from this audit.

# Repository organization plan

**Latest membership checkpoint r167 (2026-11-23 JST; current main `490d7bcb4d84927116112e5ff348cdeadfc489d6` before and after reads):** Complete paginated GitHub reads found 1,640 open Issues and 406 open PRs. Issue IDs match r166; the only PR-set addition is #10473, with no removals. This updates membership only. The r160 crosswalk remains the latest full semantic-routing review, so queue cleanup and custody reconciliation are incomplete. See the [r167 receipt](maintenance/repository-inventory-recheck-20261123-r167.md), [exact-ID JSON](maintenance/repository-inventory-recheck-20261123-r167.json), and [r160 crosswalk](maintenance/idea-index-crosswalk-20261121-r160.md).

**Issue #57 Calc evidence crosswalk (2026-11-23):** The G10 retained OCR/compiled-graph result remains a narrow positive control; its historical record lacks a current-schema caller receipt and primary provider usage. Current research code already contains a durable allocation composition with offline synthetic coverage. This does not establish live provider bindings or matched economics. Reuse it for the next provider-attempt/accounting audit; do not repeat or retrofit the consumed G10 allocation. See the [crosswalk](maintenance/issue57-calc-evidence-bridge-audit-20261123.md).

**Issue #57 Win32 standard-caller fixture update (2026-11-22):** Current-main R01 isolated a producer receipt capacity mismatch; after the minimal fix, fresh R03 completed one key action, verified input release, observed no late input for 2 s, and independently recorded a 6 s delayed task effect. R02 remains an explicit foreground-refusal/recovery attempt. These three packets preserve each attempt and its distinct outcome; do not pool R01/R02 into the positive result or treat this fixture as MAP01, efficiency, or repeated reliability evidence. See [R01](../research/integration/win32_current_main_fixture_effect_r01_20261122/README.md), [R02](../research/integration/win32_current_main_fixture_effect_r02_20261122/README.md), and [R03](../research/integration/win32_current_main_fixture_effect_r03_20261122/README.md).

R04 supplies a second independent fixture pass under the same fixed protocol; it preserves a fresh process/window and its own MCP receipts. R03/R04 are two descriptive task successes, not an estimated reliability rate. See [R04](../research/integration/win32_current_main_fixture_effect_r04_20261122/README.md).

**Issue #57 evidence custody (2026-11-21):** Two X11 follow-up packets now
preserve the WSL TCP transport-identity HOLD and the passing isolated Docker
Unix-socket normal/`-O` queue pair. Both are separately source-pinned and
audited; neither changes the open Issue's product or research gates. Link them
from the current goal and roadmap, and keep the next worker item scoped to
standard-caller recovery/effect composition rather than repeating Xvfb queue
drainage.

**Issue #57 standard-caller evidence wave (2026-11-21):** Preserve the distinct
R01 runner-metadata deviation, R02 normal/optimized split, R03 3/3 optimized
XRes timeouts, R04 one-second diagnostic, and R05 500 ms candidate. The candidate
records improved disconnect/release observation while retaining the old task's
held-A repeat failure and UNKNOWN/no-replay; the scheduled delayed B KeyPress
was not observed. Keep the raw attempts, conditions,
source pins, and audit together; do not merge a green unittest into a task-success
claim. The next bounded item is public-result semantics plus late-request
quarantine, with a separate writable path and no overlap with the MAP01 or
provider-efficiency allocations.

**Issue #57 evidence update (2026-11-21):** The latest current-main focused
recheck after PR #10368 passes normal mode but fails under `-O` at the existing
3 s Save boundary and terminal receipt wait. Preserve it as a scheduling
sensitivity result; do not widen timeouts without boundary-state evidence.
The raw logs and limits are in
[the focused cancellation packet](../research/integration/standard_mcp_task_ledger_57_v1/current_main_cancel_boundary_recheck_20261121/RESULT.md).

**Issue #7728 / PR #7758 targeted disposition (2026-11-21):** The exact PR
head remains draft and is `DIRTY` against current main; its A01 runner-custody
and A02 stale-base holds remain. Both synthetic audit suites pass 3/3 normal and
3/3 under `-O` on the exact PR head. Preserve the packet, do not merge or rerun
the one-shot sensor observations, and keep #7728 open. The PR's stated two
non-author approval quota conflicts with the current Worker Quickstart and is
not enforced by GitHub protection, but is not the reason this old head cannot
integrate. A fresh evidence/navigation-only successor is the safe path if this
family is resumed. See the
[disposition record](maintenance/pr7758-disposition-20261121.md). This is one
targeted B13 family review; the full B13 batch and whole-repository semantic
triage remain unfinished.

**Issue #7722 / PR #7735 targeted disposition (2026-11-21):** The frozen
synthetic T0 hypothesis failed despite a 71–77% p99 response reduction because
1–3/10 control deadlines were still missed per schedulable trace. The original
audit PASS was superseded after defects; the issue's later correction reports a
separate read-only 18-run reconstruction and eight mutation classes, with zero
formal reruns. PR #7735 remains Draft and 4,062 commits behind current main.
Preserve the historical packet; do not rerun or infer host scheduling/GUI
release behavior. Keep the Issue open while deciding whether to close only its
synthetic T0 hypothesis; any OS/GUI follow-up is separate. See the [B13
crosswalk](maintenance/idea-index-crosswalk-20261121-r160.md).

**Issue #7732 / predecessor #6774 targeted disposition (2026-11-21):** Keep
#7732 open but execution-held on its explicit custody dependency. #6774's
nine-row packet has seven recorded-vs-published hash mismatches that disappear
when the final CRLF is excluded (cause unknown), and an auditor that cannot parse its terminal blank line; the
separate 12-row packet matches its manifest but lacks independently attributable
executor identity. Preserve both histories and #6775's merged bytes; do not
repair/replay the consumed allocation or normalize evidence. Any later #7732
experiment is a separately preregistered question after custody is resolved.
See the [B13 crosswalk](maintenance/idea-index-crosswalk-20261121-r160.md).

**Issue #7741 / PR #8181 targeted disposition (2026-11-22):** Preserve the
sequence: T0 v1 had 217 lifecycle-accounting errors, T0b stopped before output,
and T0c failed its per-principal negative control despite a clean primary
contrast. The separate frozen T0d passed its synthetic gate in 32/32 cells
with zero replay errors and exact-null controls. Merged PR #10419 imported that packet byte-for-byte, passed seven local tests in normal and `-O`, passed applicable hosted checks, and skipped formal. It supersedes closed Draft PR #8181. Do not replay the consumed allocation. Keep the Issue open for external validity. No real
adoption, production queue, or user effect is established. See the [B13
crosswalk](maintenance/idea-index-crosswalk-20261121-r160.md).

**Issue #7748 disposition (2026-11-22 JST):** Closed after its declared
synthetic method question completed: merged #7762 has a six-trace
`PASS_METHOD_SCOPED`, and #8182 retains the separate duplicate-ID A02 boundary
result plus A01 STOP. The closure comment keeps external validity, host/runtime
scheduling, GUI behavior, and physical release out of scope. The issue route and
results remain in `docs/IDEAS_AND_OUTCOMES.md` and the [B13 crosswalk](maintenance/idea-index-crosswalk-20261121-r160.md); this is one evidence-backed closure, not a batch policy.

**Issue #7765 disposition (2026-11-22 JST):** Closed after the calibrated
held-out comparison failed its preregistered improvement gate. The T0 gain
confound and calibration A01 audit STOP remain; distinct calibration A02 and the
held-out rows are retained unchanged in merged #7772, and merged #7782 only
repairs harness input validation. No real-GUI/task-effect result follows. See
[the closure comment](https://github.com/Unjuno/agent-interface/issues/7765#issuecomment-7064868582) and the [B13 crosswalk](maintenance/idea-index-crosswalk-20261121-r160.md).

**Issue #7817 disposition (2026-11-22 JST):** Closed at the declared finite
T0 method scope after verifying the retained one-shot candidate/auditor result,
all ten frozen cases and five applied hostile mutations, no authority change,
and all 17 current-main Git-blob manifest digests. The old Issue comment's
two-review condition was stale because PR #7938 had already merged; it is not a
repository-wide reviewer quota. The closure preserves explicit limits: no
normative-policy, real-source, GUI/runtime-safety, or action-authority claim.
The 25-item B13 cohort is now 22 open / three closed. See the [closure comment](https://github.com/Unjuno/agent-interface/issues/7817#issuecomment-7065690444) and [crosswalk](maintenance/idea-index-crosswalk-20261121-r160.md).

**Issue #7773 current-main feasibility recheck (2026-11-22):** The source
search at current main `85a1d02d65` found no model-visible ordered target-belief
list in the inspected runtime paths. Keep `HOLD_NO_CANDIDATE_LIST_CONSUMER`; do
not substitute image/tool/detector order or run a model/GUI proxy. The Issue
remains open, with T1 gated on a real identity-stable consumer and separate
preregistration. See the [current-main HOLD comment](https://github.com/Unjuno/agent-interface/issues/7773#issuecomment-7064923854) and the [B13 crosswalk](maintenance/idea-index-crosswalk-20261121-r160.md).

**Fake X release-boundary regressions (PRs #10416/#10417):** Both are now on
main; their R01/R02 current-main results and limits are recorded in
`docs/CURRENT_GOAL.md`. They test synthetic delayed input and a test-double
lease-expiry refusal. They do not demonstrate physical input release, live GUI
effect, task success, or recovery reliability.

**Purpose:** make `Unjuno/agent-interface` understandable and safe for many
independent workers while preserving every distinct research idea, result,
owner, and recovery path. Organization enables computer-control research; it
does not replace or complete that research.

This is the short execution plan. The [cleanup ledger](REPOSITORY_CLEANUP_PLAN.md)
and [consolidation record](REPOSITORY_CONSOLIDATION.md) retain historical
snapshots and detailed receipts. Never rewrite a historical result to make the
current repository look cleaner.

**Current membership update r165 (2026-11-22, main `d5ada452`):** The paginated live read found 1,640 open Issues and 405 open PRs; exact sorted-ID hashes match r164. PR #10463 opened after r164 and merged before r165; it was absent from both snapshots, so no net open-set change was observed. This remains a membership receipt, not semantic cleanup. See [r165](maintenance/repository-inventory-recheck-20261122-r165.md). The same merge integrated the frozen-source audit repair and supported WSL package build evidence; #58 stays open for host/golden acceptance and #57 stays open for recovered-task, reliability and matched economics gates. Current portable-runtime tests pass 21/21 on Windows and WSL in both normal and optimized modes; see [the test packet](../research/integration/portable_runtime_distribution_v2_current_main_d5ada452_20261122/RESULT.md).

## What “organized” means

- Each live research Issue has a distinct hypothesis, current evidence and its
  limits, dependencies/owner or an explicit unknown, a finite next step, and a
  reason to remain open or a verified successor/disposition.
- Each open PR has a current exact head/base, a known diff and local validation
  plan, linked Issue, unique code/evidence custody, dependencies, and a concrete
  disposition: integrate, repair/retarget, preserve on hold, or close after
  verified transfer/supersession.
- Every useful branch, worktree, process/session, ignored output, and raw packet
  has a recoverable owner/custody record. Unknown custody is retained and
  investigated; it is never treated as disposable.
- A worker can select one bounded item, see its writable paths and dependencies,
  produce a reviewable result, and update a shared index without overlapping
  another worker. Shared indexes have one integrator at a time; family and PR
  audits can proceed independently when their records and paths do not overlap.
- Entry points direct readers to current work and canonical idea/evidence
  records. Duplicate navigation can be removed only after inbound links and
  unique content are checked.

An empty Issue/PR queue is not the success condition. The condition is that each
record has an evidence-backed disposition and remaining research is easy to
resume.

## Work order

1. **Establish the live queue.** Fetch complete paginated open Issue and PR
   membership, record the main SHA before and after, and compare with the latest
   full snapshot. Reuse unchanged row metadata; refresh only additions,
   removals, and records selected for action. Membership counts are not semantic
   review, ownership, or merge readiness.
2. **Route ideas by family.** Work in bounded batches from the existing idea
   discovery and exact-URL queues. For each candidate, read the live Issue,
   related PRs, canonical family record, and cited first outcomes. Record the
   specific question, strongest simple comparison, supporting and contradicting
   evidence, unresolved residual, dependency, and smallest discriminating next
   test. Keep similar but distinct hypotheses separate. A link or summary alone
   does not count as semantic disposition.
3. **Resolve PRs against current source.** For one PR or a proven disjoint
   group, refresh exact head/base, diff, checks, reviews, linked Issue, branch
   ancestry, and unique evidence. Run the appropriate local checks on the exact
   source. Integrate useful, applicable work when actual repository protections
   permit. Transfer and hash-check unique work before closing a superseded PR.
   Keep unresolved research and evidence-custody holds open with a concrete
   release condition. Do not use fixed reviewer counts or merge to reduce the
   queue size.
4. **Disposition Issues from evidence.** Keep actionable questions open with
   one finite next test; keep blocked questions open with the real dependency
   and release condition; link duplicates to a canonical record only after
   confirming the hypothesis is the same; close scoped-complete or superseded
   records only after preserving the result and return path in the catalog and
   Issue. Never bulk-close by age, label, or inactivity.
5. **Reconcile custody.** Audit branches, registered and unregistered
   worktrees, sessions/processes, ignored outputs, and raw packets after their
   owners and dependencies are known. Verify exact tips, unique changes,
   manifests/hashes, and recovery before archiving or deleting an item. Unknown
   owner or recoverability means retain and investigate.
6. **Repair navigation and enable parallel work.** Update README/current-goal,
   roadmap, worker map, family indexes, and research entry points after their
   targets are verified. Give each work packet a narrow scope, allowed writable
   paths, evidence source, output location, dependency, and completion receipt.
   Resolve conflicting guidance at its canonical source rather than adding
   another policy layer.

## Repository-wide convergence sequence

The six work orders above are performed as finite waves, with the evidence and
ownership needed by a later wave established before state changes:

1. **Freeze the map, not the work.** Refresh complete Issue/PR membership and
   note active allocations, owners, exact branches and unique evidence. Ongoing
   experiments keep their declared boundary; independent audits can continue.
2. **Build a hypothesis catalog.** Route source Issues into canonical families.
   Keep distinct questions distinct even when they share code. Preserve the
   original Issue URL, first outcomes, counterexamples, raw/source identity,
   unresolved question and next discriminating test. Mark idea-only records as
   deferred only after the canonical page and source Issue cross-link each
   other.
3. **Converge PRs on current main.** Classify each open PR as merge-ready,
   bounded repair/retarget, superseded with verified transfer, or evidence/
   dependency hold. Verify exact head/base, changed files, source applicability,
   local checks, unique artifacts and actual repository protections before any
   merge or close. Integrate useful work as soon as these checks pass; do not
   wait for an invented reviewer quota or close a PR just to lower counts.
4. **Set Issue state from the catalog and implementation.** Close scoped work
   only when the recorded result satisfies that Issue's question. Close a
   duplicate only after its unique evidence is represented by the canonical
   family and the source Issue links there. Keep unfinished research and real
   blockers open with one finite next action and a verifiable release
   condition.
5. **Resolve custody and navigation.** Reconcile live branches, worktrees,
   ignored outputs, sessions and experiment packets against merged/current
   content. Preserve uncertain ownership. Then update the entry points and
   publish disjoint worker packets.

Workers may audit separate families or PRs in parallel when their write paths
and evidence are disjoint. One integrator serializes edits to shared indexes;
this is file ownership, not a head-count or approval gate. A repository is
orchestration-ready when every current queue item has an evidence-backed
disposition, every retained artifact has recoverable custody or an explicit
investigation, and independent workers can identify non-overlapping scopes.
Open Issues and PRs may remain when their research or evidence is still live.

## Prior whole-repository checkpoint r155 (2026-11-21)

On main `63449e8abed5938a780de22cabc160aefd9d3326`, complete paginated REST
reads before and after were bracketed by the same main SHA. The open Issue set
contains 1,643 IDs and exactly matches r152. The open PR set contains 409 IDs;
compared with r152, #10218 is the sole removed member. PR #10377 was opened and
merged during the interval and has no remaining membership effect. Existing
sorted Issue IDs are reused; the PR delta and capture conditions are retained
in [the r155 receipt](maintenance/repository-inventory-recheck-20261121-r155.md).
This is membership evidence only. It does not semantically classify the queue,
assign custody, or imply merge readiness, and it supports no bulk closure.

The sole removed PR, [#10218](https://github.com/Unjuno/agent-interface/pull/10218),
is closed unmerged as superseded, with its source branch retained. Its late
App Server usage port was transferred to [#10352](https://github.com/Unjuno/agent-interface/pull/10352)
(merged as `b0493167`); the scheduling/cleanup repair was merged in [#10365](https://github.com/Unjuno/agent-interface/pull/10365)
(`897f4896`). Current main contains the late-usage spool publication, recorder,
and public-caller methods. This only resolves that PR's unique-code custody;
the caller does not automatically invoke the post-score usage method, and the
work remains synthetic rather than real provider/economics evidence for #57.

## Batch protocol

Each batch selects one family, PR, or custody slice and leaves a compact receipt
with: source SHA and live-record timestamp; records and files inspected;
decision and its evidence; changed paths; local checks; preserved unique data;
open dependency; and the next bounded batch. Do not duplicate full inventories
when only a delta is needed. Do not rerun a consumed experiment to make its
record easier to classify.

Before changing an Issue or PR state, refresh its live body, comments, state,
head/base, checks, dependencies, and owner. Before integrating, check the exact
diff against current main, run relevant local validation, and verify actual
branch protections. Optional CI may be reported as pending; do not wait for it
when local evidence is sufficient and repository protections allow progress.

## Additive integration and organization checkpoint after PR #9397 (2026-10-22)

PR #9393 merged the offline adapter from one persistent Codex App Server turn
to the existing provider-attempt recorder and public-MCP caller, with Fake X
success and stale-generation composition cases. PR #9394 refreshed this plan.
PR #9395 then added internal consistency checks between reported turn usage
and the matching raw App Server usage event, plus preservation of valid partial
usage on ineligible turns. The current main commit is
`4c97e6fc635a103fb333dd271a479f2452d6df6f`. On this exact source, the related
ledger/recorder/provider/public-caller suite passes 44/44 in normal and
optimized Windows CPython 3.11.9; the deterministic replay-gate passes. Issue
#57 was updated at [comment 6334338432](https://github.com/Unjuno/agent-interface/issues/57#issuecomment-6334338432)
and remains OPEN. These offline checks prove neither production provider
routing nor independent provider-log reconciliation, live desktop/MAP01
effect, blocked-platform-I/O release, matched efficiency, or reliability.

PR #9397 then added a composed public-caller regression for terminal receipt
archival blocked after cancellation. On its exact merged source, 51/51 related
owned-process/relay tests passed in normal and optimized Windows CPython 3.11.9;
the remote Xvfb and relevant replay/caller checks passed. The separate evidence
job failed before running tests because its Ubuntu 26.04 runner could not
provide the pinned Python 3.13.5 runtime. This synthetic telemetry-stall test
does not prove release while X11 itself is unavailable, physical input state,
or live task effect. Issue #17 remains open.

The fresh full membership receipt [r149](maintenance/repository-inventory-recheck-20261022-r149.md)
was bracketed by stable main `b0e8c6c9b4cfb7917932f52e7a69d8267348aa89` and
reproduced r148 exactly: 1,654 open Issues and 452 open PRs, with no ID-set
deltas. It updates discovery only; no semantic disposition or ownership is
implied. PR #8800 remains open at exact head
`bf77bc4c1905bd99a5a99a138e897eededddd834` on an A14 raw-custody hold. Its
public result/reconciliation preserve the aggregate and frozen hashes, but
state that the raw `episode/report.json`, protocol and images remain in private
allocation output. A targeted search of the accessible Codex workspace found
no matching raw packet or owner record. A different historical #59 report is
not a substitute. The live PR now records this scoped finding and a release
condition at [comment 6334524921](https://github.com/Unjuno/agent-interface/pull/8800#issuecomment-6334524921).
Keep the PR open, do not rerun A14, and recover only from the original frozen
allocation source if its owner/location is identified. This batch used no
WSLc or Docker allocation.

The [prestarted X11 supervisor implementation and qualification record](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md)
remains canonical; no duplicate was created. Keep the separate, still-proposed
[Win32 operation-owner design](superpowers/specs/2026-10-22-win32-prestarted-supervisor-design.md)
distinct from that implementation. Its input authority, process-generation,
and blocked-I/O release evidence require platform-specific qualification.

## Worktree custody checkpoint after PR #9399 (2026-10-22)

The fresh complete membership read [r151](maintenance/repository-inventory-recheck-20261022-r151.md) at stable main `08064035460187ba5c8c5cbb2f4e9732ca622ada` again records 1,654 open Issues and 452 open PRs. Its ID sets match r150; PR #9399 was opened and merged between the reads, so it had no net effect on open membership.

A read-only audit of the two largest changed worktrees found clear branch history but not a safe cleanup/transfer decision. The detailed paths, commands and limits are in the [worktree custody receipt](maintenance/worktree-custody-recheck-20261022-r01.md).

- `research/owned-cancel-supervisor-prototype-r01` is local-only at `24e5fbd0823f0a8adbbad85830da2e639b8ecc91`, seven patch-unique commits ahead and 141 behind main; neither a remote branch nor a PR exists. Its committed branch diff spans 112 paths. The worktree reports 42 tracked modifications and 18,365 untracked entries, mostly local integration evidence plus a Python 3.12 environment. `git status` warned it could not open `lib64/` (`Function not implemented`), so completeness is uncertain. Representative READMEs describe synthetic Fake X/App Server composition and explicitly exclude real provider calls, WSLc, Docker and matched efficiency.
- `feat/prestarted-cancel-supervisor-r01` is the remote head of closed, unmerged PR #9315 at `76626da8b03df25024d12efb5f1dde2f12c53ed2`, 21 patch-unique commits ahead and 136 behind main. The PR was explicitly superseded; its comment says committed packet paths/manifests were transferred through #9333, merged at `4fe158d2f5e3774580c3812c3c589fbc64d4f8d2`. That does not cover this worktree's 15 tracked modifications and 5,135 untracked entries, including 4,809 in the standard-caller ledger and 315 in the supervisor packet. Its untracked WSLc snapshot notes are explicitly HOLD: an empty listing does not prove an unused lane. Issue #7924 is currently OPEN/STOP.

No files were copied, committed or removed from either worktree. PR #9315's supersession record does not establish custody for the later uncommitted state. The owner of each worktree remains unknown. Do not reset, clean, rebase or archive them. The next step is to identify each current task/worker owner, then compare untracked packet manifests with current main without running experiment runners. Only after that choose a focused current-main transfer PR for unique useful material. Keep the other 12 changed worktrees on hold for later batches. No WSLc or Docker allocation was used.

## Earlier full-inventory checkpoint after PR #9390 (2026-10-22)

After docs-only PR #9390, a full membership reread at stable main
`38b3d2f1c42b568851827cc969a242104f328366` exactly matched [r148](maintenance/repository-inventory-recheck-20261022-r148.md):
1,654 open Issues and 452 open PRs. The Issue ID set matches r145; the PR set
equals r145 minus merged #8845. The r148 receipt retains the full exact ID CSVs
and Git-blob hashes. Membership is routing metadata only; it does not establish
semantic disposition, ownership, custody, or merge readiness.

PR #9389 narrows one saturated-relay boundary: at the 16-response cap a
cancellation can pass one deferred ordinary request, consume one separately
bounded response slot, and stop later tool dispatch if its response writer
fails. The relay and Fake X composition suites passed 26/26 in both normal and
optimized Windows CPython 3.11. This is bounded stream/Fake X composition
evidence; one or more queued ordinary requests can still delay cancellation,
and it proves no native or physical input release. See the
[supervisor design crosswalk](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md).

PR #8845 preserved a separate frozen-source construction result for Issue #59:
the planner's authored `minimum_ammo=5` rejects ammo 4 while the same-epoch
cover monitor retains cover with its separate hard floor of 1; the zero-ammo
control invalidates. The original WSLc run is retained and was not repeated.
On its exact PR head, local Windows CPython 3.11 tests passed 2/2 in normal and
optimized modes, the non-executing audit returned `PASS_SCOPED`, and the saved
result JSONs were restored byte-for-byte after replay. This is a policy-boundary
difference, not proof of a defect or live MAP01 behavior. The packet is indexed
in the [MAP01 family crosswalk](ideas/map01-live-guard-evidence-family.md);
Issue #59 remains open.

**Next repository-convergence batch: PR #8800 / Issue #59 A14 custody.** The
2026-10-22 live read found PR #8800 OPEN, non-Draft, base `main`, exact head
`bf77bc4c1905bd99a5a99a138e897eededddd834`, replay-gate PASS, and no closing
Issue references. Its body says the raw protocol and images remain local; the
family crosswalk identifies `episode/report.json` as absent from the tracked
packet. Resolve whether those exact originals and their recovery path can be
verified against the frozen A14 records. Do not rerun A14. If custody remains
unavailable, keep the PR open on that specific hold and preserve the first
result. Then choose a disjoint exact-head PR, idea-family, or custody slice.
Do not select records by age/count, close research to empty the queue, or
delete unknown-custody work. This batch used no WSLc allocation.

The following PR #9379 checkpoint is historical context, not a current source
pointer.

The last code-bearing main change is PR #9377 at
`e698167ede85085b61446ad85dc6330fa1ba283d`. PRs #9378 and #9379 only refreshed
repository documentation and the membership receipt.
The complete [r147 membership recheck](maintenance/repository-inventory-recheck-20261022-r147.md)
captured main `b481ce7e5950352ac39cde1612f9ef691d541c4c` and records 1,654 open
Issues and 453 open PRs at a stable before/after SHA; both exact ID sets match
r145. Treat r147 as the last complete queue snapshot and refresh before later
dispositions. PR #9377 adds a research bridge
from the existing model-call boundary to the durable attempt ledger and
standard public MCP caller. Its 36 local ledger/provider-recorder/public-MCP
tests pass in normal and optimized Windows CPython 3.11; the regression uses an
injected model call and remains synthetic. The live provider route and external
usage reconciliation remain open under #57.

The selected [prestarted supervisor design](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md)
already exists as the canonical design/evidence page; its new
[qualification crosswalk](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md#qualification-crosswalk-and-current-decision-2026-10-22)
maps existing tests and retained outcomes to the open requirements. Do not
create a duplicate spec. Its operation-owner candidate remains unqualified:
Win32 blocked-call packets use inert API fakes, while the X11 source audit
leaves accepted-request effects during server unavailability unresolved. Keep
runtime behavior experimental/default-off, and use only separately verified
WSLc allocations; #7924 still records STOP/HOLD for shared ownership.

The following PR #9373 checkpoint and r146 inventory details are retained as
historical context, not current membership or source pointers.

At PR #9373, main was `0ba19dc885d9531e6fc21c5ea9e26a624fb25bca`. The
complete [r146 membership recheck](maintenance/repository-inventory-recheck-20261022-r146.md)
records 1,654 open Issues and 453 open PRs. Both full ID sets were re-read
before and after at the same main SHA and compared row-for-row with r145; no
membership changed. The exact ID CSVs and hashes remain in r145, linked from
the r146 receipt. Membership is not semantic disposition, PR readiness,
ownership, or custody.

PR #9373 aligned the root README and docs index with this organization plan as
the single current execution pointer; the cleanup plan and consolidation
record remain detailed receipts/history. The older r145 checkpoint below is
historical. Its named next candidate, PR #8819 / Issue #8493, was already
merged/closed before r145: the method-scoped result is in main, and the exact
live states are `MERGED` and `CLOSED`. Do not reopen or rerun that completed
finite result. The next cleanup batch must select a different item from r146's
live sets and refresh that item's exact head/state/owner before disposition.

The selected supervisor design already exists. The direct live-Xvfb
`x11_cancel_worker` bystander-reuse discriminator now has one retained scoped
pass in [R01](../research/integration/live_xres_bystander_reuse_20261022_r01/DISPOSITION.md):
natural XRes-base reuse by an unrelated client was detected, cleanup refused,
and independent key-state readback showed no release. A separately retained
[public-caller R02](../research/integration/live_xres_public_caller_bystander_20261022_r02/DISPOSITION.md)
now shows one composed live-Xvfb sample with the same fail-closed result. The
broader release/effect/recovery/efficiency gates remain distinct. Keep
experimental runtime behavior opt-in and do not use WSLc/Docker while Issue
#7924's shared ownership STOP/HOLD remains in force.

## Historical execution checkpoint after PR #9370 (2026-10-22)

Current main is `dcc9e9ed4688b8b9dda71156e50b054b2a88297b` (PR #9370). The
complete [r145 membership recheck](maintenance/repository-inventory-recheck-20261022-r145.md)
records 1,654 open Issues and 453 open PRs with matching before/after main
SHA. The Issue and PR ID sets match r144; #9370 added the targeted high-risk
worktree custody receipt without changing membership. Counts are discovery
metadata, not semantic disposition, ownership, or readiness.

The user's selected first work item is the existing
[prestarted cancellation supervisor design](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md),
which is already the canonical design/evidence page; do not create a second
spec or treat the merged opt-in path as qualified. Retained WSL2/private-Xvfb
evidence now includes two same-Xvfb fresh-session recovery runs, one paused
Xvfb run, a three-pair pause pilot, and one caller/effect timing run. These
show bounded caller responses in their declared schedules and independent
synthetic task-oracle results. They do not promote the canceled runtime result
from `UNKNOWN`, establish release while X11 is unavailable, prove shared
desktop input authority, or qualify physical GUI/MAP01, matched efficiency,
or reliability. Keep the supervisor default-off and keep #17/#57 open.

The design page identifies the remaining technical boundaries: global XTest
release lacks a proven exclusive-input capability; deadline expiry must also
prevent a delayed supervisor from emitting a new effect. The direct
worker-path live-Xvfb bystander refusal has one pass, but public-caller live
composition is still open. The next discriminator is to exercise natural
resource-base reuse through the standard caller with independent key-state
readback and raw conditions, preserving `UNKNOWN`/no-replay. WSLc remains
STOP/HOLD under #7924; this batch does not use WSLc or Docker.

PR #9367–#9370 updated the catalog, checkpoint, worktree census, and
high-risk custody follow-up. The census found 45 local worktrees, including
14 dirty ones; branch-name comparison alone found no dirty branch exactly
matching an open PR head. The largest unpublished supervisor prototype and
closed #9315 worktree still lack verified owner/recovery records. Preserve
them and the other dirty worktrees until custody is established; do not reset,
archive, or delete them. Continue repository convergence in separate bounded
family/PR/custody batches so those cleanup records do not displace the selected
scientific discriminator.

## Historical membership checkpoint after PR #8819 (2026-10-22)

The complete [r142 membership recheck](maintenance/repository-inventory-recheck-20261022-r142.md)
captured main `7ee142d642de45c1129a138e01f3519ed4a1449c`, with 1,655 open
Issues and 453 open PRs. The Issue set matched r141; #8819 was the only PR
removed. The later r143 baseline records the scoped closure of #8493 and PR #9367's documentation integration; r144 reverified the same membership after PR #9368.

## Historical execution checkpoint after PR #8824 (2026-10-22)

Current main is `d56609f46aae0be91d593a111adca84fca5a2893` (PR #8824).
The complete [r141 membership recheck](maintenance/repository-inventory-recheck-20261022-r141.md)
confirms 1,655 open Issues and 454 open PRs, with main unchanged across
pagination. The Issue set matches r140; #8824 is the only PR removed. Exact IDs
and sorted-ID hashes are retained in the r141 CSVs. Counts are discovery aids,
not semantic disposition or readiness.

PR #8824 added the unique A03 audit-only result for Issue #8553: the older A01
checker accepted unsupported branch labels and swapped `red`/`blue` child
policies; independent replay rejected both mutations and accepted the unchanged
policy across all five retained cases. The packet preserves A01 unchanged and
does not claim A01's original policy was wrong. Local construction tests pass
3/3, the 11 frozen-input hashes and results manifest match exact Git blobs, and
the exact packet survives Windows checkout with a dedicated `.gitattributes`
rule. This is finite synthetic evidence only. Issue #8553 stays OPEN because
the unsafe policy-binding gap has not been repaired or qualified beyond its
authored model.

PR #9363's Win32 supervisor design and two inert-fake counterexamples are also
integrated. They require old-producer fencing before compensating UP can
establish neutral state. Windows checkout now preserves those packet hashes;
the two audits pass in normal and optimized Python. These are not native
Windows behavior, physical release, task-effect, or reliability evidence.
Issue #17, #57, and #7924 remain OPEN; the Win32 design remains a proposal and
the runtime supervisor stays opt-in.

The prior draft of this plan incorrectly listed PR #8819 / Issue #8493 as the
next candidate even though its result had already been integrated by PR #8819
and the Issue closed. The r146 checkpoint above corrects that stale pointer;
the completed result and its finite-model limits remain in the linked report
and Issue record. No WSLc/Docker allocation was used.

## Historical execution checkpoint after PR #9356 (2026-10-22)

Current main is `5a32f1e486b40103a1f24a6059ae78c8cb884e0f` (PR #9356).
Membership recheck [r138](maintenance/repository-inventory-recheck-20261022-r138.md)
confirms 1,655 open Issues and 457 open PRs. The Issue set is unchanged from
r137; #8827 was closed as superseded after its C02 result was transferred
byte-for-byte through #9356. PR #9356 opened and merged during the interval and
has no net membership effect. These counts are only a queue baseline, not
semantic triage or readiness. The authoritative exact IDs and hashes are in
r138.

Fresh live reads show #17 and #57 OPEN; #7924 is OPEN with its migration STOP
still requiring a current ownership/release receipt. PR #8371 and #9355 are
MERGED; #7290 and #8827 are CLOSED as superseded; #9356 is MERGED at the
current main SHA. PR state changes still require refreshed exact records and
evidence review.

The first PR convergence batch after r137 transferred Issue #8648's C02 finite
synthetic-model result from old-base PR #8827 to current-main PR #9356. No
candidate/auditor was rerun. Fourteen manifest entries match Git blobs; all 15
packet files are blob-identical to the source PR, while the shared analysis
index retains the C02 route along with newer entries. Current-main successor
validation passed with Python 3.13 strict analysis-index and workspace-index
checks and `git diff --check`. The remote checks were queued, but main had no
branch protection or rulesets and the relevant local checks passed. PR #8827
was closed only after merge and transfer verification. Issue #8648 remains
open because the finite model does not answer real route/task feedback.

The separate `work/agent-interface` checkout is on
`integration/x11-fake-socket-relay-r01` at `994f18dcd479eca0885e979749db30073a98f3a2`,
with modified and untracked files across idea indexes, current-goal and
consolidation documents, maintenance receipts, and integration evidence. Its
owner and resume status are not verified. Preserve it and establish custody
before any reset or archive. This makes that worktree a concrete next custody
batch; repository-wide branch deletion is not justified.

**Next bounded batch:** select a small exact-head PR slice from r138, refresh
live metadata/diff/checks and linked Issue, and integrate the first item whose
current-main applicability and local checks pass. The previously refreshed
candidate set includes the evidence-only #8845 and #8833; their WSLc/model/task
limits and unique evidence must be checked before disposition. In parallel only
where paths are disjoint, audit one idea family from the existing semantic-route
queue. Do not start with mass Issue closure or worktree deletion.

## Historical execution checkpoint (2026-10-22; superseded by r137)

This checkpoint records main `3e46261966957f0852703ededb4b6fb2f3a594bf`,
after PR #9346 and the current-pointer refresh. The retained R02 Xvfb trial ran against source
`cdc8bd6b65bf976137db645c2be31e20090f7d67`; its results are historical and
remain tied to that exact source. The latest complete paginated membership receipt is
[r136](maintenance/repository-inventory-recheck-20261022-r136.md), captured at
this main SHA: 1,655 open Issues and 460 open PRs. Its Issue set matches r135;
its PR set differs by the merge of #7181, with #9346 opened and merged between
captures. Counts establish membership only, not semantic disposition. Refresh a
complete set when the next change requires it, and refresh every touched record
before state changes.

The prestarted-supervisor design remains the selected integration thread. Its
standard-caller Xvfb evidence and limits are recorded in the
[design page](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md#design-review-checkpoint-2026-10-22).
PR #9381 and PR #9382 are merged. PR #9382's retained Fake X composition
packet and normal/optimized local tests support one immediately following
cancel at a saturated relay. Queued ordinary input, independent input-state
readback, native GUI/MAP01, WSLc, and integrated efficiency remain unresolved.
See the design page's saturated relay R01 section for the exact conditions and
next discriminator.
The new [R02 trial](../research/integration/standard_caller_xvfb_current_main_20261022/prestarted-fresh-recovery-02/README.md)
passed once against its frozen source: the cancellation response returned pending in
252.924 ms; the supervisor release readback completed in 324.791 ms; independent
key-up readback was observed in 379.339 ms; and a distinct fresh session passed
its synthetic task oracle through an 8.501 s horizon. The old runtime result
remains UNKNOWN, `task_success` null, and replay denied. This qualifies one
same-Xvfb fresh-session recovery schedule, not reliability. The public-caller
Fake X bystander-reuse refusal passes in normal and optimized mode; see its
[separate packet](../research/integration/local_fakex_public_bystander_refusal_20261022_r01/README.md).
The live-Xvfb bystander negative path and whole-server-unavailable release
remain unqualified. Keep the supervisor default-off. The next
science/integration batch must target an explicit remaining gap; do not repeat a
consumed run or turn cleanup into a WSLc/Docker allocation.

PR [#7181](https://github.com/Unjuno/agent-interface/pull/7181) is now merged
and preserves a native P01 three-arm comparison for #57. Its report records
persistent input+output of 39,329 tokens versus 109,373 plain and 111,226
ephemeral, plus ready-to-independent-oracle times of 27.712, 36.631 and 46.550
seconds. Eighteen effects were independently checked, with one bounded repair.
The disposition remains HOLD: each arm has one sample, one fixed-order six-task
fixture/domain, and model/cache/host-load confounding. It is a useful measured
input, not the matched current-caller/second-domain integrated qualification or
a reliability estimate. Keep #57 open and carry these limits into the next
matched integration decision.

Repository-wide execution stays on the six work orders above: establish a live
queue when needed; preserve and route one bounded idea family; resolve exact
PRs against current source; disposition Issues individually from evidence;
reconcile custody only after owner/recoverability checks; then repair entry
points and issue non-overlapping work packets. Start from the
[cleanup ledger](REPOSITORY_CLEANUP_PLAN.md) and
[consolidation history](REPOSITORY_CONSOLIDATION.md), using them as receipts,
not as proof that old counts or assignments remain current. The next cleanup
batch is one refreshed family or exact-head PR slice with a named writable
surface and a short disposition receipt. No bulk close/merge by age, label,
count, or inactivity; no fixed reviewer quota. A disjoint audit may proceed
only when it does not edit the same shared index, branch, or evidence.

The computer-control work remains the research objective. Cleanup must not
launch or consume WSLc/Docker allocations; Issue #7924 remains STOP/HOLD for
shared WSLc ownership. PR #9320 integrated the opt-in supervisor, #9321
preserved its initial evidence, #9322 reconciled the design, #9323
preserved a scoped standard-caller Xvfb result, and #9329 added a bounded
worker-exit grace with a separate retained Xvfb outcome. That run missed the
strict 300 ms caller-response target by 1.268 ms and correctly kept the runtime
receipt UNKNOWN; see the [design page](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md#additive-shutdown-grace-result-2026-10-22).
PR #9331 added a 25 ms response handoff margin. A separate Xvfb run then
returned in 276.447 ms, with independent key-up readback and a passing
synthetic task oracle; runtime status remains UNKNOWN and replay denied. See
the [updated design page](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md#standard-caller-xvfb-after-handoff-margin-2026-10-22).
The packet records release/readback and an independent task oracle, while
runtime task success remains null and replay stays denied. Keep
#17 and #57 open while recovery, task semantics, efficiency, and safety gates
remain. Continue family disposition from a refreshed current queue; the
remaining route count is a discovery queue, not a closure target.

## Completion checks

This plan is fulfilled when a fresh membership pointer exists; every processed
family/PR/Issue has a traceable disposition; every retained artifact has known
custody or an explicit investigation item; canonical entry points are current;
and workers can claim independent packets without conflicting instructions or
shared-file edits. Report remaining unreviewed records and research gaps
explicitly. “Clean” never means deleting ideas or hiding unresolved science.

## PR convergence receipt (2026-10-22)

After the earlier checkpoint, PR [#8371](https://github.com/Unjuno/agent-interface/pull/8371) merged through GitHub at `999c811a6e516f79db357d9a48ed03b1aca50f2c`. Its six-path result preserves bounded report publication/retention and truthful all-attempt model metrics. The exact composed tree was checked against the locally validated candidate; focused custody and metrics tests passed 12/12 in normal and optimized Windows CPython 3.11.9 with Pillow 10.2. Workspace-index, navigation-link, and whitespace checks passed. The broader native runner was attempted locally but did not pass on this Windows checkout: its protocol run recorded 2 failures, 106 errors, and 17 skips, with platform/sparse-checkout incompatibilities; do not describe that suite as green.

PR [#7290](https://github.com/Unjuno/agent-interface/pull/7290) was closed as superseded by #8371 after comparing all six changed paths. Its five report/caller paths match the merged result, and the protocol/harness suite registrations in its branch are already present in current main. The close preserves the source branch, discussion, and historical evidence; no unique code or registration was discarded.

This receipt advances report custody and measurement accounting only. It does not qualify live GUI control, bounded release under blocked platform I/O, MAP01, task-success semantics, matched efficiency/reliability, or WSLc. Issue #7924 remains STOP/HOLD because shared WSLc ownership is unknown; no WSLc allocation or container operation was used. The supervisor design remains opt-in, and its remaining qualification gates stay in the [canonical design page](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md).


A paired current-main Fake X regression packet is retained at [r01](../research/integration/fakex_prestarted_supervisor_local_current_main_20261022_r01/README.md), with raw mode-specific logs, structured receipts and SHA-256 manifest. The public-caller and supervisor suites passed 15/15 normally and under `-O`. A helper-only late-resume probe also resumed 16 ms after expiry in each mode and recorded zero effects, one refusal, and `expired_deadline`. This is synthetic helper/caller evidence only; real X-server blocked-I/O release and MAP01 remain unqualified.

## Current-main R02 source audit (2026-10-22)

The retained [R02 standard-caller Xvfb result](../research/integration/standard_caller_xvfb_current_main_20261022/prestarted-fresh-recovery-02/README.md) ran at `cdc8bd6b65bf976137db645c2be31e20090f7d67`, an ancestor of current main `2f971fe867f7c85a82c90d504b1dce9e29534bd5`. A current-main diff over `runtime/cli_v1`, `runtime/guarded_x11_v1`, and `runtime/backends/x11_v1` is empty, and all five files listed in the packet's `raw/runtime-manifest.sha256` match the current checkout byte-for-byte. R02 therefore remains applicable to current runtime source as of this main SHA; this is a source-currency audit, not a new run or a reliability sample.

The result remains one schedule with the owner blocked in `Display.sync()` while the X server can serve the supervisor; whole-server unavailability, physical desktop/MAP01, owner-exclusive XTest state, matched efficiency, and reliability remain unqualified. Its independent task oracle is synthetic, and the canceled operation still has `task_success=null`, `release_confirmed=false`, and replay denied. No WSLc allocation was used.


The retained [R02 experiment packet](../research/integration/standard_caller_xvfb_current_main_20261022/prestarted-fresh-recovery-02/README.md) records the 252.924 ms caller response, 324.791 ms supervisor readback, 379.339 ms parent-client readback, and 8.501 s delayed-request horizon, along with its raw files and manifests. This is one retained outcome; no separate raw/source audit file is present in the current checkout, so none is claimed here.

## Current-main R03 Xvfb repeat (2026-10-22)

One independently frozen repeat ran the same standard-caller blocked-`Display.sync()` and fresh-session scenario against main `6b276fcabfa11c060282e0714501a1057e75c0a6` in Ubuntu WSL2 with private Xvfb. The unittest passed 1/1 and Xvfb exited 0. Caller response was 255.100 ms; supervisor readback 323.415 ms; terminal cancellation receipt 329.723 ms; separate parent-client keymap readback 386.460 ms; and the 8.505 s delayed-request horizon found all keys up with no old delayed press. Distinct target/session/process-generation values passed the synthetic fresh-task oracle at input and horizon. The old operation remains UNKNOWN, task success null, and replay denied.

The shell wrapper exited 2 after writing both successful test/Xvfb exit codes because its CRLF-terminated final `exit 0` was parsed incorrectly. This wrapper defect and three preflight-script parsing failures are preserved in [R03](../research/integration/standard_caller_xvfb_current_main_20261022/prestarted-fresh-recovery-03/README.md); none altered the candidate result, and R03 was not retried. The paired R02/R03 outcomes are two observed passes under this one schedule, not a reliability estimate. Whole-server unavailability, physical GUI/MAP01, matched efficiency, and WSLc remain unqualified; no WSLc allocation was used.

## Current-main Xvfb full-process pause boundary R01 (2026-10-22)

A test-only extension to the standard-caller test paused its exact private Xvfb process for 1,500.674 ms. The request returned pending in 253.566 ms from cancellation admission, before Xvfb resumed; pending preserved UNKNOWN/no-release/no-replay. After resume, the supervisor verified release in 59.355 ms and an independent client saw all keys up in 98.039 ms. The delayed-request horizon and distinct fresh-session synthetic task oracle passed. See the [frozen R01 evidence packet](../research/integration/standard_caller_xvfb_current_main_20261022/prestarted-xserver-pause-01/README.md).

This is one paused-Xvfb schedule. It does not prove release while X11 is stopped or establish physical GUI/MAP01, reliability, matched efficiency, or WSLc portability. The runtime result remains UNKNOWN; no task-success or replay promotion follows from the synthetic oracle.

## Matched Xvfb pause pilot and remaining timing gap (2026-10-22)

A six-trial matched pilot on current main `cc5ef16c560cc985ee0951d3d53d659e892f5167` compared three no-pause controls with three 1.5 s pauses of the exact private Xvfb process. All six passed the frozen admission-based caller, release/readback, fresh-generation synthetic task, and old UNKNOWN/no-replay checks. Admission-to-response ranged 253.263–256.398 ms. Paused-arm independent all-up readback followed Xvfb resume by 101.874–127.834 ms. Full conditions, paired results and raw hashes are in the [pilot packet](../research/integration/standard_caller_xvfb_current_main_20261022/paused-server-matched-pilot-01/README.md).

The test timestamp precedes a deliberate 50 ms stop-confirmation wait; it lacks a timestamp immediately before the caller tool invocation. Actual invocation-to-return and exact fresh-effect observation latency remain unqualified. This small three-pair pilot does not establish broad reliability, matched token/model efficiency, release while X11 is stopped, physical GUI/MAP01, or WSLc portability.

## PR convergence follow-through: #7120 (2026-10-22)

At current `origin/main` `31dd17fa83131d3cdf3c4f3703d98015e411e2e5`,
PR [#7120](https://github.com/Unjuno/agent-interface/pull/7120) was an
old-base draft with a conflicting merge state. Its overflow-safe caller-cost
aggregation and focused aggregate/cost-coverage checks are already present on
current main. The retained experiment packet is also present in the current
tree from rescue commit `cb3fb7cea16ab57c5474164dc17b88f7ff51daa9`.
Against the exact current-main source, 21 aggregate and cost-coverage tests
passed in both normal and optimized Python 3.13.14. The stale PR was closed
after this source/evidence check; the original branch, discussion, and saved
results were retained. No experiment or WSLc/Docker allocation was used.

This closes one historical duplicate PR, not the PR queue. The latest complete
membership receipt remains r138 at its recorded older main SHA; no fresh
full-queue count or semantic census is claimed here. Next cleanup batch: refresh
the live queue, then select one open PR with a bounded source/evidence transfer
or a computer-control family with a clearly finite canonical-record update.

## Current continuation after PR #9400 and supervisor-design review (2026-10-22)

The user selected the prestarted cancellation supervisor design as the first
organization item. The canonical
[design record](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md) already
contains the architecture options, implementation history, requirement/test
crosswalk, and current qualification limits, so this work did not create a
second design document. The supervisor remains opt-in; its open live-platform,
authority, target-recovery, and efficiency boundaries remain research items.

PR [#9400](https://github.com/Unjuno/agent-interface/pull/9400) merged at
`632d3603a8df157c1e841dac7ca422c766c77e60`. It adds the custody recheck for
two changed worktrees. It is documentation-only and does not change the r151
membership counts (1,654 open Issues and 452 open PRs), so no fresh semantic
queue classification is implied.

PR [#9401](https://github.com/Unjuno/agent-interface/pull/9401) merged the
additive transfer of
[`chromium_public_compiled_caller_20261021`](../research/integration/chromium_public_compiled_caller_20261021/README.md)
and its supplemental custody record. The packet preserves the one-shot r09
live Chromium/App Server result found in a dirty worktree whose current owner
is unresolved. The original source packet was not edited. Its earlier
`audit-recheck-r09.json` reports a successful temporary-copy audit of all 317
then-listed artifact entries. A later read-only comparison finds one current
artifact-manifest mismatch (`README.md`, updated after that audit); the other
316 files match, including the raw r09 evidence. The frozen 179-entry source
manifest matches only 161 files in the extant source worktree; 18 runtime
files differ. A read-only comparison across all 48 linked worktrees found no
complete 179-file match. Expected source versions for 170 entries exist in at
least one worktree; nine expected versions were not found. The exact dirty
source snapshot is therefore not reconstructed, and the result is not
represented as current-main evidence. The supplemental
[custody recheck](../research/integration/chromium_public_compiled_caller_20261021/CUSTODY-RECHECK-20261022.md)
records these limits. No experiment was rerun, and the source worktree was
left intact.

Next bounded work is to identify the source worktree owner and recover the
nine unavailable source versions if they remain available outside the linked
worktrees. Then reconcile the frozen source with the intended integration
before any further branch/worktree disposition. Keep #57 open: this packet is one scoped polling
result and does not satisfy its matched three-arm token/latency/correctness
comparison. Continue the Issue/PR inventory from the r151 ID sets in disjoint
batches; do not convert the large open queue into a closure target.

## Current whole-repository checkpoint r152 (2026-11-21)

The paginated membership read is recorded in
[`repository-inventory-recheck-20261121-r152.md`](maintenance/repository-inventory-recheck-20261121-r152.md)
against main `bab0b6fd18a8c64fbc664476ebbf26ef2267f7d7`, read immediately
before and after the Issue and PR enumeration. It contains the exact sorted ID
sets and deltas from r151: 1,643 open Issues (zero added, 11 removed) and 410
open PRs (11 added, 53 removed). This is a queue membership comparison, not
semantic disposition, owner/custody validation, or merge readiness. The next
organization wave must refresh selected records and route their distinct
hypotheses into canonical families; no bulk closure follows from these counts.

Three current-main candidates were verified and integrated during this wave:

- [PR #10354](https://github.com/Unjuno/agent-interface/pull/10354) adds the
  bounded R281 raw audit and expiry-release publication candidate. The live
  trial confirms one task effect, not MAP01 completion, efficiency, or
  reliability. Merge commit: `551cf28bb3ef3249af66d4c1ea33c2ca0b98882e`.
- [PR #10352](https://github.com/Unjuno/agent-interface/pull/10352) adds the
  late App Server usage receipt adapter. Its four changed modules pass 26/26
  normal and 26/26 under `-O`; a broader 107-test local discovery exposed two
  separate Calc/Fake X failures and is retained as nonpassing evidence. The
  adapter is not wired automatically into every runner and proves no provider
  billing or efficiency result. Merge commit: `b049316731b0c8ddf47ed22c3df28c37c9f5d396`.
- [PR #10353](https://github.com/Unjuno/agent-interface/pull/10353) records a
  Windows portable-runtime build on current main: 21/21 normal and `-O`,
  checkout-outside `doctor` and `validate --help` both exit 0, and the
  diagnostic explicitly grants no side-effect authority. Public distribution,
  Linux/WSL startup, and live input remain unverified. Merge commit:
  `bab0b6fd18a8c64fbc664476ebbf26ef2267f7d7`.

Issue #57 remains open: matched integrated token/latency/correctness economics,
standard-caller task success after recovery, repeated reliability, and trusted
fresh comparison allocation are still outstanding. PR #10340 remains a draft
on base `86a52662`. The initial local rebase failure was a property of this
shallow clone, not unrelated PR history. GitHub's compare API confirms merge
base `86a52662dc2bb690dd670d52ea8d97816aef2a26`, with the PR 10 commits ahead
and current main 14 commits ahead; the API-reported changed-file sets have no
path overlap. The broad local rebase was aborted without changing the PR. A
lineage correction and exact file/test audit are recorded in
[`pr10340-lineage-correction-20261121.md`](maintenance/pr10340-lineage-correction-20261121.md).
No WSLc or Docker live allocation was used in this checkpoint.

### PR #10340 follow-up after lineage correction

GitHub updated the draft to current main successfully; new head is
`c47ae761ed7a8c47e6d5d6b16937b468145956cd` and all five checks passed. The PR
remains correctly draft: its own limits say no dispatch, external allocation
attestor, or live comparison. The old Edge evidence is only a local one-form
effect with offline model double. A recheck of its journal suite was incomplete
because the local shallow/sparse tree lacked pinned source files (3 allocation
checks passed; 10 errored on file lookup), so old 12/12 claims are not
reconfirmed for the rebased head. See the correction memo for exact detail.

### #57 experimental work queue (2026-11-21)

Do not close #57, #5130, or historical #908/#879 to make the queue look clean.
Their evidence represents separate dependent gates. The current order is:
(1) prepare an additive fresh successor to #908 for exact pinned v160.2 JAR and
canonical-save setup-only smoke; (2) obtain the named Docker CPU lane and
reconcile sibling ownership required by #5130; (3) execute the single frozen
six-task Mindustry economics allocation and independent raw audit; (4)
separately resolve #57's standard-caller recovered-task and repeated
reliability gates; (5) run the provider-backed matched integrated
token/latency/correctness comparison and verify distributable runtime
boundaries. See
[`issue57-next-gates-20261121.md`](maintenance/issue57-next-gates-20261121.md)
for source and resource evidence. No live resource was touched in this wave.

## Current whole-repository checkpoint r153 (2026-11-21)

The membership was read from the paginated GitHub REST Issue and PR endpoints
between `2026-11-20T20:19:58Z` and `2026-11-20T20:20:37Z`. Remote `main` was
`cfb691b3b890d01c0b24fd1cd988609a62c4dd2a` immediately before and after the
reads. The exact open sets are unchanged from r152: 1,643 Issues and 410 PRs;
their sorted ID CSV byte hashes are unchanged (`9a2abc9b…e1f79` and
`e45999de…3e64b`). The read receipt is
[`repository-inventory-recheck-20261121-r153.md`](maintenance/repository-inventory-recheck-20261121-r153.md).

PR [#10361](https://github.com/Unjuno/agent-interface/pull/10361) was merged
as `cfb691b3b890d01c0b24fd1cd988609a62c4dd2a`. It adds the retained Ubuntu
WSL portable-runtime result: Python 3.12.3 passes the 21-test distribution
suite normally and under `-O`; outside-checkout `doctor` and `validate --help`
exit 0, with the diagnostic granting no side-effect authority. The same
zipapp's 64 Git-managed source hashes match the current-main blobs. This closes
the basic Ubuntu WSL startup gap only; it does not establish live X11 input,
task effects, permission flow, public release, or preview graduation. The
current scoped gate wording is corrected in
[`issue57-next-gates-20261121.md`](maintenance/issue57-next-gates-20261121.md).


Issue #58's read-only first-run launcher boundary was also checked on current
main: 19/19 pass in a fresh sparse Ubuntu WSL ext4 checkout, while the
Windows-mounted checkout retains four CRLF/worktree-byte failures. The
intermediate output-capture failure is preserved and excluded. This current-main
preflight is not the frozen RC1 supported-host setup/doctor or golden run; see
[the packet](../research/integration/research_preview_preflight_current_main_20261121/RESULT.md).

Issue #57 remains open. #908 is a consumed, closed HOLD; #5130 and #7924 remain
open with Docker/WSLc resource ownership unresolved. PR #10340 remains draft
with its five checks green; it is a non-dispatching synthetic journal and has
no external allocation attestor. The pinned v160.2 JAR and canonical saves are now size/hash-verified, but
Ubuntu WSL has no Java runtime; the game has not been launched and the
setup-only smoke remains held. See the
[asset-readiness packet](../research/integration/mindustry_asset_readiness_v1_20261121/RESULT.md).
The next local prerequisite is an available Java runtime; the separate Docker
CPU slot and WSLc ownership gates remain unresolved. Do not start or inspect
Docker, launch Mindustry, or consume a formal comparison slot until the
applicable conditions are satisfied. Do not bulk-close queue items based on
the unchanged membership snapshot.

## Current whole-repository checkpoint r154 (2026-11-21)

On current main `8c71a6199bd51ca6b38aa02cb92d9833c3260a67`, a complete paginated REST reread found 1,643 open Issues and 410 open PRs. Both exact ID sets match r152/r153 (zero added, zero removed); main was the same SHA before and after the reads. Reuse the existing sorted ID CSVs. This confirms stable membership only, not item meaning, ownership, evidence custody, or merge readiness. No bulk state change follows.

The active product/research map remains: #57 is open for standard-caller recovered task success, repeated reliability, and matched all-attempt provider/token/latency/correctness economics; #58 remains open for exact frozen RC1 host setup, retained audit, a fresh no-retry golden run, and `audit-live`. The new R05 setup/doctor packet records pinned Python dependency setup success but a doctor HOLD caused by missing expected Windows Codex CLI JS and WSL Chromium. #5130 is the one-time six-task Mindustry three-arm economics allocation under #57, still gated on its frozen source/resource conditions; #7924 remains the explicit WSLc migration STOP. PR #10340 is still a draft/prospective journal and does not authorize dispatch or supply a trusted allocation attestor. Keep these records open until their distinct gates have evidence; continue bounded family/PR triage from the existing work map instead of treating the unchanged queue as cleaned.

## Issue #57 evidence update (2026-11-21)

The current-main Calc cancellation recheck was corrected with retained failure-boundary evidence. In both normal and -O fail-fast runs, calc_entry resolves as STALE/expired_or_nonfresh_observation at the 1500 ms capture-freshness bound before owner I/O; zero Save states and no input/task effect are recorded. The prior scheduling explanation applies only to the preliminary runs and is superseded for these repros. Test cleanup receipts verify owner retirement/exit 0, without claiming input release. This evidence does not test cancellation recovery. Preserve #57 and the cancellation gate as open; next isolate safe fresh-observation reacquisition with renewed review/admission, and a changed-target negative control.

## Issue #57 evidence update (2026-11-21)

The current-main Calc cancellation recheck was corrected with retained failure-boundary evidence. In both normal and -O fail-fast runs, calc_entry resolves as STALE/expired_or_nonfresh_observation at the 1500 ms capture-freshness bound before owner I/O; zero Save states and no input/task effect are recorded. The prior scheduling explanation applies only to the preliminary runs and is superseded for these repros. Test cleanup receipts verify owner retirement/exit 0, without claiming input release. This evidence does not test cancellation recovery. Preserve #57 and the cancellation gate as open; next isolate safe fresh-observation reacquisition with renewed review/admission, and a changed-target negative control.


The 2026-11-21 cancellation packet also corrected a false-green test wrapper: inner unittest assertions are now propagated. Corrected wrapper tests pass in normal and -O because UNKNOWN after cancel is their expected contract, but the optimized receipt shows a real recovery gap: cancel grace expiry retires the owner (-15), release remains unconfirmed, and close is cleanup_failed despite an independent empty Fake-X readback. Keep this as an explicit open defect/evidence gap, not a completed reliability gate.


The corrected 2026-11-21 paired standard-caller cancellation recheck separates test PASS from product recovery: normal/-O each 1/1 pass and reach Save/cancel, but both custody receipts remain UNKNOWN with release unconfirmed, despite independent Fake-X readback showing empty keys/buttons; close is cleanup_failed. Keep the recovery/release gate open. The packet records excluded exploratory runs and invocation-linked raw, so do not pool historical stale and cancellation outcomes.

**Issue #57 effect-attribution integration gate recheck (2026-11-21, current main 9cc75e28):** Reran test_post_authority_effect_attribution_v1 plus test_comparison_measurement_v1 together using Windows CPython 3.11.9: 27/27 pass normally and under -O, with identical log hash b16483b325beaf6864c364e65c68952a889251ca61e59879ac1bc66e5263e1e9. The matched measurement validator preserves factual final-state success and uses eligibility-aware task success: R149's queue effect at 2,714.9257 ms after expiry and 691.4841 ms beyond the neutral horizon is ineligible; R281's effect timestamp is unresolvable from 50, 50, 49 samples and remains unknown. Audit of the current tree found no production/frozen caller adapter invoking these validators. This is a scoped current-main contract recheck, not a provider-backed matched comparison. No live GUI input, provider call, Docker, or WSLc was used. Next gate: bind real caller receipts and all provider attempts into a frozen matched run, failing closed when evidence is missing; keep #57 open.

**Issue #57 recorded-caller comparison adapter candidate (2026-11-21, based on main `9cc75e28`):** A research-only adapter now projects complete provider recorder journals into measured-run records, verifies event-bound raw custody against disk hashes, and calls the current matched-comparison validator. Three synthetic arms validate as one matched block; missing attribution, incomplete journal, omitted raw references, conflicting hashes for one path, and hash drift fail closed. Normal/-O each pass six adapter tests and the combined attribution/comparison/adapter suites pass 33/33. The reproducible synthetic records, raw files, and the post-hardening R03 rerun are in [the packet](../research/integration/standard_mcp_task_ledger_57_v1/recorded_comparison_adapter_v1/RESULT.md). It does not bind native owner expiry/release evidence or reconcile hidden provider retries; it cannot count as live comparative evidence. Continue toward a production-bound evidence join and keep #57 open.

**Post-merge current-main checkpoint (2026-11-21, `428a38eaac2dce07c7b7557985ec58a998d8736b`):** PR #10373 added a fail-closed research adapter from complete recorder journals into matched measured-run records. Its synthetic A/B/C packet preserves raw bytes and passes all 86 manifest entries. The merged main source passes the combined R149/R281 attribution, measurement, and adapter suites 33/33 normally and under `-O`; GitHub `replay-gate` and `public-navigation` pass while `formal` is skipped. This narrows offline schema integration only. Identity-bound native expiry/release/horizon evidence and independent provider-attempt reconciliation remain absent, so no live efficiency result is established and #57 remains open.

## Issue #57 evidence update (2026-11-21; main `ecb0f037`)

PRs #10380–#10384 preserve the one-shot post-score late-usage positive/control and make its audit portable across clean Windows checkouts. The main-tree audit passes with 6 raw references and 32 manifest entries. PR #10385 adds R01, composing late usage with a second action attempt and identity-bound synthetic native-owner lifecycle evidence; positive 28/5 token totals are complete, while the missing-usage control stays incomplete/null. Its normal and `-O` tests pass 12/12, and clean-main audit verifies 24 raw references and 44 manifest entries. All eligible task/effect outcomes remain UNKNOWN; no live provider, GUI input, Docker, or WSLc was used. Keep Issue #57 open. Next: join a production caller receipt to independent exhaustive provider-attempt evidence. Empirical integrated efficiency, task/recovery reliability, live MAP01, research-preview acceptance, and runtime distribution remain open.


**Golden-v3 result-layer semantics (2026-11-21):** Keep the raw application task assertion separate from the top-level cleanup-qualified outcome. The R01 adapter probe records the deliberate `cleanup_failed` / `task_success=false` envelope when raw task success is true, and the normal/-O focused suite confirms that behavior. Link the packet from current goal and roadmap; do not relabel this existing fail-closed policy as a defect or change the result schema without a contract-level decision.


**G10 public stdio current-main recheck (2026-11-21; tested source `5dab476e`, current main `704ea90c`):** After materializing the exact pinned G10 FODS fixtures in this sparse checkout, `runtime.cli_v1.test_mcp_g10_production_stdio` passed 3/3 normally and 3/3 under `-O`. The public MCP/stdio ledger records two archived-byte fixture effects verified, input release verified, owner close closed and replay denied; provider usage remains unknown. The first R01 attempt in this checkout failed before reliable assessment because the sparse tree omitted `first.fods`; its failure logs are retained separately and are not pooled with the R02 pass. Exact code/fixture pins still match main after the documentation-only crosswalk merge. This is Fake X plus archived FODS, not live Calc/provider evidence or efficiency. See [R01/R02 packet](../research/integration/issue57_g10_currentmain_stdio_recheck_20261121/RESULT.md). #57 still needs a permitted prospective live lifecycle comparison and the broader task/recovery gates.

## Current repository membership checkpoint r160 (2026-11-21)

On main `f39e966b6478170a7a91f1eec7859d30046784bf`, complete paginated reads
found 1,643 open Issues and 408 open PRs, with both ID sets byte-identical to
r159 and zero additions/removals. PRs #10402 and #10403 were opened and merged
after r159 and therefore had no net membership effect. This confirms queue
membership only; full semantic triage and evidence-custody reconciliation of
the 2,051 open records remain unfinished. Do not bulk-close records. See the
[r160 receipt](repository-inventory-recheck-20261121-r160.md).

## WSLc smoke receipt custody follow-up (2026-11-21)

A one-shot pinned-image/read-only-bind WSLc smoke on main `e5866db03e25c044f7ffead5118624a1cd8c33e9` exited 0 and observed `EROFS`. Its successful cleanup removed the exact-CID and query stdout files, so disposition is scoped pass with receipt limitation. The bounded local harness was repaired to emit a JSON exact-CID cleanup receipt into the captured outer log; the offline harness passes on Windows PowerShell 5.1. This does not release shared ownership, close #7924, satisfy #5130, or establish computer-control/economics/reliability. See [result packet](../research/integration/wslc_local_runtime_receipt_fix_20261121/RESULT.md).

**Targeted Draft PR disposition #10144 (2026-11-23; current main `3a705de2`):** Keep open as Draft. Remote comparison reports a 44-commit head with 524 main commits ahead of its base, no merge base, and 174 unique paths (13,629 added lines, no deletions). The only check is a Nov 2 replay-gate pass; the author reported 100/100 prototype tests on Nov 3 but explicitly says the lifecycle adapter is not ready for live use and lists unresolved custody/restart, synchronous deadline, descendant ownership, independent release/scoring, and matched-trial requirements. Later Calc R01-R06 only close synthetic offline joins, not those live requirements. Preserve the unique evidence while reviewing it against current-main records; do not bulk merge or close. See [the targeted disposition](maintenance/targeted-pr-disposition-10144-20261123.md).
