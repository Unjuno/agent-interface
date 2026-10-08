# T5 container successor — terminal disposition

**Overall: `HOLD_AUDIT_ARTIFACT_WRITE_PATH_PREEXISTED`.** The one-shot candidate completed and preserved all four synthetic traces. The independent auditor was invoked once and exited 1 while trying to create its already-existing bind-mounted output directory. The allocation is terminal; no candidate or auditor retry is authorized or claimed.

## Evidence

- Base main: `c4d2d4b1ccf4512ec79af75bd8eaecfcada39947`.
- Candidate image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, Linux/amd64; network disabled, 1 CPU, 512 MiB, pids 64, read-only root and source.
- Frozen T4 candidate and runner blobs matched: `afd5d4ea1bbbede29ecb67ff49f6e944b4d22320` and `f5caf71a743a563b7de046b82d44db7ebe49e829`.
- Construction suite: host 4/4; final container invocation 4/4. Two preceding construction-container commands failed before candidate start (unsupported `unittest discover` invocation and wrong bind source); they are retained in `RUN.json` and were not candidate runs.
- Candidate: exactly 1 invocation, exit 0, retries 0. Four children produced the preregistered matching / wrong-ID / absent / late-exact boundary patterns; all processes were reaped and reader threads joined. Raw output is `results/container-01/`.
- Independent auditor: exactly 1 invocation, exit 1, retries 0. Its `audit()` function returned before the script attempted `Path('/audit').mkdir(..., exist_ok=False)`. That failed because the host had already created the bind target. Consequently no `audit.json` was persisted and the required D gate is not satisfied; do not relabel this as an auditor PASS based only on the candidate receipt or the auditor process reaching the write step.

## Interpretation and limits

The candidate's four synthetic outcomes are consistent with T4's scoped `JsonSession.wait()` ambiguity and the captured timestamps. The overall allocation remains HOLD because the independent audit artifact was not written and its process returned nonzero. This container-transfer attempt does not identify the original #3202/#3211 recovery-arm terminal cause, establish MAP01 behavior, modify production code, or authorize a formal recovery allocation. No GPU/CUDA, model/provider, network, GUI, game, user data, or OS input was used.

Preserve the candidate and the auditor failure unchanged. Any future successful audit must be a newly frozen additive successor allocation, not a retry or repair of this consumed T5.
