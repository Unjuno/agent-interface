# Formal result — Issue #4792

**Decision: `FAIL_BINDING_OR_SAFETY` (frozen decision label).** The independent audit found integrity intact and zero unsafe simulator effects, but the required YIELD/NO_ACTION exactness gates both failed. Do not use or promote this candidate.

## Results

- Candidate exact semantic action/effect: **24/64 (37.5%)**, below 80%; base: **0/64**, so delta +37.5 percentage points.
- YIELD: **0/8** exact (required 8/8); NO_ACTION: **0/8** exact (required 8/8).
- Unsafe bound simulator effects: **0** for both base and candidate.
- Mutation controls rejected: **5/5**.
- Candidate p95: **1,077,806,267 ns** (1.078 s; <=1.2 s gate passes). Base p95: 841,044,542 ns.
- Fit: **2.757 s**, 16 optimizer steps, peak CUDA allocation **2,892,767,232 bytes** (~2.69 GiB); <=300 s / <=12 GiB gates pass.
- Candidate output mean: 17.09 tokens vs base 18.94 tokens.
- Integrity: 64 rows each, reconstructed successfully, no audit errors.

## Interpretation and limits

This is one local synthetic settings benchmark, one 0.5B model, one seed and one laptop GPU. It is not a general capability, latency, real-world agent or production-authority result. The compact boundary achieved zero unsafe effects under the simulator and rejected all five mutation controls, but semantic quality is not useful under the preregistered gates. The model completely missed required abstention classes. No retry, tuning, or second fit was performed. Preserve this failure; any new idea requires a separately preregistered successor experiment.

Both model loads emitted: `Sliding Window Attention is enabled but not implemented for sdpa; unexpected results may be encountered.` This warning is retained as a limitation; frozen sources were not modified.

## Artifacts

- `formal/results/audit.json`: independent CPU audit.
- `formal/results/base-raw.json`, `candidate-raw.json`: per-row raw model outputs and timing.
- `formal/results/fit.json`: fit metrics and adapter hashes.
- `formal/results/adapter_config.json`, `adapter_model.safetensors`: exact fitted LoRA adapter (2,175,168 bytes), retained for reproducibility only; not endorsed.
- `formal/results/EXECUTION.json`: source/data/model/image and result hashes.
