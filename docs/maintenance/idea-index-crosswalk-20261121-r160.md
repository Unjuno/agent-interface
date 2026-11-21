# Current-main Issue index crosswalk r160 — 2026-11-21

## Baseline and method

The latest complete Issue/PR membership snapshot is [r162](repository-inventory-recheck-20261122-r162.md). This file remains the r160 semantic-routing crosswalk, based on main `87f1afe2ad2202a3a5200a4add86190e9f6a1496`; its counts and routing were frozen against the earlier membership/main snapshot. The r160 open-Issue set contains 1,643 IDs and has SHA-256 `2b878bf18f22dde388f76611c9c8ae317c70842aed3a06aaff26b66fb11e4aad` in its preserved CRLF form. Its canonical sorted decimal-ID list with LF terminators hashes to `89bc3a4f1f5ca2c135d01bf102ba585b5fea1f56f3c0c3eec881239bfd2fbde1`.

Recomputed against current-main blobs:

- Primary rows were parsed only from the `Issue inventory` table in `docs/RESEARCH_ISSUE_INDEX.md`.
- Exact canonical GitHub Issue URLs were counted in `docs/IDEAS_AND_OUTCOMES.md` and tracked `docs/ideas/*.md` files (`git ls-tree -r origin/main docs/ideas`: 153 Markdown files).
- The immutable r51 queue `open-issues-missing-research-primary-row-20261019-r51.csv` was joined by numeric Issue ID to r160's current open set.
- Batches B01–B07's queued Issues were rechecked for current open state with direct GitHub Issue reads and joined to exact URLs in the current `IDEAS_AND_OUTCOMES.md` blob. B03/B04 state reads occurred about 2026-11-21 13:23–13:24 UTC; B05–B07 were checked shortly afterward. For B01–B04, B06, and B07 the check was routing-only; comments and linked artifacts were not batch-reviewed, except for the latest #57 comment used to preserve its acceptance boundary and #2369's current operational-policy comment. B05 additionally compares the specific #643 product-distribution requirement with merged #10377 and current #58 launch conditions.

## Current coverage

| Route | Open Issues | Interpretation |
|---|---:|---|
| Primary row in `RESEARCH_ISSUE_INDEX.md` | 1,184 | Present in the selected research inventory. |
| No primary row | 459 | Every ID is already in the historical r51 discovery queue; this is not evidence that an idea is missing or complete. |
| Exact URL in `IDEAS_AND_OUTCOMES.md` | 657 | A direct central idea/outcome route exists; it does not prove semantic reconciliation. |
| Missing from both the research primary table and `IDEAS_AND_OUTCOMES.md` | 0 | Every current open Issue has at least one of these two central routes. |
| Exact URL in tracked `docs/ideas/*.md` | 271 | A local idea/audit route exists; a citation or agenda is not necessarily a canonical family disposition. |
| No primary row, but exact URL in `docs/ideas/*.md` | 221 | Already has a local idea-file link despite the missing research-primary row. |

The r51 queue has 491 historical rows: 459 are still open and lack a primary row; 32 are no longer in the open set. No current open primary-row gap falls outside the old queue. The older `triageStatus=untriaged` values are historical queue metadata, not current semantic decisions.

## B01 current-route crosswalk

All 24 B01 IDs that remain open were fetched from GitHub and are still open. Every one has an exact URL in the current `IDEAS_AND_OUTCOMES.md`. Existing routes preserve distinct topics:

| Topic group | Issues | Current route / disposition |
|---|---|---|
| Architecture risks and north-star thesis | #2, #4 | Preserve the broad risk register and thesis; neither is one completed experiment. |
| Visual addresses and observation presentation | #3, #5, #7, #8 | Keep grid selection, address/feedback contracts, view-set selection, and composite encoding as separate hypotheses under the visual-interface family. |
| Local control, shared semantics, and execution structure | #6, #9, #11, #13, #14, #15, #16 | Keep reactive macros, learned local control, ABI vocabulary, no-authority speculation, attention scheduling, causal trace, and transactional grouping distinct. |
| Evaluation and admission/observation contracts | #12, #18, #19, #20, #21, #22, #23, #25, #26, #28, #29 | Preserve the benchmark/oracle contract and each separate uncertainty, shadow-check, schema, affordance, temporal-feedback, parallelism, probing, risk, history, and cross-modal question. |

