# Issue #3850 — bounded validation detail, Obstac rung 1

## H / T / D / C / U

**H** — At the exact PR head `b545e6cfbe216d241154254fc58a028ed7754f3c`, the public CLI dispatch facade adds bounded static diagnostics for the two observed malformed `observe` shapes while preserving `INVALID_PROGRAM`, zero backend emissions, and one dispatch. A valid-program refusal is not misdiagnosed, and an unsupported caller-controlled operation string is not echoed.

**T** — Four deterministic facade rows: `region` instead of x/y/w/h; width/height instead of w/h; a valid program with a mocked `INVALID_PROGRAM` backend refusal; and an unsupported op with a 2000-character caller string. Each row calls `dispatch` once, uses fixed observation/binding values, a mocked backend/session, and no capture directory. Retain exact input, returned row, dispatch/close counts and emission counter. No model, GUI, display, native input, network request, or lease grant.

**D** — PASS only if both malformed rows return `refused/INVALID_PROGRAM`, zero backend emissions, `detail_source=program_validation`, and the exact expected field diagnostic; the valid-program control remains without `detail`; the unsupported op returns only `unsupported operation` and does not echo caller text; all rows dispatch/close exactly once and leave input objects unchanged. Any deterministic mismatch is FAIL. Provenance, image, mount or runner mismatch is STOP before rows.

**C** — Source base main `51cc5f964bb36677ad6f9192ddd75d03ca7343c7`; exact candidate PR head `4d51fccac55433570bc714cfaf21c88531fe325d` (merges predecessor candidate `b545e6cfbe216d241154254fc58a028ed7754f3c` with the updated main); runtime subtree `7fae16c1766a36376d6c49f49a7fb0e68f93cb0d`. The selected runtime subtree is byte-identical to the predecessor candidate tree; selected transitive runtime source is retained under `source/` and verified against GitHub tree/blob SHAs and SHA-256. OrbStack context, `linux/arm64`, pinned `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; `--network none`, read-only root and source, dedicated writable output only. Runner checks `OBSTAC_SOURCE_COMMIT`, `OBSTAC_IMAGE_ID`, and `OBSTAC_FREEZE_SHA256` against its frozen constants and recomputes the source closure before producing rows. Independent auditor runs separately with network disabled and source/raw read-only.

## U — limits

This is one deterministic facade-contract experiment only. It does not exercise the public executable end-to-end with a native backend, prove general backend refusal attribution, expose operation indices, measure model recovery calls/time, establish user benefit, or close Issue #3850. Earlier local CLI and Linux/amd64 suite results on the PR are construction/test evidence, not this Obstac result.

## Immutable predecessor boundary

PR #3853 and its tests are read-only inputs. The experiment record will be added at `research/experiments/issue_3850_static_validation_obstac_v1/` on a new additive branch after the bundle is frozen. No predecessor bytes are edited.
