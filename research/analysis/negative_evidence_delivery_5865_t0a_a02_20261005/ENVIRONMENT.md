# T0a environment record

Captured on 2026-10-05 before candidate execution.

- Repository HEAD: `19a6b723e58ccfd2b8265e88659589ef9223fcc9` (latest `origin/main` at preflight).
- Host: macOS, arm64.
- Python: captured exactly in `FREEZE.json`.
- Docker context: `orbstack`; `docker info` reported `29.4.0 OrbStack aarch64`.
- Read-only `docker ps` failed with:

  ```text
  Error response from daemon: rpc error: code = Unknown desc = blob sha256:7a8e909db2bd3083e5661e95489b517d4cfcab6d153c01b2d0063dc58dd1a45b expected at /var/lib/docker/containerd/daemon/io.containerd.content.v1.content/blobs/sha256/7a8e909db2bd3083e5661e95489b517d4cfcab6d153c01b2d0063dc58dd1a45b: open /var/lib/docker/containerd/daemon/io.containerd.content.v1.content/blobs/sha256/7a8e909db2bd3083e5661e95489b517d4cfcab6d153c01b2d0063dc58dd1a45b: operation not supported
  ```

  No image/container/VM mutation or retry was made.

The proposal explicitly allows a CPU-only standard-library finite model. The
experiment is run with the local Python interpreter and is **not** described
as container-backed or equivalent to a runtime allocation.
