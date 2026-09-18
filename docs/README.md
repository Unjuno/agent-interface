# Documentation

This directory is the public documentation map for Agent Interface. It organizes the existing project record; the linked research reports and retained artifacts remain the evidence source.

## Start here

| Question | Canonical document |
|---|---|
| What is the project trying to do? | [Project README](../README.md) and [principles](principles.md) |
| What is the current research objective? | [CURRENT_GOAL.md](CURRENT_GOAL.md) |
| What architecture is currently promoted? | [architecture.md](architecture.md) |
| What has been measured so far? | [PROGRESS_FROM_BASELINE.md](PROGRESS_FROM_BASELINE.md) |
| What is the detailed evidence ledger? | [RESEARCH.md](../RESEARCH.md) |
| What are the latest failures, handoffs, and next steps? | [LOCAL_RESEARCH_HANDOFF.md](LOCAL_RESEARCH_HANDOFF.md) |
| What remains before a public release? | [ROADMAP.md](../ROADMAP.md) and the [release contract](../release/README.md) |
| What can currently be run? | [runtime/README.md](../runtime/README.md) |

## Documentation layers

### Current status

- [CURRENT_GOAL.md](CURRENT_GOAL.md) — current governing invariant and active research direction.
- [PROGRESS_FROM_BASELINE.md](PROGRESS_FROM_BASELINE.md) — evidence-backed progress, measured bottlenecks, and remaining gates.
- [LOCAL_RESEARCH_HANDOFF.md](LOCAL_RESEARCH_HANDOFF.md) — detailed running handoff across experiments and failures.
- [SEMANTIC_EVIDENCE_STATUS.md](SEMANTIC_EVIDENCE_STATUS.md) — scoped semantic-evidence status.

### Design and architecture

- [principles.md](principles.md) — project thesis and component principles.
- [architecture.md](architecture.md) — current promoted architecture.
- [CANDIDATE_ARCHITECTURE_REVIEW.md](CANDIDATE_ARCHITECTURE_REVIEW.md) — architecture review material.
- [design-theses.md](design-theses.md) — design theses retained for reference.
- [control-codec.md](control-codec.md) — control-codec design notes.

### Research and evidence

- [../RESEARCH.md](../RESEARCH.md) — top-level evidence ledger and claims index.
- [../research/README.md](../research/README.md) — map of the experimental workspace.
- [../research/](../research/) — experiment sources, reports, raw summaries, audits, and retained negative results.

### Runtime and release

- [../runtime/README.md](../runtime/README.md) — current runnable construction preview and runtime entry points.
- [../release/README.md](../release/README.md) — public release contract and readiness boundary.
- [product-hunt.md](product-hunt.md) — launch/presentation notes; not a research-status source.

### Coordination records

- [orchestration/](orchestration/) — retained coordination/launch records. These are operational history, not the canonical statement of current project status.

## Suggested reading order

```text
README.md
  -> docs/CURRENT_GOAL.md
  -> docs/architecture.md
  -> docs/PROGRESS_FROM_BASELINE.md
  -> RESEARCH.md
  -> individual research reports / raw evidence
```

For current claims, prefer the canonical documents above over inferring status from directory names or historical experiment filenames.
