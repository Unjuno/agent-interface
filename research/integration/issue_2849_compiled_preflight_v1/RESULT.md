# Result — compiled schema over Docker/OrbStack host IPC

**Status: PASS — one compiled-schema no-image endpoint preflight only.**

- Exactly one fresh `gpt-5.6-luna` low request; broker/CLI and container returned 0. Backend resolver selected the Docker preflight call. IPC request id: `ac7ec4ec8aff48d1924b18b60bf307cb`.
- Request mode was `handle`, image was null, workspace empty, authority false. OrbStack context, Linux/aarch64; pinned Python image `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; `--network none`, read-only root/source, `--tmpfs /tmp`.
- Event stream held one known skills-context-budget auxiliary warning (classified, hash retained), one `agent_message`, and one usage-bearing `turn.completed`. Usage: 12,401 input; 113 output; 0 reasoning output; no cached/cache-write input.
- Candidate runner status PASS. Independent offline Draft 2020-12 validation PASS; one valid JSON object and one completed turn. All 8 independent audit checks true.
- Raw event SHA-256: `d9fc965e576e357aefcf537a7732ba7932ee362276a2b00dd9b82f68b5e7350e`. Request SHA-256: `3b216fc1c88e3f9bc89f83ee735c6c3a62ee91eeb80d210ca0c5d3e1f3af2e26`. Broker receipt SHA-256: `f626b0702bf4a6082e74914b8b077255529f64e4941ae2ae1ce5abf08a2ea387`.
- Host Codex CLI: `codex-cli 0.146.1`; Node `v26.7.0`. Broker stderr includes local CLI cache/state and optional MCP shutdown diagnostics; protocol and schema checks nevertheless completed successfully.

This result unlocks only the next preregistration. No GUI or task input occurred; no six-task Docker allocation, comparative outcome, or integrated efficiency claim is made here. Issue #2849 remains open.

Raw request/response, broker, process, schema, candidate classification, container output and independent audit command/result are retained under `evidence/compiled/compiled/`.
