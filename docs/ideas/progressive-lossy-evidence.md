# Progressive and lossy evidence descriptions

## Separate questions: #8865 and #8875

These open proposals concern how evidence can remain useful as the model-facing budget or delivery state changes. They are related by graded information, but have different experimental units and must not be counted as one result.

### Nested summaries across budgets — #8865

**Idea.** Compare a single progressive `base + refinements` stream with independently optimized summaries for different evidence/token budgets. The central question is whether requiring later summaries to preserve earlier summaries imposes a cost in decision sufficiency.

**Important design refinement.** The Issue's 2026-10-12 addendum identifies receiver side information as a confound: if a local verifier and a rich model receive different evidence, summary differences may come from those private inputs rather than nesting. A discriminator should hold receiver information explicit and compare like-for-like. The source-coding literature motivates the question but says nothing directly about GUI evidence or agent cognition.

**Status:** Open and unverified. No allocation or result is reported. See [Issue #8865](https://github.com/Unjuno/agent-interface/issues/8865).

### Independent descriptions under loss — #8875

**Idea.** Test whether each independently received semantic description, including reordered or incomplete subsets, can provide a conservative lower-utility planner view before full reconstruction, and whether combining descriptions improves decision usefulness under loss.

This differs from #8865's prefix/budget nesting comparison and from error-correcting transport: the proposal asks for declared semantics for partial subsets, not only eventual exact recovery. Its latest prior-art note identifies semantic multiple-description coding work, narrowing novelty; any T0 should compare established coding baselines and distinguish source reconstruction from planner-level decision value.

**Status:** Open and unverified. No transport implementation, planner result, GUI safety claim, or current feedback-loss defect is reported. See [Issue #8875](https://github.com/Unjuno/agent-interface/issues/8875).

## Shared boundaries

Any future study should keep evidence completeness and action authority separate: a partial description can be useful for planning without satisfying freshness, verification, or effect requirements. No result here establishes semantic correctness, safe GUI action, reduced latency, or useful performance for Agent Interface.
