# Read-only preflight command record

All commands below were read-only inventory/hash probes. No `docker run`, training command, optimizer, checkpoint load, model download, or container mutation was executed.

| Check | Command / observation | Result |
|---|---|---|
| GPU | `nvidia-smi --query-gpu=name,memory.total,memory.free,utilization.gpu,driver_version --format=csv,noheader` | `NVIDIA GeForce RTX 3080 Laptop GPU, 16384 MiB, 16177 MiB, 0 %, 581.57` |
| Exact training image | `docker image inspect cactus-needle3-train:4205-v1 --format '{{.Id}} {{.Os}}/{{.Architecture}} size={{.Size}} entrypoint={{json .Config.Entrypoint}}'` | `sha256:69f3c6830fda67fc5e8d3f6d8c09bbf730dffca043e3dfb70e433c84bc9db2a5 linux/amd64 size=16680334553 entrypoint=["python","runner.py"]` |
| Frozen base image | `docker image inspect cactus-needle3-action:v1-frozen --format '{{.Id}} {{.Os}}/{{.Architecture}} size={{.Size}}'` | `sha256:268ca519beed0aa750ef44c8cbc47e66dcf824b885591f905009127233bb5151 linux/amd64 size=222946863` |
| Exact frozen checkpoint | Check expected Hugging Face snapshot path and `rg --files` only under the local `models--Cactus-Compute--needle3` cache | `needle3.safetensors` (expected SHA-256 `c234c70dccc7a9115e7c41ac2e41d3655fea3b85c245dd898b46179fb90c6c0c`, 242047978 bytes) absent |
| Confounding cached artifact | `Get-FileHash ...\needle3.cact -Algorithm SHA256` | Present, 35335380 bytes, SHA-256 `c9d915eca282ed42d1a09b143b592adb4cc6744ffe2d294adf5cfc5548170c38`; different artifact and identity |
| Image build inputs | Read-only review of frozen `Dockerfile.train` | Copies only the wheelhouse over `cactus-needle3-action:v1-frozen`; no checkpoint is embedded |

No outputs from the existing R3 Ollama container were used as model/checkpoint evidence. That container was left untouched.

