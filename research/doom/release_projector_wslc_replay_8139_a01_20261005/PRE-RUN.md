## H/T/D/C/U — WSLc replay of #8139 producer-bound projector

- **H:** the #8139 projector accepts actual V12/V4/batch producer rows when every admission has exactly one matching release, rejects duplicate/missing pairs and ambiguous cross-step holds, and rejects each boolean-alias step/ordinal field independently.
- **T:** Freeze the 11-file closure and hashes listed below from PR head `9648fc1dc6f68fa6702afb4d59b3c6cc8377a9e9`. Run both projector test modules (16 expected unit/composition methods) and independently apply four controls to `valid_pair()`: untouched positive; only retry ordinal `1 -> true`; only release identity step `2 -> true`; only release batch step `2 -> true`. One container invocation; retries 0. Image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`; WSLc, network none, CPU 1, read-only bind mount. No GPU, live input, game, or external service.
- **D:** all 16 methods pass; untouched positive is ready with one row; each boolean-only mutation is not ready with zero rows. Any deviation is FAIL; setup failure before tests is STOP. No retry.
- **C:** synthetic Xlib/test fixtures and selected producer closure only. Not Session/V39/game execution, physical release proof, application consumption, useful feedback, recovery, or MAP01 outcome.
- **U:** conclusion limited to these frozen PR blobs, tests, inputs, and pinned image.

PR head `9648fc1dc6f68fa6702afb4d59b3c6cc8377a9e9`; PR-reported base/main `19a6b723e58ccfd2b8265e88659589ef9223fcc9`. The 11 files are the exact `green-v1/sources.json` closure; their frozen SHA-256 values are retained in the shell capture and reported after execution.

## Result

Not run yet.
