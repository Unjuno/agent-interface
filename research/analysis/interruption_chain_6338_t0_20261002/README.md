# Issue #6338 — interruption-chain ledger, T0

## H / T / D / C / U

- **H:** In a deterministic multi-task fixture, source-linked notice revision will reduce delivered endogenous follow-up notices versus emit-each-revision while preserving per-card authority, hard alerts, exact task effects and deadlines. Exogenous-only clustering remains a plausible null.
- **T0:** Native Windows CPU-only simulator; no person, model, GPU, network, WSL or container. Eight frozen fixtures cover a common-cause burst, a two-generation clarification/re-review chain, exact duplicates, target-version invalidation, denial/nonresponse, a cross-principal attempt, mandatory hard alerts and an opaque-card negative control. Compare emit-each, exact-duplicate batching, source-linked same-scope revision, and the explicitly adverse opaque consolidation control.
- **D:** `METHOD_PASS_SCOPED` only if the auditor distinguishes unlinked exogenous events from parent-linked descendants, verifies preserved authority/effects/deadlines/hard alerts, detects a lower-card-but-worse opaque control, and rejects all five planted corruptions. This is a finite-mechanism result, not causal evidence about actual users or attention.
- **C:** Ordinary duplicate suppression may explain the reduction; a hidden common cause may explain temporal clustering; a better task/approval contract may eliminate the chain without a point-process model.
- **U:** Parent edges encode fixture truth only. No inference about real human behavior, attention, Hawkes parameters, actual burden, system prevalence or T1 policy effect.

## Frozen boundary

Source `main` commit: `645bc89c71f28a88d8ff37f995d56057cb4cf734`.
Package: `research/analysis/interruption_chain_6338_t0_20261002/`.
Run ID: `t0-formal-02`; deterministic; candidate invocation exactly once, then independent raw-only auditor exactly once. The first prospective freeze (`t0-formal-01`) was superseded before any candidate launch after final construction review added independent parent-edge and effect-count reconstruction; it remains preserved in `FREEZE-0001-SUPERSEDED.json`. The formal boundary begins only after the revised construction tests, output directory creation and amended prospective freeze comment on Issue #6338. No retry, seed substitution or policy tuning after candidate start.

The primary measures are delivered-card count, reconstructed parent-chain tail, and the trace span from first root event to the final event in the frozen finite trace. The final-event span is only a deterministic fixture proxy for quiescence, not real elapsed time or human waiting. The opaque consolidation control must be reported as `CHAIN_REDUCTION_WITH_BURDEN_UNKNOWN_OR_WORSE`. No remote execution or user contact.

## Reproduce

From this directory on Windows with Python 3.11+: `python -B candidate.py cases.json results/formal-02/candidate.json`; after a zero candidate exit only: `python -B auditor.py cases.json results/formal-02/candidate.json results/formal-02/audit.json`. The results directory is created before either command. Run construction tests separately with `python -B -m unittest -v`.
