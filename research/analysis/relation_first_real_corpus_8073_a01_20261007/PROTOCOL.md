# Issue #8073 real-corpus retrieval experiment A01

Status: frozen protocol; search has not started.

Allocation: `RELATION-FIRST-8073-REAL-CORPUS-A01-20261007-01`
Base: `9fb2dd6782d1d1477a00d14be870487fd4c54fa2` (`origin/main`)
Issue: [#8073](https://github.com/Unjuno/agent-interface/issues/8073)
Predecessor synthetic discriminator: [PR #8238](https://github.com/Unjuno/agent-interface/pull/8238), preserved and not rerun.

## H / T / D / C / U

**H.** With equal retrieval effort over one frozen public-web search surface, relation-graph queries will produce a higher independently rated yield of structurally valid, nonduplicate cross-domain source candidates than target-vocabulary queries, without lowering concrete-testability ratings by more than 0.5 on a five-point rubric.

**T.** Eight currently open target Issues are frozen below. For each target, issue-keyword and relation-graph conditions each receive exactly one query and at most five organic results, with the same engine, locale, date, time window, and result limit. Searches are paired and the arm order alternates by target. Record all returned results and exclusions. Canonicalize URLs/DOIs and deduplicate within target before rating. Replace arm labels with random IDs and remove query text, rank, snippets that explicitly reveal the query, and arm provenance from assessor packets. Two independent assessors, not the searcher, score each candidate. No source is promoted to repository evidence merely because it was retrieved.

**D.** `PASS_METHOD_SCOPED` requires: (1) >=8 targets with both arms completed under the frozen budget; (2) >=80% of candidates have source identity verified from a publisher, DOI, or recognized index; (3) both assessors complete every packet without access to arm/query provenance; (4) inter-rater weighted kappa >=0.60 on the primary validity decision; (5) relation-first valid-and-nonduplicate yield exceeds keyword-first by >=10 percentage points under paired target-level scoring; (6) mean testability is no worse than -0.5 points; (7) low-lexical/high-relational seeded controls are retrieved in more relation-first than keyword-first cells, while high-lexical/low-relational decoys are not accepted as valid transfers; and (8) an independent audit finds equal budgets, intact blinding, complete lineage, valid citations, and exact scoring reconstruction. `FAIL_METHOD` if the completed, adequately rated sample misses the practical margin or relation-first creates excess false/decorative analogies. `HOLD` if independent assessors, source verification, corpus-surface stability, or blinding cannot be established. No candidate-quality result is inferred from retrieval counts alone.

**C.** Familiar terminology and expert knowledge may already surface useful sources; relation graphs can add effort and encourage decorative mappings. A two-stage hybrid could outperform either arm.

**U.** Search results vary by location, index updates, personalization, and time. Eight targets and two assessors cannot establish broad research productivity or idea truth. This protocol tests only the frozen query method and target set; no runtime, user, safety, or product claim follows.

## Frozen targets and paired query budget

For each row, submit one exact query per arm to the same public search interface, with a maximum of five organic results. Do not reformulate a query, use follow-up/click-through ranking as a new result, or replace an inconvenient result. If an arm errors, preserve it and classify the paired target `HOLD`; no retry in A01.

| Target | Issue | Keyword-first query | Relation-first query |
|---|---:|---|---|
| AT handback context | #8166 | screen reader browse cursor preserve reading position after agent interruption handback | restore a suspended user's navigation context after another actor temporarily changes shared interface state; preserve an anchor and resume without steering |
| Safety reassessment spacing | #7831 | deadline constrained minimum spacing safety reassessment stale control | schedule recurring inspections when frequent measurements have a cost but waiting too long can miss a hazard change under uncertain detection delay |
| Crash recovery receipts | #7802 | machine crash durability effect recovery receipt torn missing confirmation | after restart decide whether a non-idempotent external action already happened when its local confirmation record may be missing or torn |
| Deferrable work windows | #7794 | carbon aware scheduling deferrable jobs deadline energy emissions | allocate flexible work to temporal windows with changing external resource cost while preserving hard completion deadlines |
| Memory locus | #8057 | internal versus environmental memory GUI task sequence retrieval | decide where information used across repeated tasks should reside so it remains available but can be checked against current source of truth |
| Hidden-state belief update | #5368 | action conditioned belief contract hidden interface state stale evidence | when an action changes hidden state update confidence in facts that cannot be observed directly and decide when to measure again |
| Typed quantity persistence | #6524 | GUI unit conversion quantity effect oracle typed values persistence | preserve physical meaning of a value across multiple representations and operations, detecting when a transformation silently changes that meaning |
| Ambiguous identity observation | #7165 | memory guided discriminating observations ambiguous object identity | choose the cheapest new measurement that distinguishes candidates sharing visible features, and refuse when no available observation resolves identity |

## Frozen handling rules

- Search only the public web surface; do not use repository source code, Issue/PR text, or prior experiment results as candidate sources.
- Search result ranking is the sampling mechanism. Capture date, exact query, rank, title, URL, displayed source/date, and visible snippet losslessly. Do not silently drop duplicates, negative results, inaccessible records, or irrelevant hits.
- Deduplication uses DOI first, otherwise normalized canonical URL; retain all arm/rank occurrences in lineage.
- Assessors score source validity, structural correspondence, concrete transfer mechanism, repository non-duplication, falsifiable minimum test, and expected value on the Issue's rubric. Primary valid/nonduplicate requires source validity and structural correspondence >=4/5, testability >=3/5, and no repository duplicate; disagreement is retained.
- The searcher is not an eligible assessor. If two independent assessors cannot be obtained, do not self-score or report PASS/FAIL; retain retrieval receipts and disposition `HOLD_NO_BLINDED_ASSESSORS`.
- Seeded positive and decoy controls are scored separately and must be labelled before search but hidden from the searcher and assessors until scoring. If the selected search surface cannot execute blinded seeded controls without query leakage, record `HOLD_CONTROL_BLINDING` rather than substituting a synthetic result.

## Execution record

No search has been executed at freeze time. Search outputs, assessor packets, ratings, independent audit, hashes, and terminal disposition will be added as separate immutable files. Any protocol change requires a new allocation; the A01 result is never overwritten or rerun.
