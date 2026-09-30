# Issue #5198 — allocation -01 plan

Allocation: `typed-mode-4844-risk-calibration-20260928-01`
Branch: `research/typed-mode-4844-risk-calibration-v5-20260928`
Evidence path: `research/experiments/typed_mode_generalization_4844_calibration_v5/`
Main intake: `317071858f3bc9e0d3d90330095b90c9835dc591`

## H — hypothesis

The allocation -04 v4 experiment used the same confidence threshold for two differently factorized classifiers and observed substantial coverage imbalance. If each arm's single global abstention threshold is selected only on a separate calibration sample to target 65% pooled coverage, typed-mode posterior aggregation may reduce wrong emitted dispositions on partial/compositional holdouts at comparable coverage. The advantage may disappear or fail to transfer across blocks.

## T — frozen design

- Reimplement the disclosed five-mode/six-binary-cue simulator and both Bernoulli Naive Bayes arms from the v4 report. Keep alpha 1, prototypes, disposition map `[0,0,1,2,2]`, flip/drop probabilities, and five block definitions unchanged.
- Formal seeds: train 67010231; calibration 67010232; heldout test 67010233. Construction seeds only: 550503/550504/550505. Three formal seeds are disjoint from all v1-v4 registered pairs and from construction seeds. Construction tests must assert this separation and never access a formal seed.
- 2,000 balanced train rows; 4,800 calibration rows and 4,800 heldout test rows, each 960/block and 192/mode/block. Both classifiers use exactly the same generated feature rows.
- Fit each arm once on training rows. On calibration rows, choose one scalar confidence threshold per arm that minimizes absolute distance from 65% pooled coverage. Ties choose greater coverage, then lower threshold. No labels are used to tune model weights or choose the operating point beyond the fixed coverage target. Freeze thresholds before the heldout test metrics are computed.
- Controls: five clean prototypes must produce correct, arm-equal dispositions; all-missing and contradictory controls must abstain in both arms at calibrated thresholds.
- Docker Desktop only: `desktop-linux`, cached image config digest `sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a`, `linux/amd64`; `--pull=never --network none --read-only --cpus=1 --memory=512m --pids-limit=32 --security-opt=no-new-privileges`, read-only source plus fresh output mount. One formal runner then one separate raw-only auditor. No retries, replacements, post-test tuning, GPU/model/provider/GUI/input/network.
- Before the only formal invocation: verify the current branch, clean working tree, exact source Git blobs/hashes, fresh output paths, Docker Desktop context/image/inventory, and rerun seed/path/branch/commit collision searches. Freeze exact commands and source identity. The auditor independently reimplements the data generator, both estimators, threshold selection and heldout score reconstruction, then rejects 16 directed corruptions.

## Exact formal command sequence

Run once from the clean repository root in PowerShell after verifying every path/hash/blob in `FREEZE.json`, the branch, the three formal seeds, current-main/path status, and Docker Desktop context/image/empty inventory. The output root must not already exist and must be outside the repository. Stop before launch if any check differs.

```powershell
$repo = (Resolve-Path .).Path
$src = Join-Path $repo 'research/experiments/typed_mode_generalization_4844_calibration_v5'
$out = 'C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-x20\typed-mode-calibration-v5-formal-01'
if (Test-Path -LiteralPath $out) { throw 'STOP: formal output path already exists' }
New-Item -ItemType Directory -Path (Join-Path $out 'runner'),(Join-Path $out 'auditor') | Out-Null
if ((docker context show) -ne 'desktop-linux') { throw 'STOP: Docker context changed' }
if (docker --context desktop-linux ps -q) { throw 'STOP: Docker Desktop already has a running container' }
if ((docker --context desktop-linux image inspect sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a --format '{{.Id}}') -ne 'sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a') { throw 'STOP: pinned image mismatch' }
docker --context desktop-linux run --cidfile (Join-Path $out 'runner/container.id') --pull=never --network none --read-only --cpus=1 --memory=512m --pids-limit=32 --security-opt=no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=32m --mount "type=bind,source=$src,target=/src,readonly" --mount "type=bind,source=$out\runner,target=/out" -e PYTHONDONTWRITEBYTECODE=1 1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a python /src/experiment.py 2>&1 | Tee-Object -FilePath (Join-Path $out 'runner/runner.log')
$runnerExit = $LASTEXITCODE
if ($runnerExit -ne 0) { throw "STOP: sole formal runner exited $runnerExit; do not retry" }
$raw = Join-Path $out 'runner/result.json'
$rawSha = (Get-FileHash -LiteralPath $raw -Algorithm SHA256).Hash.ToLower()
$runnerId = (Get-Content (Join-Path $out 'runner/container.id') -Raw).Trim()
docker --context desktop-linux inspect $runnerId | Tee-Object -FilePath (Join-Path $out 'runner/container-inspect.json') | Out-Null
docker --context desktop-linux rm $runnerId | Out-Null
if (docker --context desktop-linux ps -q) { throw 'STOP: unexpected running container before audit' }
docker --context desktop-linux run --cidfile (Join-Path $out 'auditor/container.id') --pull=never --network none --read-only --cpus=1 --memory=512m --pids-limit=32 --security-opt=no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=32m --mount "type=bind,source=$src,target=/src,readonly" --mount "type=bind,source=$raw,target=/in/result.json,readonly" --mount "type=bind,source=$out\auditor,target=/audit" -e PYTHONDONTWRITEBYTECODE=1 1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a python /src/audit.py /in/result.json $rawSha 2>&1 | Tee-Object -FilePath (Join-Path $out 'auditor/auditor.log')
$auditExit = $LASTEXITCODE
$auditorId = (Get-Content (Join-Path $out 'auditor/container.id') -Raw).Trim()
docker --context desktop-linux inspect $auditorId | Tee-Object -FilePath (Join-Path $out 'auditor/container-inspect.json') | Out-Null
docker --context desktop-linux rm $auditorId | Out-Null
if ($auditExit -ne 0) { throw "STOP: separate raw-only audit exited $auditExit; do not rerun" }
if (docker --context desktop-linux ps -q) { throw 'STOP: unexpected container remains after audit' }
```

## D — decisions

`PASS_TYPED_MODE_MATCHED_COVERAGE_SCOPED` only if calibration coverage is within 2pp of target for both arms; heldout pooled coverage differs by <=3pp and each of SINGLE_MISSING, MULTI_MISSING and COMPOSITION_HOLDOUT differs by <=5pp; typed has at least 25% fewer wrong emissions in every primary block; all controls pass; and independent audit errors are empty with 16/16 corruptions rejected.

`HOLD_CALIBRATION_COVERAGE_INSTABILITY` if calibration or heldout coverage tolerances fail; report results, but do not claim matched-coverage risk. With matched coverage, a valid miss is `FAIL_TYPED_MODE_NO_SELECTIVE_RISK_ADVANTAGE`. Control failures are `FAIL_CONTROL_OR_INTEGRITY`; source/image/seed/command/auditor provenance failures are `STOP_PROVENANCE_OR_INFRASTRUCTURE`. Never retry.

## C — controls/confounders

All three seed streams are disjoint, and both arms share every row. Calibration and test have the same declared block mixture but are finite samples. A single global threshold may transfer unevenly by block; block-wise coverage gates expose this. This compares one calibrated operating point, not complete risk-coverage curves.

## U — limits

This is a synthetic finite-family selective-risk experiment only. It does not establish real-GUI diagnosis, runtime authority/safety, model quality, task effect, latency/token efficiency, cross-app transfer, human tempo or product readiness. The fixed-threshold v4 result stays distinct and unchanged.
