# Planner-contract r02 per-arm cost reconciliation

This read-only reconciliation joins the merged #7438/r02 retained task audit with its six separately retained A/B/C schema-preflight calls at source revision `510c98fe46889461dce2a4c0e14e261eaa47e8ed`. The formal experiment itself used frozen source snapshot `13bab54ea6d91978247ecc1b70e5060db752367a`; this accounting reads its immutable post-run evidence from the later archive commit.

Run from a repository checkout containing the pinned archive revision:

```powershell
python -B research/integration/planner_contract_56_4d74_20261004/r02/accounting-reconciliation/reconcile.py > research/integration/planner_contract_56_4d74_20261004/r02/accounting-reconciliation/ARM_COST_RECONCILIATION.json
```

## Results

- Reconciles all 29 r02 model attempts and global totals exactly: input 388,547; output 5,767; cached input 235,264 (subset); reasoning output 2,397 (subset); cache-write input 0.
- Arm A: 14 attempts, 187,847 task+preflight input/output tokens, 136.345 s task elapsed plus preflight wait, 12/12 exact submissions.
- Arm B: 6 attempts, 79,018 task+preflight input/output tokens, 112.945 s task elapsed plus preflight wait, 12/12 exact submissions.
- Arm C: 9 attempts, 127,449 task+preflight input/output tokens, 209.666 s task elapsed plus preflight wait, 10/12 exact submissions, and 9/12 graph successes with three declared safe-yields.
- Arm D: no model attempts, 21.708 s task elapsed, 12/12 exact submissions; human setup cost is unavailable.

B versus A reduces the joined input+output total by 57.93% and task-plus-preflight wait by 17.16% in these two descriptive blocks. C costs 61.29% more joined input+output and takes 85.64% longer than B, while failing the graph-success gate. C is therefore ineligible for an efficiency claim and remains REJECT on the full correctness/effect gate. The exact independently scored block2/task1 submission remains distinct from the declared graph effect failure; this arithmetic does not reinterpret it.

## Limits

Task elapsed includes model wait and excludes schema preflight, process startup and final independent scoring; do not add model wait a second time. Cached/reasoning token values are provider-reported subsets, not additive totals. D setup and monetary cost are unavailable.

This independently reconciles r02; it does not pool it with compiled-comparison A05. It proves retained-JSON arithmetic only, not original-host provenance, authority, arbitrary collateral-content safety, privacy/redaction, general compiler behavior, human setup cost, or product acceptance. It does not replay provider or GUI activity and does not alter the source allocation or its terminal disposition.