This route check confirms that B01 is already represented in the central idea catalog; it does not establish that each route is a current canonical family record or that a research gate passed. The one B01 row no longer open is not dispositioned by absence from r160. No Issues were closed or edited. Do not add duplicate primary rows solely to make the research index resemble a complete idea catalog: its selected-research scope differs from `IDEAS_AND_OUTCOMES.md`.

## B02 current-route crosswalk

All 25 B02 IDs remain open and all 25 have an exact URL in the current `IDEAS_AND_OUTCOMES.md`. Their existing routes cover observation-only recovery, relative viewpoint and semantic targets, handoff/effect/provenance contracts, object identity, clipboard and keyboard semantics, privacy/negative outcomes, capability discovery, invariants/backpressure/checkpoints, scoped targets/caret state, end-to-end timing and actor/readiness attribution, pre-action assurance, adaptive acquisition accounting, symbolic planning, integrated efficiency, and O2/O1 startup custody. These are separate scopes; the broad grouping here does not merge their hypotheses or owner boundaries.

Issue #57 was fetched in its current open state (`updated_at=2026-11-21T12:07:41Z`, 1,270 comments). Its latest comment at this read, [#7062348464](https://github.com/Unjuno/agent-interface/issues/57#issuecomment-7062348464), reports the offline dispatch-disabled #10340 journal integration and explicitly retains the live matched-efficiency, task-effect and recovery-reliability gates. This is a navigation cross-reference, not a new experiment result. No issue state changed.

## B03–B06 current-route crosswalk

All 20 currently open B03 Issues were fetched and remain open; all 20 have exact `IDEAS_AND_OUTCOMES.md` URLs. Their route spans MAP01 acquisition/scoring and lifecycle questions, local control/terminal behavior, observation scheduling, compiled-runtime validation, and retained source provenance. All 23 currently open B04 Issues were fetched and remain open; all 23 have exact central URLs. Their route spans delayed Git delivery/CAS, Inkscape selection/readiness and cross-session identity, native accessibility/event setup, concurrent SVG writes, FFmpeg candidate identity, and correction/retention of earlier watcher claims. Preserve the counterexamples, corrections, and distinct effect domains separately; route overlap is not evidence of a shared resolution.

These are navigation plus current-state checks. No B03/B04 comments or linked experiment packets were reviewed, no issue disposition was made, and no Issue state changed.

All 21 currently open B05 Issues were fetched and remain open; all 21 have exact `IDEAS_AND_OUTCOMES.md` URLs. Their routes span publish/postcondition semantics, Inkscape/AT-SPI selection and event delivery, typed effect outcomes and compensation, short-cue watcher discrimination, MAP01 lifecycle transfer, native-backend promotion, packaging, and retained-evidence/custody work. The route is not a shared resolution.

### Product-distribution Issue #643

Issue #643's pass condition requires byte-identical artifacts built on Linux, Windows and macOS, `doctor` on all three hosts, exact archive closure, and malformed-target fail-closed behavior. Merged [PR #10377](https://github.com/Unjuno/agent-interface/pull/10377) contributes a package artifact (`786,369` bytes; SHA-256 `11804313d731cbebe84d371ce6f3e23871a77a3bf8ccae569dedb68d6ea9e1ea`), a deterministic second-build comparison, 21/21 normal and `-O` Windows distribution tests, a 64/64 pinned-source audit, and outside-checkout `doctor`/`validate --help` startup on Windows CPython 3.13.14 and Ubuntu WSL CPython 3.12.3. The retained report has no macOS build/startup evidence and does not show byte identity across independent OS builds or all three native-backend acceptance gates. This is a scoped advance, but #643's original acceptance remains incomplete; keep it open.

