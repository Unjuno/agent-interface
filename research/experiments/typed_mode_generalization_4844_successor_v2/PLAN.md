# Issue #5184 — prospective replication plan

Allocation: `typed-mode-4844-successor-20260928-02`
Branch: `research/typed-mode-4844-successor-v2-20260928`
Evidence path: `research/experiments/typed_mode_generalization_4844_successor_v2/`
Intake main: `6df1e32308f1f0854e19ba0cdbf022833441f54f`

## H — hypothesis

For the same synthetic five-mode/six-binary-cue family, predicting a latent mode and aggregating its posterior through the fixed safe-disposition map may reduce wrong emitted recovery on partially observed and compositional holdouts relative to direct recovery classification. It may instead fail to improve or trade away too much coverage. No direction is assumed.

## T — frozen experiment

- Reimplement the disclosed family independently in this v2 directory; do not execute or modify predecessor artifacts. Five prototypes and map `[0,0,1,2,2]`; standard-library Bernoulli Naive Bayes, Laplace alpha 1; both arms receive identical generated rows, features, and training data. Direct predicts three dispositions; typed predicts five modes and sums their posterior by disposition. Emit only at confidence >=0.65; ties are stable by lower class index.
- Training: fresh seed 484421, 2,000 balanced rows (400/mode). Heldout: fresh seed 484422, 4,800 rows (960/block; 192/mode/block). Per-cue flip probability .08. Random missingness .20 except COMPLETE; SINGLE_MISSING forces cue index 1 missing; MULTI_MISSING forces indices 1 and 4 missing; COMPOSITION_HOLDOUT inverts prototype cues 0 and 5 before noise; NUISANCE_SHIFT inverts cue 3 before noise. Row ordering, generator and all outputs are frozen by the committed source.
- Controls: five noiseless full-observation prototypes; all-missing unknown; frozen contradictory vector `[0,0,0,1,0,1]`. Control vector inherited from the disclosed predecessor; no test-label or formal-output selection.
- Construction uses only disjoint seeds 59001/59002. The construction test checks deterministic byte output, row/block/mode balance, and labels. Formal seeds must not be used in construction or preview. Freeze source, tests, auditor, gates, exact Git blobs, SHA-256, image and commands on the additive branch before formal data generation.
- Docker Desktop only; cached image config digest `sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a`, `linux/amd64`; `--pull=never --network none --read-only --cpus=1 --memory=512m --pids-limit=32`; source read-only and fresh output-only writable mount. One runner container, then one separate auditor container with raw read-only and distinct audit output. No GPU, model/provider, GUI, OS input, network, retry, replacement, pooling or post-result tuning.

## D — frozen decisions

- `PASS_TYPED_MODE_GENERALIZATION_SCOPED`: each of SINGLE_MISSING, MULTI_MISSING, and COMPOSITION_HOLDOUT has >=25% relative reduction in wrong emitted dispositions, no increase in wrong recovery, and <=0.05 absolute safe-coverage loss; all five full-observation prototype controls are correct and arm-equal; unknown and contradictory controls abstain in both arms; zero unsafe emissions; raw-only auditor errors empty and all 16 directed corruption controls rejected.
- `FAIL_MODE_MISROUTES_RECOVERY`: integrity-valid unsafe emission or failure of a frozen prototype/unknown/contradictory control.
- `HOLD_COVERAGE_TRADEOFF`: apparent primary-block error reduction requires >0.05 absolute coverage loss.
- `FAIL_DIAGNOSIS_STILL_REDUNDANT`: integrity-valid data, but no primary block qualifies and no coverage tradeoff is the limiting condition.
- `HOLD_MIXED_PARTIAL_RESULT`: valid but mixed/insufficient primary effects not classified above.
- `STOP_PROVENANCE_OR_AUDIT`: source/image/invocation/evidence/auditor provenance failure; this does not adjudicate the scientific hypothesis and is not retried.

Wrong emitted recovery means an emitted disposition unequal to the row's mapped truth; conservative YIELD is not counted as a wrong recovery. Safe coverage is the fraction of rows with an emitted disposition. Relative reduction is undefined as an improvement when direct wrong count is zero; that block cannot pass the >=25% reduction gate.

## C — controls/confounders

The two arms share exact rows and information, but have different inductive biases. Authored prototypes and a finite seed pair constrain generality. The row generator uses deterministic Python `random.Random`; exact source bytes and result bytes are bound to Git and SHA-256. The independent auditor separately regenerates data, fits both estimators, reconstructs predictions/metrics/controls, and mutates raw evidence in 16 fixed ways.

## U — scope

Synthetic fault family and classifier factorization only. No real GUI diagnosis, cross-app transfer, runtime integration/authority, safety proof, model quality, latency/token efficiency, human tempo or product claim.

## Exact formal commands

From PowerShell, with empty fresh `formal-01` and `audit-01` output directories and Docker context `desktop-linux`:

```powershell
$src = (Resolve-Path .).Path
$out = (Resolve-Path .\formal-01).Path
$auditOut = (Resolve-Path .\audit-01).Path
docker run --rm --pull=never --network none --read-only --cpus=1 --memory=512m --pids-limit=32 --mount "type=bind,source=$src,target=/src,readonly" --mount "type=bind,source=$out,target=/out" -e OUT_DIR=/out -e PYTHONDONTWRITEBYTECODE=1 1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a python /src/experiment.py
$digest = (Get-FileHash .\formal-01\result.json -Algorithm SHA256).Hash.ToLower()
docker run --rm --pull=never --network none --read-only --cpus=1 --memory=512m --pids-limit=32 --mount "type=bind,source=$src,target=/src,readonly" --mount "type=bind,source=$out,target=/in,readonly" --mount "type=bind,source=$auditOut,target=/audit" -e PYTHONDONTWRITEBYTECODE=1 1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a python /src/audit.py /in/result.json $digest
```

Record exact commands, Docker context/version/image inspection, container IDs/config, stdout/stderr/exit codes, raw SHA-256/size and audit receipt. Stop before runner if current context, image, source blobs, or output emptiness differs. Never rerun the formal allocation.
