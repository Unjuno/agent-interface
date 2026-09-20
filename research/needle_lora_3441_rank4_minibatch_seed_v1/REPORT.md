# Issue 3851 sampler-stream comparison — formal STOP

## H / T / D / C / U

**H — hypothesis.** On the original #3807 seeds and data, replacing only rank-4 online minibatch stream seed+35 with the #3826 shared schedule seed+31 rescues held-out B accuracy. The sampler is a candidate explanation, not an asserted cause.

**T — frozen allocation.** Five seeds 3451–3455; exact #3807 CUDA runner data generation, CUDA base training, rank-4 initialization seed+24, feedback row order seed+30, AdamW LR .04, 512 base rows / 400 steps, 16 sequential B rows, 8 updates per arrival, batch size 32. Additive path `research/needle_lora_3441_rank4_minibatch_seed_v1/`; branch `research/needle-lora-rank4-minibatch-seed-3851-20260921`. Frozen runner and auditor hashes are pinned in FREEZE.json.

**D — disposition: `STOP_RUNNER_INDEXING_FAILURE`.** Exactly one formal process invocation; exit code 1. Seed 3451 completed its 400-step CUDA base fit, then failed on the first online feedback update before any adapter optimizer step or held-out evaluation. The frozen feedback order begins with support row 4. The runner builds a one-element `seen` array containing that row's source index (4), then incorrectly indexes the one-element array with `bix=[4,...]` (`ids[bix]`), causing CUDA IndexKernel out-of-bounds. Stdout is exactly 0 bytes (SHA-256 `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`). No quality metric or causal conclusion exists. No retry, source edit, or same-allocation correction was made.

The process wrote a 9,786-byte stderr trace (SHA-256 `C268FFDF6D7AB21C3E5FAE92FC1D93A5C5F7CEA0E399C05A85F483AE49268378`), preserved verbatim in FORMAL_STDERR.txt. Independent metric audit was not run because there is no result payload; AUDIT.json records this explicitly. After process exit the GPU returned to 0% utilization, 0 MiB used, and 16,177 MiB free.

**C — constraints.** Local Windows host, Python 3.11.9 / PyTorch 2.5.1+cu121 / CUDA 12.1, RTX 3080 Laptop GPU; CUBLAS workspace :4096:8, deterministic algorithms enabled, TF32 disabled. The issue specified host CUDA rather than container evidence; no image pull, install, or service repair occurred. Pre-run disk and VRAM gates passed. Construction suite passed 9/9 before the formal invocation.

**U — limits.** No sampler comparison or held-out result was produced. This is a runner STOP only; it neither supports nor refutes the sampler hypothesis, rank-4 adaptation, transfer, runtime safety, or product performance. Preserve this STOP unchanged. Any corrected harness requires a distinct successor allocation and a newly frozen source/gate.

## Raw artifacts

- FORMAL_STDOUT.json: empty file, 0 bytes.
- FORMAL_STDERR.txt: exact stderr captured from the single process.
- FORMAL_METADATA.json and AUDIT.json: process and audit status.
