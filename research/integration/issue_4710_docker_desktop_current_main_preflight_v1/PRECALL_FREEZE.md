# Formal 01 pre-call freeze and amendment

Allocation: `issue-4710-formal01`; intake main: `f5205f532b1f64b71c9a1d69af07e8389f7fd8e0`.

## Image amendment

Issue #4710 preregistered local image ID `sha256:7e4a3b6f3917baa9f153b4dfd011a4ea528a3d200a7a3d274aa9479900ee7b41`. A Docker Desktop local inspection before any formal invocation found that image absent. Do not pull, build, or substitute silently. This additive amendment pins the already-cached `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, inspected as the same immutable image ID on `desktop-linux`, Linux/amd64. The runner and host broker use only Python standard-library facilities; the archived offline construction Dockerfile for this runner also uses this exact base image. Formal results, if any, must state this amendment. No image has network access during either invocation.

## Fixed request and bounds

- Exactly one broker/CLI invocation, no retries, including after timeout or ambiguous transport.
- Prompt bytes: `Schema compatibility probe. Produce any object accepted by the supplied schema.\n`.
- No image, task fixture, GUI, user input, or submission. Authority is false.
- Host executable/version and Docker context/engine/image ID/platform are in `SOURCE_MANIFEST.json`; hashes are SHA-256 over exact source bytes.
- The current host broker launches `codex exec` with `--sandbox read-only`, `--ignore-user-config`, `--ignore-rules`, and `--ephemeral`; the prompt and supplied instructions prohibit tools, file/network access, and execution claims. The working directory is a dedicated empty scratch directory, never this project workspace.
- Container: network none, read-only root and source, no capabilities, no-new-privileges, 1 CPU, 512 MiB, 64 PIDs; only output and IPC host mounts writable (container `/tmp` is bounded tmpfs).
- Unique per-attempt output, IPC, and container name must be empty/nonexistent before formal start. Retain all outputs and never retry the allocation.
- A separate Docker invocation audits the raw event stream, usage, schema, request lineage, and inspected container restrictions.

## Construction only (not a formal result)

On Docker Desktop `desktop-linux` with engine `28.5.1 linux/amd64` and the amended cached image, the exact main-source event accounting tests passed 8/8 (0.039 s); independent-auditor controls passed 5/5 (0.000 s). These runs contained no model call. Host Codex CLI identity was `codex-cli 0.158.0-alpha.2.1`, SHA-256 `8f0554ede25bbc5450921897c468b2e84635aa513c5017457997af0954581f49`; `codex login status` reported ChatGPT login. No formal call has started.

## Decision handling

The main-run exit status alone never establishes PASS. The independent offline audit must return `PASS_DOCKER_DESKTOP_CURRENT_MAIN_INSTRUCTIONS_PREFLIGHT_ONLY`. Any uncertain call start, timeout, incomplete receipt, or failed audit is retained as STOP/HOLD with no retry. This result cannot satisfy #3489 or authorize #3311's multi-task allocation.
