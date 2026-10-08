# Issue #4837 — extent-aware readout construction

Disposition: **STOP_NO_CONSTRUCTION_COMPETENCE**. The frozen two-arm construction ran locally in Docker, but neither arm learned the task; the hypothesis did not pass its pre-registered competence gates.

## Frozen question and allocation

This is a separate cached-environment successor to #4828's pre-fit NumPy environment STOP. It regenerated the balanced synthetic 30x40 fixture with 9x9 positives and a centered 5x5 negative distractor (data seed 89100471), and compared a shared 4-channel 3x3 CNN with max-only readout against the same convolution plus max-and-spatial-mean readout. Both arms used initialization seed 89100472, 1,000 full-batch SGD updates, learning rate 0.2, and threshold 0.75. Two construction fits; zero formal fits. No tuning or retries of the fit.

Cached image ID: `sha256:e4cf185ef1d8d148f257f52091777952e707dd4f296feb30b20f1d7e03410724` (`linux/amd64`, Python 3.12.14, NumPy 2.5.3, OpenBLAS 0.3.34.106.0). This differs from #4828's frozen but deficient image and is not represented as an exact replication. Docker used `--pull never`, `--network none`, `--read-only`, read-only source mount, one CPU, 2 GiB memory, 64 PIDs, and no GPU; BLAS thread counts were pinned to one.

## Validation and execution

The first diagnostic version tested central differences at the prescribed initialization, where zero mean-branch weights and tied zero max pools make centered finite differences non-smooth. No optimizer update occurred. The test was corrected to use a separate smooth float64 probe (seed 89100473) without changing training initialization or training source. In the pinned container, all 49 scalar derivatives passed with maximum symmetric relative error `3.725338356451932e-05`; optimizer updates in the diagnostic: 0.

The producer then ran exactly two fits (max-only: 11.5299 s; max+mean: 13.4493 s) and retained `RAW.json`, `INPUTS.npz`, `INITIAL_WEIGHTS.npz`, and `WEIGHTS.npz`. The original independent-auditor source encountered a NumPy 2 scalar-conversion incompatibility before producing an audit. No fit was repeated. A separate NumPy-2-compatible raw-only auditor was added; the frozen auditor source recorded by the producer remains unchanged and is included in its source-hash checks. The independent auditor reconstructed saved logits from raw inputs and weights with `integrity_pass=true`, `errors=[]`. All eight mutation controls were rejected after adding missing seed and nonnegative-fit-time checks.

## Results

| Gate | Max-only control | Max + spatial mean | Required for candidate |
|---|---:|---:|---:|
| Train accuracy | 52.5% | 50.0% | >=95% |
| Same-location base accuracy | 52.5% | 50.0% | >=95% |
| Mean held-location positive accept | 0.0% | 0.0% | >=90% |
| Mean held-location negative false accept | 0.0% | 0.0% | <=1% |

The candidate therefore receives `STOP_NO_CONSTRUCTION_COMPETENCE`. Its conservative false-accept rate does not compensate for accepting none of the positives. The max-only control is also at chance and has 0% held-positive acceptance, so there is no evidence of separation favoring max+mean. This one-seed construction does not decide multi-seed efficacy or justify model adoption.

## Retained evidence

Raw producer data, binary arrays and weights remain locally retained under `outputs/tiny_visual_extent_4837_v2/construction-01/`. Their SHA-256 values, plus source hashes and Docker recipe, are recorded in `MANIFEST.json`. Text evidence (`RAW.json`, `AUDIT.json`, and `CONTROL_RESULTS.json`) is also committed beside this report. `audit_numpy2.py` and `controls_numpy2.py` are supplemental auditors, not part of the trained model or the producer's frozen source set.

## Limits and next step

This synthetic single-seed construction cannot establish transfer or live-agent utility. Preserve #4817 and #4828 unchanged. A new seed or hyperparameter/architecture exploration needs a new issue and allocation; no formal successor is warranted from this competence miss without a separately justified new hypothesis.
