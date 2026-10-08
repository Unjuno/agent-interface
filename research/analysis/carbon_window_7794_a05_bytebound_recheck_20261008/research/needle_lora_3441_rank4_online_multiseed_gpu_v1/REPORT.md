# GPU rank-4 online LoRA multi-seed result — Issue #3807

## H / T / D / C / U

**H — hypothesis.** Across five fresh seeds, output-LoRA rank 4 would rescue the rank-2 online adaptation quality miss, while retaining base role A, staying within 0.03 of matched rank-4 batch replay, and satisfying route, timing, full-state and audit gates.

**T — allocation.** One formal invocation, allocation `needle-lora-3441-rank4-online-multiseed-gpu-v1`; seeds 3451–3455; local NVIDIA RTX 3080 Laptop GPU, Python 3.11.9, PyTorch 2.5.1+cu121, CUDA 12.1; `CUBLAS_WORKSPACE_CONFIG=:4096:8` set before process startup; deterministic algorithms on, TF32 off. Source was verified against [FREEZE.json](FREEZE.json) immediately before execution. No container or external workflow was used.

**D — decision.** **`FAIL_ONLINE_RANK_CAPACITY_GPU`**. Independently audited results:

| Seed | Base A | Rank-2 online B | Rank-4 online B | Rank-4 batch B |
|---:|---:|---:|---:|---:|
| 3451 | 0.9700 | 0.9414 | 0.0156 | 0.9519 |
| 3452 | 0.9636 | 0.9326 | 0.0149 | 0.9299 |
| 3453 | 0.9578 | 0.9331 | 0.0222 | 0.9534 |
| 3454 | 0.9668 | 0.9583 | 0.0134 | 0.9580 |
| 3455 | 0.9556 | 0.9368 | 0.0193 | 0.9531 |

- Rank-4 online B fails the >=0.90 gate on all five seeds; mean accuracy is 0.0171.
- Rank-2 online mean is 0.9404; rank-4 online minus rank-2 online is -0.9233, missing the required +0.03.
- Rank-4 online is more than 0.03 below rank-4 batch on every seed.
- Rank-4 online feedback p95 is 33.335 ms (passes <=60 ms).
- Route invalidation controls all YIELD; base is immutable; full-state snapshot round-trip and rollback are tensor-exact for all seeds. Integrity audit: true.

**C — constraints and execution.** Five-seed runner returned exit code 0 after one invocation; 0 retries, no post-result tuning. In-memory synthetic data; no provider/network, GUI/input, checkpoint, runtime integration, or action authority. C: had >=1 GiB free immediately before formal execution. No Docker image pull, cleanup or service repair. Exact raw stdout wrapper is retained in [FORMAL_RESULT.json](FORMAL_RESULT.json); independent recomputation is [AUDIT.json](AUDIT.json). Wrapper stdout SHA-256: `abf9a01dd4dc34bc137bf4c25d191372ddceb8c872b3df73a61cdc9c30defc06`; decompressed canonical result SHA-256: `2ae484327db48fd1f428e2f724887edcdc06da771f0df97c5d2cfbda7a7d7bf0`; runner SHA-256: `43e6e6ef39883e78e50c3887b2ddf804a755f0305cad0d9ef6f640b00bdccdff`; auditor SHA-256: `d7f76504328a9492a8fe8f83be773e6b1a5a344e6da7cd0e4bd96192fec8bd7a`.

**U — limits.** Five seeds from one binary-factor synthetic task family only. No real Astra feedback, general skill transfer, GUI/task effect, production safety, crash persistence, concurrent training/inference, or production latency claim. GPU timing is specific to this local hardware/runtime. This FAIL does not justify tuning or retrying the same allocation; any follow-up needs a distinct preregistered hypothesis and successor Issue.

Construction history remains in [PREALLOCATION_STOP.md](PREALLOCATION_STOP.md) and [FREEZE.json](FREEZE.json): an initial syntax check caught a source typo before tests/model execution; corrected construction checks passed 6/6. The earlier storage STOP was pre-allocation only and remains unmodified. A separate CUDA feasibility smoke passed under Issue #3812; it is not pooled with this result.
