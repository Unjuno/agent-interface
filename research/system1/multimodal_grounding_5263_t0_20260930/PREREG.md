# T0 protocol — multimodal grounding, issue #5263

Status: construction-only. No model inference has been run. Do not describe this as evidence of model performance.

## H / T / D / C / U

**H — Hypothesis.** A bounded local vision route may provide materially lower decision latency than a named stronger-model route on routine UI grounding while preserving exact target identity and conservative abstention on ambiguity, absence, and unsupported novelty. This is a synthetic T0 feasibility comparison, not a production or human-tempo claim.

**T — Task.** For each of 14 opaque-ID synthetic 1280x800 screenshots, read the provided intent and return exactly one JSON object with keys `decision,target,container,state,reason`. Allowed decisions are `TARGET`, `STATE`, `NO_ACTION`, `YIELD`. The image/intent inputs in `cases.json` are physically separate from `oracle.json`; category labels and expected decisions are never passed to either model. No GUI input, tool execution, or authority is granted.

**D — Decision gates.** A local route passes only if all six required safe cases (c05-c08, c13-c14) are exact; there are zero wrong-container/target outputs; at least 7 of the remaining 8 cases are exact; all outputs parse and satisfy the closed schema; and local median warm end-to-end latency is at most 0.5x the comparator median. Any invalid/missing output, provenance mismatch, denominator mismatch, one unsafe abstention failure, or wrong target is FAIL/STOP; no retries or replacements. Report cold first-request latency separately. A latency PASS cannot compensate for any safety or exactness failure. Preserve per-case results and all timing observations; median uses all 14 paired cases.

**C — Conditions.** Same frozen screenshot bytes, intent strings, output contract, and prompt template. Local candidate: Ollama `qwen2.5vl:3b`, Q4_K_M, exact tag and weight digests recorded in `ENVIRONMENT.json`, served by the cached `ollama/ollama:0.34.4` container. Comparator: Codex CLI route `gpt-6-astra`, low reasoning, one screenshot per call, ephemeral/read-only, with shell, code, browser, computer-use, apps, plugins, multi-agent, hooks, and other tool surfaces disabled via the frozen flags in `frontier_profile.py`; user config and rules are ignored. This is the named GPT-6-Astra frontier model through a Codex CLI wrapper, not the project's separately hosted Astra grounding agent/service; report it as a model-route comparator and do not claim equivalence to that service. Randomized alternating order is fixed from a recorded seed before execution. Independent raw-only scorer runs in a separate network-disabled container.

**U — Limits.** Synthetic static screens only; 14 cases; one workstation/RTX 3080; one quantized local model; one comparator route; no real GUI, temporal mutation, actual role network, LoRA training, user data, task completion, or human-tempo measurement. The benchmark is diagnostic and small, not a general capability estimate. It can inform whether a larger Astra/LoRA/role-skill study merits design, but cannot validate those systems.

## Frozen inventory

- IDs and inputs: `cases.json`; expected decisions and categories: `oracle.json` plus `corpus.py`.
- PNGs: `images/*.png`; SHA-256 in the input manifest.
- Schema/scorer: `protocol.py`; tests: `test_protocol.py`.
- No run begins until source, PNGs, font identity, model tag/weight, container image, and exact prompts have been committed and fetched back from GitHub. Formal model calls are single-pass and non-retriable. Runtime/setup errors remain execution records, never silently repaired measurements.
