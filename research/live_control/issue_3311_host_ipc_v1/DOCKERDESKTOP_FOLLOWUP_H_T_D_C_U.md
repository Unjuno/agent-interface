# Docker Desktop transport follow-up for #3311

This platform-specific supplement does not alter the prior OrbStack Linux/arm64 PASS or the #3311 integrated cold/warm/repair scope.

## H — hypothesis

The existing v1 host-IPC broker and container runner may or may not support Docker Desktop's Windows/WSL shared-volume ownership and permission behavior. A valid test must prove the actual Docker endpoint, exact image ID, mount paths, and one-shot command before interpreting transport behavior.

## T — next bounded construction

Do not reuse allocation `dockerdesktop-v1-transport-20260927-01`. A future allocation must use a new immutable allocation ID and evidence path, start from current main and pinned source hashes, explicitly inspect `desktop-linux`, bind the image tag to the inspected image ID, and record the exact command actually passed to Docker after adapters. Use an isolated Windows-backed temporary directory; capture host ACLs and in-container UID/GID/mode for mounted IPC files without normalizing permissions before retaining originals. Freeze exactly one fake-CLI, no-network, no-authority invocation and capture Docker endpoint/container identity, broker/container outputs and exit codes, request/response bytes, source hashes, and cleanup. Run the independent auditor on the host, and bind its command receipt to the selected endpoint and image inspect receipt.

## D — current disposition

`HOLD_EXECUTION_CONTEXT_UNVERIFIED` for the 2026-09-27 Desktop bundle. Its raw test output reports a root-owned mode-0600 request read failure and container timeout, but its freeze says context `default` while the saved command says `orbstack`. On this Windows host, Docker `default` and Docker Desktop `desktop-linux` resolve to distinct named-pipe endpoints. The freeze also does not bind the test's default image tag (`agent-interface-3311-runtime-v2:20260920`) to its recorded inspected ID. These gaps prevent attributing the raw failure specifically to Docker Desktop. The original raw records and `FAIL_AUDIT` remain unchanged.

No new invocation was made after discovering these gaps. The active Docker Desktop daemon also had unrelated stopped containers, so the original empty-daemon isolation condition was unavailable for a fresh run.

## C — controls

No model call, GUI action, task input, or retry occurred. Host-context inspection was read-only. Existing allocation #3926 and other containers were not changed. The raw bundle was copied byte-for-byte; this addendum is an independent interpretation, not a rewrite of the experiment.

## U — unresolved / stop conditions

The next allocation remains unstarted until a dedicated, conflict-checked Docker Desktop invocation can pin `desktop-linux`, image identity, and the actual executed command receipt. Do not use this transport-only check as evidence for #3489's real Codex schema preflight or #3311's integrated six-task efficiency comparison.

## Addendum — Windows bind permission boundary probes (2026-09-27)

Two separate, frozen one-container allocations used a cached local image because the upstream transport test's pinned tag was absent. Both used `desktop-linux`, exact image ID `sha256:f82bbd2c087056f324794ca9b0de64c16f0ecaf9a84f30bb0aba17b5b1833786`, `--network none`, a unique Windows-backed temp path, fake IPC-shaped bytes only, and `--rm`.

**Allocation 02 / T:** container root created the exact 53-byte request fixture mode `0600`; Windows host readback matched its hash, but WSL non-root received `Permission denied`. Independent audit: 8/8 checks; decision `STOP_WSL_NONROOT_CANNOT_READ_ROOT_0600_WINDOWS_BIND_FILE`.

**Allocation 03 / explicit treatment delta:** the same fixture bytes were changed to mode `0644` in-container. Container, Windows, and WSL SHA-256 values matched; WSL could read. Independent audit: 10/10 checks; decision `PASS_MODE0644_MAKES_SYNTHETIC_FILE_READABLE_NOT_A_SECURE_FIX`.

**D:** The paired construction evidence supports permission mode as a mechanism on this Docker Desktop Windows-backed bind mount. It does not establish a safe production fix: 0644 exposes request contents to all local users allowed by the mount. Keep the current runtime behavior unchanged pending a scoped ownership/ACL design and same-boundary broker/runner verification.

**C:** Each allocation ran once with no retry, network, model, GUI, or input. Unrelated stopped containers were left untouched; named test containers were removed and post-run absence recorded. Raw outcomes and per-bundle hashes are retained separately.

**U:** Remaining work is a secure least-privilege file-ownership/ACL treatment tested with the actual repository runner and host broker, followed by the distinct real host-Codex schema preflight gate and the #3311 integrated six-task matched comparison. Neither has been satisfied by these probes.
