# LM Studio local vision adapter — construction only

## H / T / D / C / U

**H.** A small standard-library adapter can send an image, bounded intent, and a closed JSON Schema to LM Studio's OpenAI-compatible chat-completions endpoint while retaining the parsed answer, raw response, actual model identifier, and provider-reported token counters. It must fail closed on non-loopback destinations, redirects, incomplete/ambiguous generations, malformed JSON, and malformed counters; absent usage stays unavailable rather than becoming zero.

**T.** One host-only CPython test invocation exercises the adapter against a real local HTTP stub bound to `127.0.0.1`. Ten contract cases cover request payload, closed-schema admission, image encoding, reported/missing usage, remote-destination refusal, redirect refusal, no-retry behavior, malformed output, truncation, and multiple choices. The scope is adapter construction—not model quality or speed.

**D.** `PASS_ADAPTER_CONSTRUCTION_ONLY` requires all ten tests to pass, exactly one request per attempted call, no model/GPU/container invocation, rejection before sending for non-loopback URLs, redirect refusal, and explicit `null` for each unavailable usage field. A test or audit failure is retained as a construction failure; no retry is used to replace a formal model result.

**C.** The HTTP server returns hand-authored complete Chat Completions responses. It does not run LM Studio, load Gemma, test the installed model's vision encoder or constrained decoding, or establish that response counters are accurate for a real inference.

**U.** No model call, task-quality, latency, speed, cost, Astra-comparison, or production-authority claim follows. Formal T0 remains gated on a current-main freeze, a reconciled dataset/model pin, disk and source checks, and a specifically assigned resource window in Issue #5085. Existing #5263/#5300 evidence is read-only input and remains unchanged.

## Contract and intended invocation

`lmstudio_chat.call_local` makes one non-streaming `POST /v1/chat/completions` request to an explicitly supplied loopback URL. The caller supplies the already-frozen image, intent, model identifier, and JSON Schema. The adapter exposes no action tool and does not grant computer-control authority. It uses temperature 0, top-p 1, a 256-token output ceiling, and no retry. The return preserves `raw_response`/`raw_usage`; reported counters are copied verbatim, and absent counters plus local monetary cost are `null`.

The current candidate name seen during prior local inventory was `google/gemma-4-e4b@q4_k_m`; this is only a candidate label, not a verified loaded API identifier or a formal model pin. Before any inference, read the model ID, quantization, digest, LM Studio version, GPU offload/context settings, and resource lease back into a fresh preregistration. Do not load the model on the strength of an idle-GPU snapshot.

The transport shape follows LM Studio's official [OpenAI-compatible image/chat endpoint](https://lmstudio.ai/docs/developer/openai-compat) and [JSON Schema output contract](https://lmstudio.ai/docs/developer/openai-compat/structured-output). For reporting, its documented Chat Completions token counters are used as returned; richer stats from the native API are not imputed into this adapter's format. [LM Studio API endpoint comparison](https://lmstudio.ai/docs/developer/rest) documents the distinct endpoint surfaces.

## Reproduce construction

```powershell
python research/system1/lmstudio_gemma4_adapter_v1/run_construction.py
python research/system1/lmstudio_gemma4_adapter_v1/audit_construction.py
```

The runner refuses to overwrite its first raw output. It starts a loopback-only mock HTTP server through the tests; it does not start the LM Studio server, model, container, or GPU work.
