# #3311/#3489 macOS OrbStack image-store preflight

Status: `STOP_LOCAL_ORBSTACK_IMAGE_STORE_UNAVAILABLE`

This is a read-only environment preflight, not the frozen #3489 endpoint/schema allocation and not a container experiment. Source context: current `main` at `85903cae9541a3faf4303cff10ba58cc5a1cc436`.

## Observations

- Docker context selection showed `orbstack`; `docker version` returned client `29.5.2` and server `29.4.0`.
- `docker info` returned `OS=linux arch=aarch64 driver=overlayfs root=/var/lib/docker`.
- `docker container ls` returned no running containers. `docker container ls -a` showed retained exited records; none were started, removed, or modified.
- `docker image inspect sha256:e47cbddc70722a816758a4a1c27cf2a38071c889670be98bf3eacdc9fff17916` failed in the daemon while opening that image's containerd content-store blob, ending with `operation not supported`.
- `docker system df` independently failed while retrieving image storage, with the same `operation not supported` content-store error for blob `sha256:0e35cdb51a82e59d359ec09b85ce835d9217a1eab65b68ce1871c9b0a85014c9`.
- Host Codex CLI reports `codex-cli 0.146.1`.

## Boundary

No container was launched, no image was pulled or built, and no host CLI request, model turn, GUI, or task input occurred. The required immutable image identity cannot be established while OrbStack's image inspection/storage endpoints fail. The #3489 one-shot schema endpoint allocation remains unspent. No accuracy, integration, or desktop-control claim follows.

The exact image-store failure was observed before freezing a candidate. This report does not represent that diagnostic as a formal candidate/auditor experiment or as a retry. Do not retry the same image inspection or launch the formal gate until the daemon's image-store condition has changed and a fresh preflight confirms a usable pinned image.

## Offline current-main regression follow-up — 2026-10-04

While the container gate is unavailable, the local, no-GUI regression path was
checked at this branch's current source:

- `python3 -m unittest runtime.test_golden_desktop_demo_v3` — 2 tests passed.
- `python3 -m unittest runtime.test_golden_desktop_demo_v2` — 1 test passed.
- `python3 -m unittest research.live_control.test_integrated_efficiency_app_server_model_v1` — 4 tests passed.
- `python3 -m unittest runtime.test_run_full_golden_ipc_v2` — 1 test passed.

The first v3 test import stopped before test execution because this sparse
checkout omitted its tracked `research/live_control/` adapter dependency. After
materializing that exact source path, all three commands above passed. No
runtime source or allocation was changed. This is local regression evidence,
not GUI, model, task-effect, or efficiency evidence.

The retained v3 live auditor is pinned to an older source snapshot. Invoking it
against this checkout stopped at its initial source-hash assertion for
`runtime/golden_desktop_demo.py`; it did not audit the archived run under current
main. Reusing it requires the exact frozen source capsule, which is not present
in this checkout. Keep the historical live report scoped to its frozen source.

## Correct Docker CLI and local schema test follow-up — 2026-10-04

OrbStack read-only diagnostics refined the earlier CLI observation. Although the
selected Docker context is `orbstack`, the shell's first `docker` is the Nix
29.5.2 client. `orbctl doctor` reported that this is not OrbStack's CLI; the
app-bundled client at `/usr/local/bin/docker` is 29.4.0 and matches the
29.4.0 server. OrbStack is version 2.1.3. Its doctor also reported stale CLI
plugin/path configuration. No PATH, symlink, plugin, or OrbStack setting was
changed. A later read-only probe with the app-bundled client is recorded below.

`orbctl list` showed other running Linux machines on this shared OrbStack host;
their ownership and release state were not established. No Docker container was
started. This shared-runtime check is not an exclusive experiment allocation.

The repository's schema validator suite was first run with system Python 3.14.5
and stopped because `jsonschema` was absent. An isolated temporary environment
installed only `runtime/requirements-docker-schema-preflight.txt`
(`jsonschema==4.25.1`); `python -m unittest
runtime.test_docker_schema_preflight_v1` then passed all 18 tests. This includes
synthetic response/schema cases and acceptance of the current plain and
compiled schemas. It does not exercise the host IPC runner, a live model turn,
container provenance, or the gated one-shot endpoint allocation.

## Matching OrbStack client image-store probe — 2026-10-04

To test whether the initial storage failure was caused by the Nix Docker client,
one read-only inspection of the same pre-existing image digest was issued via
`/usr/local/bin/docker --context orbstack`, the OrbStack-bundled 29.4.0 client
that matches the 29.4.0 server:

```text
docker image inspect sha256:e47cbddc70722a816758a4a1c27cf2a38071c889670be98bf3eacdc9fff17916
Error response from daemon: rpc error: code = Unknown desc = blob sha256:e47cbddc70722a816758a4a1c27cf2a38071c889670be98bf3eacdc9fff17916 expected at /var/lib/docker/containerd/daemon/io.containerd.content.v1.content/blobs/sha256/e47cbddc70722a816758a4a1c27cf2a38071c889670be98bf3eacdc9fff17916: open ...: operation not supported
```

The same daemon-side content-store failure with the matching client falsifies
client-version mismatch as a sufficient cause. It does not distinguish an
unreadable or missing blob from a backing-store or daemon defect. This
diagnostic line is closed; do not repeat image inspection or alter the store
while other OrbStack machines are running without an owner-confirmed
maintenance window. No container, pull, build, restart, reset, host Codex
request, model turn, GUI, or task input occurred. The frozen #3489 allocation
remains unspent.
