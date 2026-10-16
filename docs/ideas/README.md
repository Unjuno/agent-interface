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

- [Visual representation, addressing and feedback](visual-interface.md) — optional grids (#3), visual addresses/feedback contracts (#5), and composite observations (#8), with [the research execution agenda](visual-interface-agenda.md). That agenda keeps image-space Jacobian adaptation (#7765) separate from #5's safety/recovery contract and records its confounded T0 and no-gain T0b outcomes. Original bodies and provenance are preserved; the three source Issues were reopened after correcting premature consolidation closures.

- [Model coupling and evaluation validity](model-coupling-and-evaluation-agenda.md) — keeps opaque model-behavior stability (#6001), model-by-interface interaction (#6035), action-selected cue-reliability feedback (#8654), benchmark-variant transition equivalence (#8920), and agreement-conditioned bounded continuation (#9004) distinct while connecting their scoped evidence and next tests.