This is separate from #58's Research Preview launch gate. Its launch conditions include the pinned reproducible desktop demo, independent task scoring, reconstructible public measurements, clear claim boundaries and either a genuine real-time MAP01 clear or an honestly labeled unfinished experiment. PR #10377 establishes package integrity/basic startup only; it does not close #58. The [portable-runtime result](../research/integration/portable_runtime_distribution_v2_current_main_acbdfc0f9_20261121/RESULT.md) records these limits. No Issue state changed.

All 22 currently open B06 Issues were fetched and remain open; all 22 have exact `IDEAS_AND_OUTCOMES.md` URLs. Their routes cover temporal sampling and capture overhead, producer-readiness and X11 recovery identity, typed local decision engines, MAP01 sector/heading transfer, speculative and decision-cache proposals, actor attribution, acquisition ordering, and stale-generation ABA protection. These are different method and transfer gates; a central URL does not validate a live effect or promote a local policy. No B06 comments or linked experiment packets were reviewed as a batch, and no issue disposition or state change was made.

## B08 current-route crosswalk

The frozen B08 queue contains 25 Issues. Current reads found 24 open and one closed (#3382); all 25 still have exact URLs in `IDEAS_AND_OUTCOMES.md`. The batch spans MAP01 finite-clear measurement, desktop integration direction, closure audits for prior evidence custody, local System-1 proposals, and public CLI attempt retention. The closure on #3382 is narrow: its latest disposition cites merged PR #3420's source-level two-tier caller audit, explicitly excluding receipt transport, live GUI/model behavior, task effect, and latency. It is not a general approval of its parent hypothesis. For #2679, its latest retained audit says the tested #3156 path was a short measurement probe that explicitly finished before the game episode ended; it did not run model-in-loop control or satisfy the finite terminal-clear criterion. Preserve that distinction and do not treat the old allocation as a result for those unmet conditions. No Issue state was changed.

## Next finite step and limits

All 24 currently open B07 Issues were fetched and remain open; all 24 have exact `IDEAS_AND_OUTCOMES.md` URLs. Their routes span X11 capture/readiness and lifecycle identity, temporal prediction and multimodal source freeze, MAP01 causal/task-effect lineage, calibration/augmentation follow-ups, and local-check policy. For #2369, its current comment and [Worker Quickstart](../WORKER_QUICKSTART.md) agree that workers should run relevant local checks and record hosted-only checks; full CI equivalence before every push is not a repository-enforced gate, and no unified runner is specified. Keep #2369 open as an operational proposal unless a concrete recurring local-check gap justifies a small runner. This does not mean arbitrary local checks replace required checks or experimental preregistration. No B07 issue disposition or state change was made.

All 25 B09 Issues were fetched and remain open; all 25 have exact `IDEAS_AND_OUTCOMES.md` URLs. Their routes cover retained execution/custody records, shared System-1 design proposals, source-level input/effect receipt work, procedural-control benchmarks, known-defect guardrails, and user-centered evaluation. This remains a routing/state pass: no batch-wide comments or linked artifacts were semantically reviewed, and no Issue state changed.

All 25 B10 Issues were fetched and remain open; all 25 have exact central URLs. Selective evidence checks found #6664's finite protocol-model PASS covers 1,191 schedules and 3,573 policy/snapshot decisions with zero false quiescence certificates, but exercises no GUI, OS/backend, model, input, or external effect. The latest #6693 migration note remains `HOLD_SHARED_RUNTIME_AND_SOURCE_OWNERSHIP_UNVERIFIED`; its paired Docker/WSLc comparison has zero formal candidates, auditors, or blocks. Do not use that note as WSLc availability or authorization. #6678's current comment explicitly separates static observation-channel evidence from an unverified adaptive/closed-loop extension. These are bounded evidence reads; no Issue state changed.

The frozen B11 queue contains 25 Issues. Current-state reads found 24 open and one closed (#6990), with exact central URLs retained for all 25. Selective comment checks show #6957 explicitly does not establish a repository-wide concurrency/review gate; #6990 closed only the offline T8 receipt-schema audit and leaves earlier WSLc STOPs intact; #6975's offline T11 publication audit PASS does not change its T7 host-receipt STOP; and #7165 retains its first auditor-runtime `HOLD_AUDITOR_RUNTIME_ERROR`, not replaced by its later raw reconstruction audit. No Issue state changed.

All 25 B12 Issues were fetched and remain open; all 25 have exact central URLs. Selective evidence checks confirm #7430's correction preserves the #7970 prohibition on new WSLc list/run/inventory calls pending ownership reconciliation; #7466's formal `FAIL_UNSAFE_RESUME` remains, while its later raw replay is supplemental artifact validation only; and #7709's `PASS_METHOD_SCOPED` is synthetic latency-inference method evidence, not live performance. No Issue state changed.

Continue with B13 using the same frozen ID join, first checking current Issue state and exact routes. Inspect current bodies, comments, linked PRs, and retained evidence only where a proposed family link or disposition depends on them. Keep leave-open, superseded, duplicate, and evidence-complete outcomes distinct; an exact URL or open/closed state alone never justifies closure. Shared index/map edits should follow completed family-level review, not precede it.

### B13 targeted disposition — Issue #7728 / PR #7758

The #7728 route remains exact in `IDEAS_AND_OUTCOMES.md`; its open state and
research question are unchanged. The linked PR #7758 was directly checked on
2026-11-21: it is still OPEN/DRAFT at head `f7f8fc24`, based on October main
`c520359e`; GitHub reports `DIRTY`. Its A01 runner-source custody and A02
stale-base holds remain in the PR's own evidence. Exact-head synthetic audit
tests pass 3/3 each in normal and `-O`; this is not sensor, task-effect, T0 or
T1 evidence. Keep the Issue and PR open, do not merge the obsolete head or
repeat the one-shot captures. The two-approval language is inconsistent with
the current Worker Quickstart and absent GitHub protection, but is not the
integration blocker; a revived successor should remove that unsupported quota.
See the [current PR disposition](pr7758-disposition-20261121.md). This is one
targeted B13 semantic review, not a full B13 batch completion.

### B13 targeted disposition — Issue #7722 / PR #7735

Issue #7722's only frozen T0 allocation remains consumed. Its preregistered
synthetic hypothesis failed: the reserved server reduced p99 service response
by 71–77%, yet still missed 1–3 of 10 control deadlines on each schedulable
trace. The original `METHOD_PASS_SCOPED` audit was explicitly superseded after
defects were found. The later issue update reports a separate read-only checker
reconstructed 18 retained runs with zero errors and rejected the original six
mutations plus dispatch-order and premature-backpressure mutations; it reports
zero candidate/frozen-auditor invocations. The reported 7/7 construction tests
are repair-branch evidence, not a rerun of the consumed allocation.

PR #7735 remains OPEN/DRAFT at `60d99065`, seven commits ahead of its old base
and 4,062 commits behind current `main` (`b5c7dff`). Preserve its exact
historical packet and the superseded-audit correction; do not rerun T0 or
promote the supplemental checker to host-scheduling evidence. Keep #7722 open
while deciding whether to close only its synthetic T0 hypothesis; any host/GUI
study is a separate question requiring fresh eligibility and independent
release evidence. See the [retained correction](https://github.com/Unjuno/agent-interface/issues/7722#issuecomment-5994116900), [audit-limit update](https://github.com/Unjuno/agent-interface/issues/7722#issuecomment-5985957545), and [PR #7735](https://github.com/Unjuno/agent-interface/pull/7735). This remains a targeted disposition, not a full B13 semantic review.

### B13 targeted disposition — Issue #7732 / predecessor #6774

Issue #7732 is a proposed finite successor about combinations of evidence
fields. Its own body explicitly gates any experiment on custody/ownership
reconciliation for #6774 and forbids rerunning that consumed allocation. The
dependency remains unresolved: #6774's latest retained owner update says the
nine-row packet's seven source/output hashes differ from published blobs by a
terminal CRLF, and its published auditor cannot parse the terminal blank JSONL
line. The separate 12-row local packet matches its ten-file manifest, but does
not identify a unique executor. These limitations qualify both histories; they
do not establish a corrected scientific result or authorize a new allocation.

Keep #7732 open but HOLD execution until the existing #6774 custody request is
resolved or the unavailable originals and accountable custodians are explicitly
recorded. Preserve #6775's merged bytes and both reported histories unchanged;
do not normalize line endings, repair/replay the consumed T0, or run the
successor against a substitute allocation under the same identity. If the
custody gate is eventually resolved, #7732's distinct minimal-field-bundle
question needs its own fresh preregistration. See [#6774's custody status](https://github.com/Unjuno/agent-interface/issues/6774#issuecomment-5988381606), [#6775's byte-level qualification](https://github.com/Unjuno/agent-interface/pull/6775#issuecomment-5958513653), and [#7732](https://github.com/Unjuno/agent-interface/issues/7732). This is the third targeted B13 disposition, not a full-batch review.

### B13 targeted disposition — Issue #7741 / PR #8181

The retained sequence has materially different outcomes. T0 v1 is
`METHOD_FAIL_OR_INCONCLUSIVE` after 217 lifecycle-accounting errors, a task-start
probability defect, and invalid controls; T0b stopped before JSON output and
was not audited. T0c's independent replay was clean and its primary contrast
reversed in 16/16 cells, but its per-principal negative control also reversed
in 11/16, so that frozen gate failed. The later separately preregistered T0d
passed its synthetic gate: 256 groups, zero replay/accounting errors, 32/32
qualifying topology/parameter/seed cells, +94 to +128 tick difference-in-
differences against a three-tick model threshold, and exact-null no-imitation
and shared-24 controls. Preserve all four outcomes; T0d does not erase the
predecessor failures.

Old Draft PR #8181 was closed as superseded after merged current-main [PR
#10419](https://github.com/Unjuno/agent-interface/pull/10419) imported the exact
23-file T0d packet at merge `85a1d02d`. The 22-file SHA256SUMS and seven focused
construction/evidence tests passed locally in normal and `-O`; all applicable
hosted checks passed and formal was skipped. The merge adds a sorted current-main
index entry and `-text` protection for both hash-bound T0c/T0d directories,
without changing the frozen packet or rerunning candidate/auditor. Keep #7741
open for unmet external validity. The result remains synthetic mechanism
sensitivity, not evidence of human adoption, production queue load, or deployment
harm. See [the T0d result](https://github.com/Unjuno/agent-interface/issues/7741#issuecomment-5993680943) and [PR #8181](https://github.com/Unjuno/agent-interface/pull/8181). This is the fourth targeted B13 disposition, not a full-batch review.

### B13 targeted closure — Issue #7748 / PRs #7762 and #8182

Issue #7748 was closed on 2026-11-22 JST after completing its declared finite
synthetic-method question. Merged PR #7762 reports `PASS_METHOD_SCOPED` on six
hash-frozen traces; merged PR #8182 preserves the A01 CLI STOP and separate A02
`PASS_DUPLICATE_ID_BOUNDARY_SCOPED`. The closure comment records both results
and explicitly excludes real workload bounds, host/WSL scheduling, GUI behavior,
physical release, and product deadlines. This does not close related Issue
#8061 or resolve #7722's consumed allocation. Keep the historical r160 batch
counts as a dated baseline; at this first closure the frozen 25-item B13 cohort had 24 open Issues and one closed (#7748); the later #7765 closure brings it to 23 open and two closed. See [the closure comment](https://github.com/Unjuno/agent-interface/issues/7748#issuecomment-7064746136), [PR #7762](https://github.com/Unjuno/agent-interface/pull/7762), and [PR #8182](https://github.com/Unjuno/agent-interface/pull/8182).

### B13 targeted closure — Issue #7765 / PRs #7772 and #7782

Issue #7765 was closed on 2026-11-22 JST at its preregistered finite synthetic
scope. T0 remains `HOLD_METHOD_DESIGN_CONFOUNDED` because the gain arms differed
and no separate calibration was used. Calibration A01 remains an immutable
`STOP_CALIBRATION_AUDIT_FAILED`; the distinct A02 training calibration is
audited and selects fixed gain 0.9. The held-out result independently
reconstructed 240 rows with zero errors, matched all goals, and recorded zero
safety violations, but fixed gain required 185 corrections versus 191 for
online Jacobian, failing the preregistered >=20% improvement gate as
`FAIL_NO_GAIN`. Merged PR #7772 retains both studies; #7782 changes only harness
validation. The closure comment and issue ledger explicitly state no real-GUI,
task-effect, or host-timing result. Any live application comparison is a
separate hypothesis. The 25-item B13 cohort now has 22 open Issues and three
closed (#7748, #7765, and #7817), with all routes retained. See [the closure comment](https://github.com/Unjuno/agent-interface/issues/7765#issuecomment-7064868582), [PR #7772](https://github.com/Unjuno/agent-interface/pull/7772), and [PR #7782](https://github.com/Unjuno/agent-interface/pull/7782).

### B13 targeted closure — Issue #7817 / merged PR #7938

Issue #7817 was closed on 2026-11-22 JST at its declared finite T0 method
scope. The retained one-shot candidate and independent auditor each exited 0
with zero retries; 10/10 authored contexts and proof paths matched the frozen
oracle, and all 5/5 applied hostile mutations returned their frozen
`UNKNOWN_STOP` reasons with no authority change. A read-only Git-blob audit
verified all 17 package manifest entries against current main. The packet does
not establish normative policy legitimacy, source interpretation, extraction
completeness, GUI/runtime safety, or action authority. The old issue comment's
two-review request was stale: PR #7938 is already merged, and repository
policy has no fixed reviewer quota. See [PR #7938](https://github.com/Unjuno/agent-interface/pull/7938), [the retained report](../../research/analysis/provenance_defeasible_obligations_7817_a01_20261005/REPORT.md), and [the closure comment](https://github.com/Unjuno/agent-interface/issues/7817#issuecomment-7065690444).

### B13 targeted HOLD recheck — Issue #7773

Issue #7773 remains OPEN at `HOLD_NO_CANDIDATE_LIST_CONSUMER`. A new read-only
check against current main `85a1d02d65bf901e8f4069564e7b8067fda34898` on
2026-11-22 JST searched `runtime/cli_v1`, `runtime/core_v1`,
`runtime/guarded_x11_v1`, and `runtime/USING_CURRENT_INTERFACE.md` for
target-belief/candidate-list serialization and found no model-visible ordered
consumer. This is a bounded source feasibility check, not proof about external
providers and not an H result. No candidate, model, GUI, or action ran. Do not
replace the required treatment with tool-list/image order or detector-internal
ranking. Resume only after a concrete identity-stable consumer exists and its
ownership/allocation are rechecked; T1 still requires a separately frozen
experiment. See [the current-main HOLD comment](https://github.com/Unjuno/agent-interface/issues/7773#issuecomment-7064923854) and [the Issue](https://github.com/Unjuno/agent-interface/issues/7773).

This audit covers navigation for one inventory snapshot and one batch. It does not semantically triage the 1,643 open Issues, reconcile worktree/PR custody, or alter the #57/#58 product gates.
