# Issue #59 — local WSL CUDA/model-route smoke (2026-10-03)

## Scope and classification

Exploratory setup/readiness smoke prompted by the user's direct instruction to use the idle local GPU. This was **not** the preregistered #59 R134 game allocation, not a formal candidate/auditor run, and not a retry of any consumed allocation. It does not satisfy the live-threat-control or MAP01 gate.

- **H:** A temporary Arch WSL Ollama server, pointed at the existing Windows Ollama model store, can load a local model and dispatch inference to the RTX 3080 without downloading a model or changing persistent service configuration.
- **T:** One `qwen3:4b` generation request, with a 32-token cap, against a temporary Ollama listener on WSL loopback port 11435.
- **D:** GPU-route PASS requires Ollama to identify CUDA0/RTX 3080 and offload model layers; response-contract PASS requires the exact requested sentinel. Report the two outcomes separately. No retry.
- **C:** Ollama 0.35.0 in Arch WSL2; existing model store `/mnt/c/Users/junny/.ollama/models`; model `qwen3:4b`, GGUF Q4_K_M, 4.0B, digest `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`; prompt: `Reply with exactly LOCAL_WSL_GPU_SMOKE_OK and nothing else.`; `num_predict=32`, `keep_alive=0`, `stream=false`. Temporary server bound only to `127.0.0.1:11435`; no WSLc container or network change.
- **U:** Local text-generation route and CUDA dispatch only. No game, visual observation, controller, task effect, latency comparison, reliability, safety, or product claim.

This smoke was exploratory rather than preregistered. These H/T/D/C/U labels document its observed scope and must not be represented as a prospective freeze.

## First outcome (preserved; no retry)

**GPU route: PASS.** The model loaded from the existing Windows store and Ollama's raw server log reports CUDA compute on the NVIDIA GeForce RTX 3080 Laptop GPU, `using device CUDA0`, and `offloaded 37/37 layers to GPU` (CUDA model buffer 2375.91 MiB; KV cache 576.00 MiB). During the request, the Windows GPU sample reached 92% utilization; before the request it was 0% / 11 MiB, and after the temporary server exited it returned to 0% / 11 MiB. This demonstrates an actual short GPU workload, not merely CUDA visibility.

**Response contract: FAIL.** The API completed (`done=true`, `done_reason=length`) but returned an empty `response`; all 32 generated tokens were consumed by Qwen3's `thinking` field. The expected sentinel was not produced. This first outcome is retained unchanged and was not retried or tuned.

Captured API result fields: `total_duration=23,400,037,522 ns`, `load_duration=22,870,604,139 ns`, `prompt_eval_count=25`, `prompt_eval_duration=79,501,000 ns`, `eval_count=32`, `eval_duration=445,316,000 ns`. These are one-shot setup observations, not a benchmark.

The full temporary server log was SHA-256 `e402d703e5f95a88b1dd2f3e5bd2e28d394fc6fcb12131056471615da468b5c0` (31,264 bytes at `/tmp/ollama-gpu-smoke-20261003.log` on the WSL distro). The log itself remained in the ephemeral WSL `/tmp` and is not included here; therefore the checksum is a contemporaneous integrity identifier, **not independently re-verifiable from this commit**. The key CUDA lines and complete summary above were captured in the task transcript. No raw game or task evidence was produced.

The temporary server process was stopped by the bounded command's exit trap; a follow-up check found no listener on port 11435, GPU 0% / 11 MiB, while the pre-existing system Ollama service remained untouched. No model was downloaded and no persistent configuration was changed.

This record is based on current main `b521912b9da1fa292f2e4fed1f1ae695c4a7658e`; the experiment itself used only the local Ollama/model-store/runtime identities listed above.
