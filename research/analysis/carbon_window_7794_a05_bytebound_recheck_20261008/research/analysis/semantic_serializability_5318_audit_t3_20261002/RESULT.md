# Issue #5957 successor T3 — frozen raw audit in Docker

**Disposition: `PASS_RAW_AUDIT_T3_SCOPED`**

This is a fresh audit-only allocation after the prior T1 Docker CLI STOP and the T2 pre-script invocation STOP. It preserves both STOPs as well as #5318's candidate/raw/original auditor outcome unchanged. No candidate was rerun and no training, model, GUI, or external action occurred.

## H — hypothesis

The independently implemented raw-only auditor reconstructs every one of the 30 frozen #5318 rows, verifies the exact raw bytes, and rejects five deterministic corruption controls in the intended container boundary.

## T — frozen inputs and invocation

- T3 allocation: `semantic-serializability-5318-audit-t3-20261002-01`; owner: this Codex task.
- Base main frozen immediately before execution: `c4d2d4b1ccf4512ec79af75bd8eaecfcada39947`.
- Auditor source branch/commit: `research/semantic-serializability-5318-audit-successor-20261001` / `4acf5905222453b1b65990de3260382dd90eba22`.
- Auditor `audit.py` SHA-256: `479e1a365c94f6fd36963f2afcc633b9c26d9fc18b39f4183ee7a6b51817cda6`.
- Immutable input commit: `3d6ffc76d535309cf3820ed33cb9327354f03648`.
- `RAW.jsonl` SHA-256: `26fa7c694fd0f3a35bc5085b6145af639e88c8dd79666c3284db12f11df9ed90`.
- Image: local immutable image ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, `linux/amd64`; no pull. Image has no ENTRYPOINT, so T3 explicitly invokes `python`.
- Prelaunch Docker container inventory: empty. RTX 3080 was idle; this deterministic Python audit is CPU-only and has no training/CUDA computation to accelerate.
- One invocation, exit 0; retries 0. Network disabled, pull disabled, root filesystem and both mounts read-only, 0.25 CPU, 256 MiB memory, 64 PIDs.

Exact command (mount source paths are the frozen local files above):

```powershell
docker run --rm --pull=never --network none --cpus=0.25 --memory=256m --pids-limit=64 --read-only --mount "type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\goal-unjuno-agent-interface-github-mcp-6\work\semantic-serializability-5318-audit-successor-20261001\research\analysis\semantic_serializability_5318_audit_t1_v1\audit.py,target=/src/audit.py,readonly" --mount "type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\goal-unjuno-agent-interface-github-mcp-6\work\semantic-serializability-5318-t0-20261001\research\analysis\semantic_serializability_5318_t0_v1\results\formal-01\RAW.jsonl,target=/input/RAW.jsonl,readonly" sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /src/audit.py /input/RAW.jsonl --controls
```

## D — observed result

The container returned exit code 0. Raw stdout is retained in [audit-output.json](audit-output.json):

- rows: 30
- raw digest: exact expected SHA-256 above
- baseline errors: `[]`
- mutation controls rejected: omitted row, duplicate row, changed final value, changed committed IDs, changed scenario label — **5/5**.

The host construction suite was rerun against the same frozen auditor source: **9/9 tests passed**. This is corroborating construction evidence, not a substitute for the Docker result.

## C — alternatives and controls

The earlier T2 `exec format error` was caused by calling a script directly in an image with no ENTRYPOINT. T3 fixed only the invocation by explicitly passing `python`; all source, input, image, and decision gates remained pinned. T2 remains `STOP_INVOCATION_ENTRYPOINT`; T1 remains `STOP_DOCKER_CLI_UNRESPONSIVE`.

## U — scope limits

This is an independent finite audit of previously retained synthetic bytes. It does not establish serializability beyond these 30 authored rows, real external effects, runtime safety, GUI behavior, Needle adaptation, GPU benefit, or product performance. The parent #5318 candidate outcome remains its original STOP.
