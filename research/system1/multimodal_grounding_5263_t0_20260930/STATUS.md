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

## Shared Docker window deviation — append-only correction

The latest #5085 coordination comments, read after the construction work, show an exclusive #5139 Docker/GPU window from 2026-09-30 08:16 through 08:30 UTC. During that window this lane ran the 10-test networkless/read-only Python Docker construction check and briefly started its own uniquely named Ollama preflight container. No formal model inference, model load, CUDA/GPU call, fit, or persistent model-store write occurred. The Ollama container was removed; existing host Ollama was not altered. Nevertheless, these Docker invocations used the shared Docker resource during another lane's exclusive window and were not authorized by that lane's lease. This was a coordination error. Preserve the already-recorded test results as construction observations with this deviation attached; do not treat them as lease-compliant evidence. No further Docker/GPU work for this study until a fresh explicit slot is assigned and the owner confirms release/availability.

## Comparator/tool-isolation correction — 2026-09-30

The earlier statement that Codex CLI had no tool-disabling controls was incorrect. A configuration-only check using `codex features list` verified all 33 flags in `frontier_profile.DISABLED_FEATURES` resolve to `false`; `unified_exec` remains an internal stable feature, while `shell_tool` and `unified_exec_tty` are disabled. The invocation also uses `--ignore-user-config`, `--ignore-rules`, `--ephemeral`, and `--sandbox read-only`. No model call was made by this configuration check.

Current OpenAI documentation includes `gpt-6-astra` in its structured-output example and says the root schema must be an object rather than a top-level union. The comparison candidate is therefore amended, before any inference, from GPT-5.6-Luna to the named `gpt-6-astra` model through a tool-disabled Codex CLI wrapper. This is not the project's separately hosted Astra grounding service; report the exact route and wrapper, not equivalence. `decision.schema.json` is now a single closed root object; conditional cross-field combinations remain enforced by the independent protocol validator. See the [official Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs).

The current formal hold is now resource/provenance only, not absence of a frontier model candidate: the #5139 window was released and the queue subsequently assigned #5134. No Docker/GPU slot is inherited. Before any calls, this amendment, exact source, prompt and model/corpus hashes must be pushed/read back, and a new explicit slot must be assigned for the local-container comparison and audit.
