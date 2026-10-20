# Held-out cross-domain benchmark and independent oracle contract — Issue #12

- **Status:** Open; the evidence-representation subquestion has a scoped method result, while benchmark validity, oracle isolation, claim interpretation, and cross-domain performance remain unverified.
- **Source:** [Issue #12](https://github.com/Unjuno/agent-interface/issues/12); adaptive-cohort successor [#8614](https://github.com/Unjuno/agent-interface/issues/8614); exposure-lineage refinement [#5603](https://github.com/Unjuno/agent-interface/issues/5603).
- **Idea:** Establish when evidence supports a named capability claim across distinct task domains, using fresh/held-out tasks, explicit required and forbidden effects, collateral scope, independent scoring, preserved failures, and matched comparisons. The proposal is a coverage matrix and claim-specific contract, not one universal scalar leaderboard or one “king benchmark.”

## What is established

- **Evidence classification only:** merged [PR #5526](https://github.com/Unjuno/agent-interface/pull/5526) (`r133_domain_coverage_transfer_v1`) recorded a finite axis-separated representation of retained DOOM and Calc evidence. Its candidate and independent auditor agreed, and three promotion-error controls were rejected. This is a scoped method result about faithful classification; it does not establish new GUI/game/model behavior, matched performance, held-out benchmark validity, or transfer between domains. The two earlier T0 infrastructure STOPs remain part of the record.
- **Adaptive tuning is a distinct method question:** [#8614's T0 A01 report](../../research/analysis/uncertainty_intervention_8641_t0_a01_20261009/REPORT.md) records an independently reconstructed synthetic result, `PASS_ADAPTIVE_FEEDBACK_METHOD_SCOPED`: repeated reuse of a finite cohort can create selection optimism in its authored fixture. It does not show bias in existing repository experiments, prove a formal privacy guarantee, or complete #12's broader oracle/domain contract. The Issue remains open for its separate transfer/evaluation question.
- **Exposure lineage is not a mislabel finding:** [#5603's T0 comment](https://github.com/Unjuno/agent-interface/issues/5603#issuecomment-5915868814) records visible reuse of a known six-task layout across a public comparison lineage, while finding no inspected claim that called it untouched held-out evidence. Exact per-variant author exposure remains unknown; no historical result was invalidated and no adaptive bias was quantified.
- **Tail-risk construction is not qualified empirical evidence:** merged [PR #5677](https://github.com/Unjuno/agent-interface/pull/5677) preserves a finite arithmetic example where authored severity changes reverse a binary ranking. Its raw-only arithmetic checks do not calibrate severity or measure GUI risk. The later [resource-coordination erratum](https://github.com/Unjuno/agent-interface/issues/12#issuecomment-5922555357) classifies the overlapping Docker execution as `STOP_RESOURCE_COORDINATION`; preserve the arithmetic artifact, but do not call that container execution a qualified experiment or rerun it. The Issue's later integration note does not erase this STOP.

## Open refinements that stay separate

Issue comments propose several additional checks; each is explicitly unverified and none supersedes the base contract or changes a prior result:

- [Paired-run oracle noninterference](https://github.com/Unjuno/agent-interface/issues/12#issuecomment-5923865209): detect whether changing an oracle-private marker changes a controller trace when all controller-visible conditions are held fixed.
- [Measurement-invariance gate for capability transfer](https://github.com/Unjuno/agent-interface/issues/12#issuecomment-5923929340): require comparable bridge tasks before linking same-named capability axes across domains; otherwise retain separate cells or `NOT_LINKABLE`.
- [Claim-specific score interpretation and use](https://github.com/Unjuno/agent-interface/issues/12#issuecomment-5924711158): audit the chain from observed effect and oracle, to a named capability, target population, and promotion decision.
- [Severity-sensitive tail risk](https://github.com/Unjuno/agent-interface/issues/12#issuecomment-5922504277): an auxiliary diagnostic only, with severity and tail support frozen in advance and forbidden-effect gates never averaged away.

These refinements answer different questions. A pass for one does not qualify the others or validate the benchmark as a whole.

## Next finite decision

Before another allocation, explicitly choose which open refinement #12 will own versus which will remain separate, and name the decision it could change. For the core contract, the next useful bounded artifact is a traceable matrix for one nominated capability axis: task contract and held-out unit; candidate exposure/lineage; controller-visible versus oracle-private channels; independent required/forbidden/collateral effects; scorer version and negative controls; all attempts and failure loci; matched conditions; and the claim/promotion decision supported. If a field or independent oracle cannot be established, record `UNKNOWN`/`HOLD` rather than infer success. Any experiment then needs its own eligible allocation and frozen protocol.

## Limits and disposition

No current result establishes a validated multi-domain benchmark, empirical adaptive bias, cross-domain task transfer, a calibrated failure-severity scale, universal capability, or a single comparable score. Do not pool these method results, close #12 on documentation alone, or infer an empirical claim from a finite constructed example. Keep #12 open until its remaining contract and validation decisions receive their own scoped dispositions.
