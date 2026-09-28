# Repair-control probe (nonformal)

## H / T / D / C / U

**H.** Deriving each dataset row's class from its frozen intent should reject a class-label corruption that the unmodified PR #5208 auditor accepted.

**T.** CPython 3.11.9 ran the repair probe against the GitHub-read-back evidence bundle from source commit 20715c0dee3064f22e47c3d26f545697cfb2c6bf. The same mutated dataset SHA-256 was 8058606289bbeb9cf31b7e5fb8082690dbc6c6bfab2e2a35e7d9be1e44ee776c; no new dataset/model allocation was used.

**D.** The proposed independent class-from-intent check rejected the fixture: integrity_pass=false, with 24 class mismatches (8 support-pool, 16 held-out-pool). Machine output and exact executed repair_probe.py are alongside this report.

**C.** Host-only source-level repair control. No model, tokenizer, GPU, CUDA, Docker, OrbStack, GUI, or formal allocation. The changed auditor is a local diagnostic copy only; PR #5208 source remains untouched.

**U.** This shows the proposed guard rejects this specific synthetic label-swap mutation. It does not prove acceptance of every clean dataset or any Qwen/LoRA/live-task quality.