# Freeze — #4817 construction diagnosis

Allocation: `tiny-visual-equivariant-diagnosis-2564-20260927-01`
Issue: https://github.com/Unjuno/agent-interface/issues/4817
Intake main: bbb889f9cabfffd3bd260dd5da9c27f8c27a04b8
Dedicated branch: research/tiny-visual-equivariant-diagnosis-2564-20260927
Additive path: research/analysis/tiny_visual_equivariant_diagnosis_2564_v1/
Construction seed: 8964300 (the only data seed; never a formal seed)
Formal fitting: prohibited in this allocation.

## H/T/D/C/U

**H.** #4814's CNN non-acceptance is optimization-limited; longer construction-only optimization may reach train and fixed-base competence. Alternative: shared local convolution plus global max pooling cannot separate the target and distractor geometry, so added steps do not fix the design.

**T.** One offline Docker construction using only seed 8964300. First check all 45 CNN scalar gradients by central finite differences on a deterministic smooth probe point. Then fit the paired MLP control once at 250 steps / 0.8 and fit the CNN from the same construction initialization under this predeclared schedule: (250,0.8), (1000,0.8), (4000,0.8), (1000,0.2), (4000,0.2). Record complete train, base-center, and eight held-out-center probability rows; held-out data are descriptive only and MUST NOT select a schedule. Construction time cap 240 seconds; no tuning beyond the listed schedule, retries, or formal fit.

**D.** Gradient gate passes only if all 45 central-difference comparisons are finite and max absolute error <= 0.01 (epsilon 0.002; smooth check point uses CNN biases offset to 0.25; every parameter scalar is perturbed). Construction competence requires one listed CNN schedule to reach >=95% positive ACCEPT and 0 negative ACCEPT on both training and base evaluation rows. If gradients pass but no schedule reaches those train/base gates within 240 seconds, record `STOP_CONSTRUCTION_COMPETENCE_NOT_REACHED`; if both pass, record `PASS_DIAGNOSTIC_CONSTRUCTION_ONLY` and do not start a formal experiment. Gradient failure is `STOP_FINITE_DIFFERENCE_GRADIENT`. These are diagnostic dispositions, not model efficacy decisions.

**C.** Paired MLP holds fixed seed, examples, optimizer and step schedule. CNN training rows use five positive support centers; negative rows are the same fixed distractor geometry. Construction schedule changes only step count and learning rate. Synthetic binary patches, one seed, and fixed ACCEPT threshold are not natural visual data or calibrated probabilities.

**U.** No efficacy/generalization conclusion, formal confirmation, real frames, GUI, runtime, product, or model promotion. A separate formal allocation requires a revised committed protocol and distinct seeds via a successor Issue. #4814 evidence remains immutable.

## Frozen sources and execution

The `models.py` and `prepare.py` contents come from the audited #4814 branch; only terminal line endings are normalized. The exact local bytes used by Docker are pinned in `source_sha256.json`. Pinned image: `codex-gtk-model:local`, image ID `sha256:ba509e8a38d311c07539c49a7a2970b6f19869de42b8008be07a85568e2c9824`, linux/amd64, Python 3.11.2, NumPy 1.24.2. Use `--pull=never --network none --read-only --cpus=1 --memory=2g --pids-limit=64`, no GPU, no package installation. Source mount is read-only and only the unique output directory writable. One producer and one independent raw-only auditor invocation. No CI/workflow scientific runs.

Frozen source SHA-256 values are in `source_sha256.json`; both producer and independent auditor will verify them. Commands (PowerShell from workspace root; output directory must be created fresh and empty):

```powershell
docker run --rm --pull=never --network none --read-only --cpus=1 --memory=2g --pids-limit=64 -e OPENBLAS_NUM_THREADS=1 -v "${PWD}/work/issue-4817-tiny-cnn-diagnosis-20260927:/src:ro" -v "${PWD}/work/issue-4817-tiny-cnn-diagnosis-20260927/run-output/construction01:/out:rw" -w /src --entrypoint /usr/bin/python3 codex-gtk-model:local /src/diagnose.py --out /out
docker run --rm --pull=never --network none --read-only --cpus=1 --memory=2g --pids-limit=64 -e OPENBLAS_NUM_THREADS=1 -v "${PWD}/work/issue-4817-tiny-cnn-diagnosis-20260927:/src:ro" -v "${PWD}/work/issue-4817-tiny-cnn-diagnosis-20260927/run-output/construction01:/out:rw" -w /src --entrypoint /usr/bin/python3 codex-gtk-model:local /src/audit.py --root /out --source /src --expected /src/source_sha256.json --out /out/audit.json
```
