# Issue #5557 T15-03 — bounded-transport temporal experiment

Fresh one-shot allocation `ISSUE-5557-TEMPORAL-SERVICE-T15-20261001-03`. It preserves the preregistered T15 finite workload while replacing the stalled checkout/archive source path with bounded, hash-verified raw-file transport. See [PLAN.md](PLAN.md), [FREEZE.json](FREEZE.json), and [SHA256SUMS.txt](SHA256SUMS.txt). Candidate and auditor source are unchanged from T15-02.

The experiment has not run merely because this package exists. Results, if produced, are retained under `results/formal-03/`. T15-01/02 remain immutable infrastructure STOPs. The scope is a finite synthetic feasibility model, not production schedulability or product benefit.
