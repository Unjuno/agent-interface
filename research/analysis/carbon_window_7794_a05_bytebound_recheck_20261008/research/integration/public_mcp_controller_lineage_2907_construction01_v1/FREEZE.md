# Issue #2907 controller/session-lineage construction probe

## H/T/D/C/U

- **H:** Current-main runtime exposes a caller-owned session boundary that can carry read-only observations and guarded dispatch through one X11 backend lineage across the three-app fixture.
- **T:** Use the exact public runtime source closure from the already frozen three-app Docker study. In one local Linux/amd64 Docker container, start private Xvfb/Openbox and Inkscape, Calc, Chromium; open one runtime session; observe the three explicit window IDs in order; submit an old observation-sequence control with otherwise valid program/lease fields; then a current-sequence harmless ESC plus mandatory release. Preserve raw receipts and PNGs. Audit separately in a network-disabled, read-only Docker container.
- **D:** Construction PASS requires all observations returned without authority/input, one session/backend object identity, stale request refused specifically as STALE_OBSERVATION with zero backend emissions, fresh neutral request completed, per-dispatch/final release receipts verified empty, source Git blobs matching exact main, and independent raw audit with no errors.
- **C:** Image public-mcp-three-app-2907:formal01, ID sha256:b2b42660e35475baf5ef7a546a8c6901c39f04f69266cd9eebfe49c7ed49ea09, linux/amd64; base mixed-app-2499-xauth:v4 ID sha256:eaf46582f96fd46a1ad6a240928b4c2a828de3d058a4b1490bbadf708d5a52d3; --pull=never --network none --pids-limit 512 --memory 4g --cpus 4; source bind read-only; evidence bind writable. No workflow, model, remote service, or existing Ollama-container interaction.
- **U:** Construction only. Does not compose calls through the public MCP-owned session; does not run all four #2499 perturbations through the controller, typed focus/modal/window-generation admission, app-specific independent effect scoring, #2789 six-task gate, model/task success, performance, product readiness or broad reliability. session_id in raw data is a construction-local correlation digest; object identity fields demonstrate the same Python session/backend object in one process, not a server-issued persistent session ID.

## Preserved construction iterations

- construction01: STOP before any observation/dispatch; Calc window owner PID differed from launcher PID. Output records the stop. The runner was revised during debugging; the exact pre-run runner hash was not captured, so the STOP source is not source-reconstructable.
- Initial local container import preflight failed because the source mount had one extra runtime/ level. No apps or dispatches ran.
- construction02: container refused to start because its output directory had been pre-created. No apps or dispatches ran.
- construction03: three observations and dispatch returns occurred, but the intended stale control was rejected earlier as INVALID_PROGRAM because expires_at_ns=0. It is not evidence of stale-sequence admission. Preserve its raw output unchanged.
- construction04: distinct output path and runner v3; valid future lease expiry isolates the stale-sequence gate. This is the only iteration evaluated by audit_v1.py.

## construction04 identities

- Runner construction_v3.py SHA-256: CDF7A51EADEBBE9114E6C5DBF90CE882A1463E163FBD1693F7E0620101A5230C.
- Raw lineage SHA-256: 5699c022ddfac9877ea6f06da270ed07f168e9b2f86942e65930ca1b48ebbb39.
- Exact runtime Git blob IDs are recorded in audit04/audit.json; five runtime-critical files were compared to the main source blobs.

No formal allocation was consumed. No runtime source was changed.

