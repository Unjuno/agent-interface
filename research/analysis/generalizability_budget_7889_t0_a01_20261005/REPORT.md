# Issue #7889 T0 result: PASS_METHOD_SCOPED

The frozen synthetic T0 supports the preregistered method claim that, under these declared crossed normal models, allocating a fixed 96 paired observations across more distinct tasks/apps can improve decision reliability when route contrasts vary across tasks or apps. It does not measure any real model, interface route, application, or task population.

| Profile | Repeats: 3×4×8 | More tasks: 3×16×2 | More apps: 8×6×2 |
|---|---:|---:|---:|
| Main effect only | 0.9995 | 0.9985 | 0.9995 |
| Task interaction | 0.7900 | 0.9355 | 0.9353 |
| App interaction | 0.6680 | 0.6785 | 0.7530 |
| Combined interactions | 0.6700 | 0.7043 | 0.7955 |

These are empirical frequencies from 4,000 deterministic simulation replicates per design/profile. Exact Gaussian truth was within 0.01271 maximum absolute difference. Estimated variance components were within 0.00528 maximum absolute error of their planted values. The route-main-only profile showed no meaningful advantage for breadth (largest observed advantage: 0.0005 in absolute value). In task, app, and combined interaction profiles, the best breadth design improved observed decision probability over repeat-cells by 0.1455, 0.0850, and 0.1255 respectively.

In the rare-hard-task stratum, designs covering 48 distinct tasks had exact decision probability 0.9166 compared with 0.8864 for the 12-task repeated design. Missing paired and unknown outcomes returned their preregistered HOLD statuses. The independent raw-ledger auditor passed 40/40 checks, including all five declared mutation controls.

**Scope:** This is a finite-generator analysis-method result only. It does not validate binary mixed models, actual benchmark/deployment sampling, causal route effects, a prospective sample-size recommendation, task scoring, safety, or transfer beyond the frozen population assumptions. Issue #7889 T1 historical cohort audit and T2 separately gated prospective route study remain outstanding.

Reproduction: use the pinned WSLc commands and frozen input hashes in `COMMANDS.json`, `FREEZE.json`, and `SHA256SUMS.txt`; candidate and independent-auditor command logs, raw ledgers, result JSON, and hashes are retained beside this report.
