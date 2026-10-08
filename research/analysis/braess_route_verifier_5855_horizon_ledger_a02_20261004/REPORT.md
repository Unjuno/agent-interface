# Issue #5855 A02 — retained result

Disposition: `PASS_HORIZON_LEDGER_TRANSFER_SCOPED`, deterministic synthetic accounting projection.

The frozen #5855 T0 raw output was read-only input. A new candidate projected 416 task rows into 832 offer/disposition events across six cells and 26 policy arms. An independently coded auditor reconstructed the projection and checked conservation after every event, unique task dispositions, identity, and source hashes. It passed. Four of 16 greedy held-out tasks were not completed within the declared common observation horizon, while all 16 baseline tasks were; across the full dataset 83 of 416 rows were right-censored.

This supports only transfer of the accounting method to the retained finite synthetic trace. The source already contains eventual outcomes, so this is not an online censoring test, a rerun of the route experiment, or evidence about production queues. Docker could not enumerate images because of a missing containerd content blob; the single candidate and auditor ran on host CPython 3.14.5 and are explicitly not container-validated.
