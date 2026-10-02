# Issue #5329 — backward evidence slice T0

This package tests the unverified backward-slice construction idea recorded in
Issue #5329 comment #5923874105. It is separate from the earlier four-packet
task-conditioned bottleneck toy, Blackwell/deadline addendum, and production
full/summary caller measurement.

## Allocations and dispositions

- **Formal01:** `STOP_PROVENANCE_OR_RUNNER`. The runner produced four rows, but
the frozen auditor exited 1 on the deliberate unresolved `external_cause` edge.
Its exact raw and traceback remain immutable under `results/formal01/`.
- **Formal02:** `PASS_METHOD_SCOPED`. A fresh allocation and unique output with
a corrected dangling-edge sentinel audit produced raw/oracle agreement across
four authored cases and rejected all four corruption controls. See
[`formal02/`](formal02/README.md) and its result disposition.

Formal02's clean/noise case retained 7 of 19 graph nodes (63.2% fewer nodes,
not a byte/token/latency measurement). Label-only was wrong on three cases;
typed slicing matched the declared oracle on all four. The data-only policy
returned UNKNOWN where required predicates were absent.

These are finite authored-graph results only. They do not validate real GUI
dependency completeness, exogenous-cause discovery, empirical consumer savings,
production safety, task effects, or universal sufficiency.
