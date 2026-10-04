# Issue #7709 T1 — retained route-trace feasibility audit

## H / T / D / C / U

**H.** Existing retained route evidence may or may not contain enough independent prepared runs, ordered trial endpoints, complete attempt/censor denominators, and stable route/task/model identity to support the prospective segment-aware comparison in #7709.

**T.** Read-only audit of three candidate evidence groups at one exact `main` commit: the public six-task direct/guarded comparison and its 1,051-file archive; three older one-shot API/CLI/MCP transport-unit comparisons; and the #3569 model-route preflight STOP. Read Git blobs directly, verify the complete public archive manifest in memory, reconstruct route/task/time counts, and keep noneligible groups separate. No archive extraction to disk and no runtime replay.

**D.** Advance to T2 only if retained evidence contains enough independent prepared route pairs and complete, comparable run/task/model/route/time/censor metadata. Otherwise preserve an explicit HOLD. The audit does not pool heterogeneous route-unit samples with the public task comparison.

**C.** This is a bounded feasibility audit of the identified main-branch evidence groups, not a search of private/unpublished workspaces. README-level protocol facts remain source claims unless independently present in raw data.

**U.** Whether fresh prospective runs could satisfy the identity, denominator, and power requirements remains unknown. No live allocation is authorized by T1.

## Finding

`HOLD_TOO_FEW_INDEPENDENT_RUNS`. The only model-visible route comparison is one exploratory fixed-order direct→guarded pair (six tasks per route), with no independent prepared pair IDs; direct task 6 lacks the final visual completion cue, though its independent exact-once submission is retained. Three transport-only experiments each contain one sample per API/CLI/MCP route, but have no model/task/effect and structurally different timing boundaries. The #3569 route-host preflight STOP made zero route/model calls. These cohorts are not pooled. No eligible historical data support a held-out segment-aware route inference.

See `REPORT.md`, `RESULT.json`, `AUDIT.json`, `FREEZE.json`, and `SHA256SUMS`.
