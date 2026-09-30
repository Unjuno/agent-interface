# Issue #4749 formal result

Status: `PASS_ROLE_C_SUPPORT64_SCOPED` (independent audit repaired invocation; see execution note).

## Hypothesis and decision

Paired support-count experiment: role C uses either the first 16 or all 64 training examples, with all other preregistered factors fixed. PASS requires (1) no treatment C score below 0.90, (2) treatment C mean improves by at least 0.01, (3) roles A/B are identical per paired seed, (4) package/loader/integrity controls pass, and (5) an independent audit has zero errors.

## Results

| Measure | Control: C support 16 | Treatment: C support 64 |
|---|---:|---:|
| Mean held-out C accuracy | 0.935474 | 0.956128 |
| Minimum held-out C accuracy | 0.850342 | 0.942383 |
| C cells below 0.90 | 1/10 | 0/10 |

Paired mean C improvement: **+0.020654** (threshold +0.01). Roles A and B were exactly identical in all ten pairs. Each of the 40 package reloads succeeded and left its package unchanged. The independent replay/audit checked 10 seeds and 60 role-seed cells with zero errors.

| Seed | C16 | C64 | Difference |
|---:|---:|---:|---:|
| 7865101 | 0.962402 | 0.960938 | -0.001465 |
| 7865201 | 0.942871 | 0.964600 | +0.021729 |
| 7865301 | 0.850342 | 0.956787 | +0.106445 |
| 7865401 | 0.932373 | 0.942383 | +0.010010 |
| 7865501 | 0.948975 | 0.954590 | +0.005615 |
| 7865601 | 0.952148 | 0.960938 | +0.008789 |
| 7865701 | 0.948242 | 0.945068 | -0.003174 |
| 7865801 | 0.957275 | 0.961182 | +0.003906 |
| 7865901 | 0.913818 | 0.953857 | +0.040039 |
| 7866001 | 0.946289 | 0.960938 | +0.014648 |

## Execution and audit trail

- One formal orchestration was started after freezing sources, image ID, Issue body hash, main snapshot, and seed-collision searches. All 10 builders and all 40 fresh-loader invocations succeeded in the pinned local Docker image (`sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, `linux/amd64`, offline, read-only, 1 CPU, 2 GiB).
- The orchestration's first independent-auditor call exited 1 because its command supplied `/baseline/runner.py` while `audit_formal.py` expects `/baseline` to be a directory containing `FREEZE.json`, `runner.py`, `loader.py`, `audit.py`, and `PREREGISTRATION.md`. The traceback is retained at `formal-output/logs/independent-auditor.stderr.bin`. This was an invocation wiring defect, not a training/loader failure.
- No trainer or loader was rerun and no formal seed was resampled. The same auditor source was run once more, in Docker only, over the immutable existing raw outputs, with the correct baseline directory mount and a separate output directory. It returned `PASS_ROLE_C_SUPPORT64_SCOPED`, 10 seeds, zero errors, paired mean C delta 0.020654296875. Both the original failing audit logs and the repaired audit JSON are retained.
- The frozen orchestrator run is therefore recorded as 50/51 successful invocations followed by a typed auditor-invocation failure; the preregistered independent audit was then completed successfully on the same raw. This scoped result passes the preregistered quality and integrity criteria, with the invocation defect disclosed rather than erased.

## Scope and interpretation

For this synthetic task and seed block, increasing role-C support from 16 to 64 removed the observed sub-0.90 lower-tail cell and improved the mean by more than the registered threshold. This is not evidence of real-time/online learning, natural-skill transfer, broad GUI generalization, production safety, or actuator authority. Ten paired seeds do not establish the frequency of rare tail failures outside this generator.

Detailed raw artifacts, command receipts, stdout/stderr, per-seed packages, loader receipts, and auditor outputs are stored under `formal-output/` beside this report.
