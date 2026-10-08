# Source-locator qualification for the retained T3 audit

This additive preservation note clarifies an input locator; it does not change the frozen report, raw output, or scientific disposition.

## Verified identities

- `RESULT.md` and Issue #6290 record `3d6ffc76d535309cf3820ed33cb9327354f03648` as the immutable input commit. That SHA is the frozen base recorded for the predecessor allocation. The referenced `research/analysis/semantic_serializability_5318_t0_v1/results/formal-01/RAW.jsonl` path is absent at that commit (GitHub contents API returned 404 during read-only review).
- The exact raw bytes are retained at predecessor PR #5952 head [`d356ed65ff9d16978caea56c1ddaf4008a7d171a`](https://github.com/Unjuno/agent-interface/blob/d356ed65ff9d16978caea56c1ddaf4008a7d171a/research/analysis/semantic_serializability_5318_t0_v1/results/formal-01/RAW.jsonl), Git blob `2725e3be1de2805787f1b384d1051111a69c9c91`.
- Independent byte hashing of that blob returned SHA-256 `26fa7c694fd0f3a35bc5085b6145af639e88c8dd79666c3284db12f11df9ed90`, exactly matching the frozen expected digest and the retained T3 output.
- The auditor at [`4acf5905222453b1b65990de3260382dd90eba22`](https://github.com/Unjuno/agent-interface/blob/4acf5905222453b1b65990de3260382dd90eba22/research/analysis/semantic_serializability_5318_audit_t1_v1/audit.py) independently hashes to `479e1a365c94f6fd36963f2afcc633b9c26d9fc18b39f4183ee7a6b51817cda6`, matching the recorded source identity.
- This directory's unchanged `audit-output.json` is Git blob `1dd3d5cf315c02f7fd47dd4dc5b2ae6ef572183e`, SHA-256 `229fd5c52d5e19b9481bcccaadcba2187e9c3a423c7ac60e13e713b822c08cf0`.

## Interpretation and preservation boundary

The original base/locator wording remains preserved in `RESULT.md`; use the verified raw-containing commit and blob above to retrieve the declared input. This review establishes byte identity and a durable retrieval location, not additional proof of the historical container execution beyond its retained record.

No candidate, auditor, model, GUI, input, Docker allocation, or source experiment was rerun for this qualification. `PASS_RAW_AUDIT_T3_SCOPED` remains a finite audit of 30 authored rows. T1 `STOP_DOCKER_CLI_UNRESPONSIVE`, T2 `STOP_INVOCATION_ENTRYPOINT`, and parent #5318 `STOP_INDEPENDENT_AUDITOR_ORACLE_MISMATCH` remain unchanged. No runtime, real-effect, safety, Needle, GPU-benefit, or product claim follows. Issues #6290, #5957, and #5318 remain open.
