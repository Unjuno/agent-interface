# Fixed half-LR rank-4 online LoRA — formal result (#3826)

## H / T / D / C / U

**H — hypothesis.** On five fresh seeds, halving only rank-4 online adapter LR from .04 to .02 would materially rescue online B quality while retaining A/rank-2 quality, matching rank-4 batch, and satisfying route, full-state, curve-audit and latency gates.

**T — frozen allocation.** Allocation `needle-lora-rank4-online-lr-half-multiseed-v1`; seeds 3461–3465; local RTX 3080 Laptop GPU, Python 3.11.9 / PyTorch 2.5.1+cu121 / CUDA 12.1. `CUBLAS_WORKSPACE_CONFIG=:4096:8` was set before Python startup; deterministic algorithms on, TF32 off. Runner/auditor/test hashes are in [FREEZE.json](FREEZE.json), verified by GitHub readback immediately before the one formal invocation.

**D — decision.** **`FAIL_LR_HALF_RESCUE`**. Independent auditor regenerated held-out labels from each seed and recomputed all final rows plus 983,040 retained online-curve predictions (5 seeds × 3 online arms × 16 arrivals × 4,096 rows). Integrity was true.

| Seed | Base A | Rank-2 online .04 | Rank-4 online .04 | Rank-4 online .02 | Rank-4 batch .04 |
|---:|---:|---:|---:|---:|---:|
| 3461 | 0.9578 | 0.9260 | 0.9265 | 0.9282 | 0.9419 |
| 3462 | 0.9680 | 0.8479 | 0.8799 | 0.8914 | 0.9067 |
| 3463 | 0.9707 | 0.2927 | 0.9150 | 0.8828 | 0.9365 |
| 3464 | 0.9763 | 0.9160 | 0.9172 | 0.8782 | 0.8850 |
| 3465 | 0.9717 | 0.7886 | 0.7942 | 0.9077 | 0.9246 |

- Rank-4 online LR .02 misses the >=0.90 gate on seeds 3462, 3463, and 3464.
- Its mean advantage over paired LR .04 is **+0.0111**, far below the required +0.50.
- LR .02 differs from matched rank-4 batch by >0.03 on seed 3463 (absolute gap 0.0537).
- Intervention per-feedback p95 is **9.9964 ms** (passes <=60 ms).
- All invalid/missing/stale route controls YIELD; both LR arms began tensor-identically; full intervention state round-trip/rollback and immutable-base gates pass.
- Across all seeds, mean accuracy over arrival counts 1–16 rises 0.0151→0.8977 for LR .02, 0.0160→0.8866 for LR .04, and 0.0159→0.7542 for rank-2 .04. The trajectory is retained per seed and per row; no post-hoc tuning or cause claim is made.

**C — constraints and execution.** One formal five-seed runner process, exit 0; 0 retries, 0 tuning. C: free immediately before run: 490,279,256,064 bytes; GPU free VRAM: 16,177 MiB. Docker Linux engine was available, but no compatible CUDA-PyTorch image was cached; no image was pulled. Execution used the installed local CUDA host, not a container. Synthetic in-memory data only; no provider/network, GUI/input, local checkpoints, runtime integration, or action authority. Exact stdout wrapper is in [FORMAL_RESULT.json](FORMAL_RESULT.json); independent output is [AUDIT.json](AUDIT.json). Wrapper SHA-256: `E64D1E35CC47C6CF504E17DEAF32D7E439F3221B98ECFD628D9352747EC36192`; canonical payload SHA-256: `489ea0eea27abd2c6e1345c49071ed920ad1e7dc81ee8dd80480c501c53c09be`.

**U — limits.** Five seeds in one synthetic binary-factor task family only. No real Astra feedback, general skill transfer, task/GUI effect, production safety, concurrent learning/inference, crash persistence, or production-latency claim. The result rejects this frozen half-LR rescue gate; it does not identify why LR=.04 behaved differently across the earlier and fresh seed sets and does not authorize runtime updates.

Source freeze and gates: [FREEZE.json](FREEZE.json). Construction-only checks passed 9/9; no training occurred before this single allocation.
