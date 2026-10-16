# Idea History

This directory is the compact history of ideas raised in Agent Interface.

Use this directory to connect ideas to existing evidence, dependencies, priorities and executable experiments. GitHub Issues remain the discussion and execution surface. Preserving an idea here does not remove it from research consideration or justify closing its Issue. Close only for verified completion, evidence-based rejection, or an actual successor that carries the remaining research forward. See the [repository consolidation plan](../REPOSITORY_CONSOLIDATION.md).

## What belongs here

For each idea, retain:

- **Idea** — the proposal or hypothesis in one short statement.
- **Source** — the originating GitHub Issue(s) or retained research record.
- **Outcome** — what was learned, implemented, rejected, superseded, or left unresolved.
- **Status** — one of:
  - **adopted**
  - **rejected**
  - **superseded**
  - **on hold**
  - **unverified**
  - **inconclusive**

Closed Issues remain valid provenance and should not be omitted merely because they are closed.

## Entry format

```markdown
## <Idea title>

- **Status:** <status>
- **Source:** #123, #456
- **Idea:** <one-paragraph summary>
- **Outcome:** <brief result; link to detailed evidence when useful>
```

## Index

- [Safety control, interruption, evidence and recovery](safety-control-agenda.md) — distinct hypotheses in #2/#10/#14/#15/#16/#17, dependencies and executed public-path Fake X blocking characterization. These parent ideas remain open.

- [Visual representation, addressing and feedback](visual-interface.md) — optional grids (#3), visual addresses/feedback contracts (#5), and composite observations (#8), with [the research execution agenda](visual-interface-agenda.md). Original bodies and provenance are preserved; all three source Issues were reopened after correcting premature consolidation closures.

- [Benchmark wave comparability](benchmark-wave-comparability.md) — anchor-gated linking of changed benchmark waves (#8885), subordinate to direct same-task comparisons and preserving per-family and safety outcomes.

- [Assumption-gated evidence acquisition](evidence-acquisition-policy-selection.md) — tests when greedy observation choice is justified and when bounded lookahead is worth its cost (#8879), without granting runtime authority.

- [Counterfactual responsibility for negative queries](negative-query-counterfactual-responsibility.md) — preserves #8624's finite method result and duplicate-allocation boundary while keeping query completeness and live visual applicability separate.

- [Query-private evidence-location lookup](query-private-evidence-location.md) — preserves #8000's no-eligible-workload HOLD and separate WSL-container STOP; no PIR or privacy result is claimed.

- [Effect-indexed semantic deoptimization](effect-indexed-semantic-deoptimization.md) — records #8040's finite cursor-reconstruction PASS while keeping external GUI effects, runtime resumption, and its Draft evidence PR unresolved.

- [Failure-episode unitization sensitivity](failure-episode-unitization-sensitivity.md) — records #7857's synthetic segmentation-sensitivity result and the separate T1 HOLD for lack of eligible continuous traces.
