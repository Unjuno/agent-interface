# Evaluator isolation v1

This artifact tests only a first Docker/X11 separation rung for Issue #4666. It is not a B0-vs-C1 comparison, semantic-performance result, or proof against a hostile process with raw access to an X11 server. X11 grants broad control over the dedicated display.

## Preregistered check

Seed 2001, difficulty 1.0, fixed simulation clock; the public v0 generator makes the first stage a `target` stage with a 2.6 s deadline. A controller container receives only a dedicated X11 display, authenticated with a per-run MIT-MAGIC-COOKIE, and sends one inert `w` key. It must not have the Arena source, report, seed, evaluator argv, evaluator PID namespace, or Docker socket available through its own filesystem/process view. The evaluator has source in its image and report in its private tmpfs. Both use an internal Docker network. The dedicated display remains a powerful input/output channel; this is container/process/filesystem separation evidence, not proof of a hardened hostile-agent boundary.

PASS requires: valid XWD capture; evaluator report shows seed 2001, target-first, natural `deadline_miss`; evaluator PID 1 argv records seed 2001; evaluator ledger records injected `w`; controller process view has no seed; source/report paths are absent; controller is unprivileged with no bind mounts, shared PID, or Docker socket; network is internal; independent raw-artifact audit has no errors. A boundary leak is FAIL. Missing provenance or broken infrastructure is STOP. No formal retry.

## Construction and formal sequence

1. Run `python build_images.py`; it copies the exact tracked `arena.py` and `engine.py`, hashes them, builds separate pinned-base images and records their ids. Apt package resolution is time-dependent; the built image IDs, rather than a future rebuild from the Dockerfiles, are the formal execution artifacts.
2. Run `python construction_smoke.py` before freeze. It uses seed 2002 and is not formal evidence. Preserve each bring-up outcome in the construction attempt ledger; the passing smoke stores the raw XWD and its digest under `construction/smoke-02/`.
3. Run `python freeze_sources.py`; commit and push only the generated `FREEZE.json`, then inspect that exact GitHub commit and source parent before proceeding. Do not rebuild images after freeze.
4. A future formal run must use exclusive creation under `formal/001`, execute once, and preserve all raw evidence. Audit it in a separate network-disabled, read-only, pinned Python container.

Construction has passed, but steps 3-4 are not implemented in this snapshot. There is no formal result and no basis to infer one from the construction smoke. The formal trial must use Docker Desktop's Linux container backend and amd64, preserving build logs, container inspection JSON, evaluator/controller outputs, report, capture, and independent audit JSON.
