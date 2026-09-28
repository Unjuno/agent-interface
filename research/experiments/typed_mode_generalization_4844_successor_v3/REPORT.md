# Issue #5189 — typed-mode fresh-seed result

**Disposition: `HOLD_COVERAGE_TRADEOFF`.** The frozen single-runner Docker Desktop allocation completed and the separate raw-only auditor independently reconstructed all 4,800 rows, reported `errors=[]`, and rejected all 16 directed corruptions. The preregistered primary-block conjunction did not pass.

## Frozen execution and evidence

- Allocation `typed-mode-4844-successor-20260928-03`; training/heldout seeds 484431/484432; 2,000 balanced training rows and 4,800 heldout rows (960 in each of five blocks, 192 per mode/block).
- Source freeze commit `fcf06f1bf4ce85952658cf9f53e38899dfc51530`; exact source hashes/Git blobs and commands are in [FREEZE.json](FREEZE.json) and [PLAN.md](PLAN.md). Formal source copied byte-for-byte from that commit and rechecked before launch.
- Docker Desktop `desktop-linux`, Docker client/server 28.5.1; image config digest `sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a` (`linux/amd64`, Python 3.12.14). Runner and auditor each used network `none`, read-only root, read-only source, 1 CPU, 512 MiB, 32 PIDs, `no-new-privileges`, and bounded tmpfs `/tmp`. No other container was running at preflight or left running afterward.
- Runner container `e3b9b407bbbb71b7f70663417fab548d273db7f6906e4da85a76143efc93c4cf`, exit 0. Auditor container `48bd68fdee2e2276521212c522760c5eeccb8f7ed3a5238e859f64325d8a1626`, exit 0. Each was inspected and removed after exit. No runner/auditor retry.
- Raw result: 1,542,155 bytes, SHA-256 `74dfede0db4676fdaf0d6385c625c2c3731a75ffe8572d7f7a45dbc060e42a22`. Full raw rows, both logs, receipts, container IDs/inspect records and auditor receipt are retained under `formal/allocation-03/`.
- Runner stdout/stderr were combined by the frozen PowerShell `2>&1 | Tee-Object` command; the exact combined streams are retained as `runner.log` and `auditor.log`.

## Results

Wrong emitted dispositions and safe-coverage rates (each block n=960):

| Block | Direct wrong | Typed wrong | Wrong reduction | Direct coverage | Typed coverage | Typed − direct coverage |
|---|---:|---:|---:|---:|---:|---:|
| SINGLE_MISSING | 47 | 53 | −12.8% | 29.896% | 75.208% | +45.312 pp |
| MULTI_MISSING | 36 | 69 | −91.7% | 27.396% | 67.604% | +40.208 pp |
| COMPOSITION_HOLDOUT | 215 | 169 | +21.4% | 73.854% | 66.771% | −7.083 pp |
| COMPLETE | 71 | 30 | +57.7% | 94.583% | 94.479% | −0.104 pp |
| NUISANCE_SHIFT | 108 | 119 | −10.2% | 67.083% | 71.979% | +4.896 pp |

The primary gate requires each partial/compositional block to reduce wrong emissions by at least 25%, without increasing wrong recovery and with no more than 5 pp coverage loss. None qualifies. In COMPOSITION_HOLDOUT, errors fall by 21.4% but coverage falls by 7.083 pp, beyond the frozen tolerance; the other two primary blocks emit more wrong recoveries despite higher coverage. Hence `HOLD_COVERAGE_TRADEOFF`, not a PASS or a reliable generalization claim.

All five noiseless full-observation prototypes were correct and arm-equal; unknown and contradictory controls abstained in both arms; unsafe emissions were zero. Auditor receipt: `pass=true`, rows=4,800, errors empty, 16/16 corruption controls rejected. These validate the retained synthetic artifact only.

## Scope and limits

One finite synthetic seed pair and one authored five-mode/six-cue family; equal inputs do not remove the classifiers' different inductive biases. No real GUI diagnosis, cross-app transfer, runtime integration/authority, safety proof, model quality, task effect, latency/token efficiency, human tempo, or product claim. The result does not replace or pool any #4155/#4169/#4844/#4863/#5184/#5188 evidence or STOP.
