# JSON structural corruption matrix for the #5139 dataset auditor

Date: 2026-09-29 (Asia/Tokyo)

## H / T / D / C / U

- **H — Hypothesis:** the independent dataset/raw auditor should reject malformed JSON structures with explicit integrity errors, rather than raise a Python exception. Valid positive evidence must continue to pass.
- **T — Test:** candidate branch head `403b04fa95eb6d03cec1505210b72e533b7c175e`, current main `b556c109828e89b3a8e78cb618530a044c97d7d8`; standard-library/host-only, 16 one-variable mutations over support/heldout pool types, rows, labels, states, intents, tasks, IDs and selected supports. Each case used synthetic formal/support sentinels `830513951`/`830513952`; no formal allocation was consumed. The same frozen probe ran before and after repair.
- **D — Data:** pre-fix auditor raised uncaught `TypeError`/`AttributeError` in **13/16** cases; the other three returned integrity errors. After adding JSON-type guards before length, grouping, counting, and set operations, it rejected **16/16**, with zero exceptions. Machine results and per-case serialized-input SHA-256 values are preserved in `pre-fix-result.json` and `post-fix-result.json`. The full package suite, including a regression over all 16 cases and existing clean raw-output controls, passes **32/32**; `git diff --check` passes. A supplemental invocation from repository root failed import-path setup and is preserved in `launcher-stop.json`; the identical probe succeeded from its package directory.
- **C — Conclusion:** the dataset auditor had a broad malformed-structure crash boundary. It now normalizes invalid collection types only for safe validation traversal while recording errors, type-checks class values before hash-based operations, checks row ID/task/state shapes, and avoids hashing invalid identifiers. This is synthetic evidence-adjudication robustness; it does not change the Qwen scientific hypothesis or model outputs.
- **U — Limits:** finite fixed mutation matrix, host Python 3.11.9, no property-based exhaustive fuzzing or deep-recursion/memory-exhaustion test. No model, tokenizer, GPU, CUDA, Docker, GUI, provider, or formal fit was invoked. #5139 still lacks exact GPU/Docker lease in #5085 and its separate provenance gates.

## Reproduction

From the experiment package directory:

```powershell
$env:PYTHONPATH='.'
python evidence/audit-shape-matrix-20260929/probe.py
python -m unittest discover -s . -p 'test_*.py' -q
```
