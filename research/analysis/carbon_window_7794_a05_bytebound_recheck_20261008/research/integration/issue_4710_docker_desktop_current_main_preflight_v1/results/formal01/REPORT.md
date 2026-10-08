# Formal 01 result — Issue #4710

## Disposition

`PASS_DOCKER_DESKTOP_CURRENT_MAIN_INSTRUCTIONS_PREFLIGHT_ONLY` for allocation `issue-4710-formal01`. Exactly one host Codex CLI invocation occurred; there were no retries. The independent audit ran in a separate network-disabled Docker Desktop container and passed 45 checks with zero errors. This is only an instructions-forwarding, event-accounting, usage, and compiled-schema plumbing result.

## Frozen identity and environment

- Issue: [#4710](https://github.com/Unjuno/agent-interface/issues/4710); intake source commit: `f5205f532b1f64b71c9a1d69af07e8389f7fd8e0`; study branch is based on the then-current main descendant `a97996b4811219a9ed09b9ad19ea3ee75955f2d0`.
- At readback, the broker, event runner, runner test, schema, and responder-instructions Git blob IDs all matched current main. The archived event fixture used by the construction-only unit test is not present on current main; it was restored as a test-only fixture from the Issue #4710 construction record. It was not used as formal prompt input.
- Docker Desktop context `desktop-linux`; engine `28.5.1 linux/amd64`.
- Preregistered image ID `sha256:7e4a3b6f3917baa9f153b4dfd011a4ea528a3d200a7a3d274aa9479900ee7b41` was absent locally. Before the formal call, the additive amendment in `PRECALL_FREEZE.md` substituted the already-cached, immutable `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9` (Linux/amd64). No image was pulled or built.
- Host CLI: `codex-cli 0.158.0-alpha.2.1`, SHA-256 `8f0554ede25bbc5450921897c468b2e84635aa513c5017457997af0954581f49`; logged into ChatGPT at preflight.
- Container controls observed from `docker inspect`: network `none`, read-only root and source, all capabilities dropped, `no-new-privileges`, 1 CPU, 512 MiB, 64 PIDs; writable bind mounts limited to output and IPC, plus bounded `/tmp` tmpfs. Container and broker exited 0; container cleanup exited 0.

## Formal request and result

One no-image request used the frozen prompt `Schema compatibility probe. Produce any object accepted by the supplied schema.` in an empty scratch working directory, with the main responder instructions and compiled grounding schema. Request, response, broker receipt, and request IDs agree. Authority was false at request, runner, and broker boundaries. The raw event stream contains exactly one completed assistant message and one completed turn, with no tool event. The JSON object passes the supplied schema.

Usage: 10,212 input tokens, 0 cached input, 0 cache-write input, 168 output tokens, 53 reasoning output tokens. The response SHA-256 is recorded in `formal01/event-accounting.json`.

The broker stderr also records a Windows `hot not supported yet for PowerShell` notice and failed initialization of the configured `cloudflare-api` MCP server due to an auth-required handshake. No tool invocation appears in the captured event stream; the one-shot call nevertheless completed successfully and the independent audit passed. This environmental warning is retained verbatim in the broker receipt, not suppressed.

## Preflight stop preserved

The first local pre-call gate stopped because the launcher checked only stdout for the successful `codex login status` text, while this invocation emitted it on stderr. It recorded zero model calls and an empty IPC directory. The evidence remains as `preflight-stop-01.json`. The launcher was corrected to inspect both streams, committed and read back from the frozen branch, and a new isolated pre-call directory then passed. No formal call was made during either preflight.

## Construction controls

Using the exact-byte runner source, the event-accounting suite passed 8/8; independent auditor controls passed 5/5 in Docker Desktop. These were construction-only tests and made no model calls. Two earlier construction STOPs remain preserved in the Issue #4710 history; they are not rewritten as passes.

## Scope and exclusions

This PASS establishes only current-main broker/instructions forwarding and event/schema accounting on Windows Docker Desktop with Linux/amd64. It does not satisfy #3489's distinct OrbStack/Linux/arm64 gate; authorize #3311's six-task allocation; establish task quality, correctness, latency, or efficiency; exercise a screenshot, GUI, input action, fixture task, or submission; or support a product claim. The authenticated MCP startup warning is a retained environment limitation. Any broader test needs its own frozen allocation.
