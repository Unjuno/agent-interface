# Issue #4728 — local RTX 3080 Docker successor

New physical-host allocation following the preserved ARM64/OrbStack STOP in #4719 / PR #4722. No predecessor record is changed.

## H/T/D/C/U

- **H:** With the exact cached Qwen2.5-VL 3B Q4_K_M model in the pinned Ollama Linux/amd64 container on Docker Desktop, prove nonzero RTX 3080 offload and achieve at least 5/6 one-target synthetic Apply boxes at IoU >= 0.5, with 2/2 absent-target abstentions.
- **T:** Freeze and publish source hashes, generate/hash eight 1280x800 synthetic cases plus one off-center construction case, and publish/read back PREFORMAL before any inference. Use a separate internal Docker network, read-only model and source mounts, helper without GPU, one construction call, then (only after GPU placement proof) one eight-call block, no retries. Capture raw requests/responses, images, GPU/ollama placement samples, container logs, identities and commands; independently audit from raw evidence.
- **D:** `PASS_DIAGNOSTIC_SCOPED` requires all eight bound inputs, every call interval with a positive GPU/offload sample above the empty-server VRAM baseline, >=5/6 hits, 2/2 abstentions and zero audit errors. Confirmed GPU with a missed answer gate is `FAIL_EASY_LAYOUT_CAPABILITY_NOT_ESTABLISHED`; missing GPU is STOP; integrity/audit issue is HOLD.
- **C:** New PC/runtime and fresh synthetic layouts; no causal GPU-vs-CPU or visual-encoding claim. One quantized model, one PC, eight formal rows.
- **U:** No real-application transfer, safety/calibration, click authority, model training, general runtime or product-readiness claim. Keep #570 and #4719 open.

## Frozen local runtime

- Ollama image ID: `sha256:8262851b2846b87c649eddf3e76beb270c52f4d1bc94559f47efde16b0841551` (`linux/amd64`, Ollama 0.34.4).
- Helper image ID: `sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261` (`linux/amd64`, PyTorch 2.5.1+cu121, Pillow 10.2.0, requests 2.32.3; helper has no GPU).
- Model: `qwen2.5vl:3b`, Q4_K_M, API digest `fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1`; model layer SHA-256 `e9758e589d443f653821b7be9bb9092c1bf7434522b70ec6e83591b1320fdb4d`, 3,200,614,720 bytes.
- Host font for deterministic synthetic text: Windows Arial, SHA-256 `b3658eadae55e682b5f69eb64c439c1ecc8f196c0bb8d4756d145d13bc86476a`.

## Reproduction on the allocated PC

Requires the exact images and local model already present; do not pull, download or contact a provider. Use the published `FREEZE.json`, `PREFORMAL.json`, `launch.py`, `prepare.py`, `model_runner.py`, `sampler.py`, and `audit.py`. First run `prepare.py` in the pinned helper with `/data` output and the frozen Arial font bind-mounted read-only; publish and read back its PREFORMAL plus the screen bundle. Only then run `launch.py` once. It refuses occupied R4 names, validates frozen source hashes and cached model digest, creates an internal-only network and a unique Ollama service with no host port, records empty-server GPU baseline, samples `nvidia-smi`/`ollama ps` during each request and skips the formal block unless the single construction request proves placement. It stops only the uniquely named R4 Ollama container it created. Run `python -m unittest -v test_audit.py` before the freeze and `python audit.py --root <evidence-dir>` after the run.

The raw user-profile model path is local-only and omitted from the published command template. Local evidence remains under `work/visual_encoding_570_gpu_local_successor_v1/`; the repository path is `research/analysis/visual_encoding_570_gpu_local_successor_v1/`.

