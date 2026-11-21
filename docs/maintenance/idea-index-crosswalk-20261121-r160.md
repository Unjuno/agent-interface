# Current-main Issue index crosswalk r160 — 2026-11-21

## Baseline and method

The latest complete Issue/PR membership snapshot is [r160](repository-inventory-recheck-20261121-r160.md), captured on main `f39e966b6478170a7a91f1eec7859d30046784bf`. The current main used for this crosswalk is `8719919ab01db547c08d816e1884a115f25cecab`; after r160, PRs #10404–#10411 changed documentation only and made no Issue-state changes. The frozen r160 open-Issue set contains 1,643 IDs and has SHA-256 `2b878bf18f22dde388f76611c9c8ae317c70842aed3a06aaff26b66fb11e4aad` in its preserved CRLF form. Its canonical sorted decimal-ID list with LF terminators hashes to `89bc3a4f1f5ca2c135d01bf102ba585b5fea1f56f3c0c3eec881239bfd2fbde1`.

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

Continue with B10 using the same frozen ID join, first checking current Issue state and exact routes. Inspect current bodies, comments, linked PRs, and retained evidence only where a proposed family link or disposition depends on them. Keep leave-open, superseded, duplicate, and evidence-complete outcomes distinct; an exact URL or open/closed state alone never justifies closure. Shared index/map edits should follow completed family-level review, not precede it.

This audit covers navigation for one inventory snapshot and one batch. It does not semantically triage the 1,643 open Issues, reconcile worktree/PR custody, or alter the #57/#58 product gates.
