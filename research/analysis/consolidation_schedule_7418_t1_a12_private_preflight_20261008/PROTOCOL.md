# Issue #8406 T1 A12 — verified private model preflight

## Rationale and delta

A10's candidate completed but failed the frozen transition auditor, so its answer contrasts remain descriptive. A11 froze a symbolic slot-mapping prompt but stopped before any model calls because its isolated server had no model tag. The error came from invoking `ollama pull` without directing the CLI to the private server; the CLI contacted the default endpoint. A separate preflight has now started the server with the dedicated store, directed the pull to `127.0.0.1:11435`, and verified the API tag, digest-addressed blob, and manifest. A12 uses a fresh allocation and seeds; it does not reuse A10/A11 outputs.

**H.** Explicit symbolic slot mappings that distinguish field labels from field values improve faithful transitions in this fixed synthetic corpus. The operational preflight only establishes model identity and is not evidence for H.

**T.** Four schedules, six prefixes, five fixed queries, seeds 5201/5202/5203; 360 query plus 30 consolidation calls, 390 maximum. Qwen3:8B, frozen digest, Ollama 0.40, private loopback service and store, same decoding as prior allocations (JSON, think=false, temperature 0.2, top-p 0.9, context 8192, query cap128, consolidation cap2048). Run the read-only `preflight.py` first; candidate identity is independently rechecked around every request. No warmup, retries, GUI, user data, or action authority.

**D.** Scoped cadence sensitivity requires a consistent >=0.10 paired contrast across all three seeds and a clean transition/raw audit. Scoped no-material result requires all contrasts within margin and all gates clean. Any failed transition/method gate is `FAIL_METHOD`; otherwise `UNCERTAIN`. No production policy inference.

**C/U.** The fixture and query set are small and synthetic. The result is limited to this corpus, model, and prompt. Transition compliance is necessary before interpreting cadence.

## One-shot boundary

Construction and identity preflight must pass before freeze and formal invocation. Run the candidate once and audit once only if all 390 calls complete. Preserve raw output; do not retry, edit prompts, or pool predecessor outputs.
