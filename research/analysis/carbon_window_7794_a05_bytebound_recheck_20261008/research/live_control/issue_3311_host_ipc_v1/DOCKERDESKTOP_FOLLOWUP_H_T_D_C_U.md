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

**Allocation 04 / least-privilege treatment:** the WSL host account was UID/GID `1002:1002`. Container root changed the same fake request's owner to `1002:1002` and retained mode `0600`. The WSL user read it successfully with the exact same SHA-256; observed mount metadata was `1002:1002 600 53`. The independent audit verifies endpoint, image, command, identity, bytes/hash and cleanup. This is a promising local mechanism, not a runtime fix: production UID discovery, ownership races, cross-host behavior, and actual runner/broker composition remain untested.

**C:** Each allocation ran once with no retry, network, model, GUI, or input. Unrelated stopped containers were left untouched; named test containers were removed and post-run absence recorded. Raw outcomes and per-bundle hashes are retained separately. Allocation 04 modifies ownership only for the generated 53-byte fake file under its unique temporary path.

**Allocation 05 / repository runner-broker roundtrip:** a candidate runner change reads an optional complete UID/GID pair, chowns its private mkstemp file before atomic rename, and verifies owner plus mode `0600`; the WSL Docker backend passes its own UID/GID. The modified existing fake-CLI roundtrip ran once against pinned Desktop `default`/image ID. It created request owner `1002:1002`, mode `0600`, and the broker successfully read/invoked the fake CLI, demonstrating that the owner-only permission boundary works in the actual runner/broker path. The roundtrip then stopped: the current host broker omitted the `model_instructions_file=...` argument required by the frozen fake CLI, which returned no events; container and broker both exited 1. No retry.

**D:** `STOP_BROKER_DID_NOT_FORWARD_MODEL_INSTRUCTIONS`. This confirms only that candidate owner assignment resolves request readability in this WSL/Docker Desktop path; it does not pass the full IPC exchange. Current main also contains a one-shot zero-exit mapping defect tracked by active PR #4524; this allocation's child failed, so that separate success case was not tested. The full WSL backend unit suite was unavailable locally because the Python environment lacks `referencing`; focused owner and command tests passed 5/5 and `py_compile` passed.

**U:** Resolve the broker's instructions forwarding in a non-conflicting follow-up and wait for #4524's one-shot exit contract to be accepted before allocating another full roundtrip. Review host-UID propagation and race-safe ownership (including mismatched identity and unexpected paths) under an independent security review. Then perform the distinct real host-Codex schema preflight and #3311's integrated six-task matched comparison. None has been satisfied by these probes.
