# Status addendum — 2026-09-30

Disposition: `HOLD_NO_QUALIFIED_COMPARISON_ROUTE`; zero model calls, zero inference results.

## Why formal T0 did not start

The current #5263 contract asks for a matched `ASTRA_GROUNDING` / local multimodal comparison. This construction proposed a GPT-5.6-Luna Codex CLI route only as a frontier proxy, and it is not the named ASTRA_GROUNDING path. More importantly, `codex exec --help` exposes no control that disables the agent's tools; `--sandbox read-only` limits filesystem writes but does not turn an agent execution into a direct, tools-disabled model inference call. Running that route would not preserve the intended T0 treatment or isolate model output, so it was not called.

The local runtime preflight did succeed in a disposable Docker container: network disabled, read-only root filesystem, model blobs/manifests mounted read-only, and private-key/temp writes isolated to tmpfs. `ollama list` recognized `qwen2.5vl:3b`; `ollama ps` remained empty. Docker Desktop did not publish the container port to the host under `--network none`, so the future local runner must invoke the Ollama API from inside the same container. The preflight container was removed; the user's host Ollama service and model store were untouched.

## Evidence boundary

- The 14-case synthetic corpus, typed schema, separate oracle, preregistration draft, and their 10 construction tests remain useful construction artifacts.
- Host tests: 10/10 passed.
- Docker tests: 10/10 passed in `python:3.13.5-slim-bookworm`, `--network none`, read-only source/root.
- No outputs, accuracy, latency comparison, Needle adaptation, LoRA update, or Astra-free claim were measured.
- Resume only after a direct, tool-free, image-capable Astra/frontier grounding route is made available and frozen, or a distinct successor question is explicitly scoped to an available direct-inference comparator. Do not silently substitute the Codex agent route.
