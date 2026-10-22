# C02 runtime preflight record

Date: 2026-10-09 JST / 2026-10-08 UTC. No existing image, container, volume, or VM was removed or modified.

- `docker info --format '{{.Architecture}} {{.OSType}} {{.DockerRootDir}}'`: `aarch64 linux /var/lib/docker`.
- `docker run --rm --pull=never --network none node@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80 --version`: exit 0, `v26.10.0`.
- `docker run --rm --pull=never --network none python:3.12-slim python --version`: exit 125. OrbStack/containerd reported an expected blob unavailable at `/var/lib/docker/containerd/daemon/io.containerd.content.v1.content/blobs/sha256/f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (`operation not supported`).
- `docker pull python:3.12-slim`: exit 1, same content-store lease/read error and blob digest.
- `docker images --digests`: failed reading blob `sha256:c9660ab9c4c50c49e59e4b11ed2e642169b42d369a0a2c28eb4f77b752d91481` (`operation not supported`). `docker system df` also failed reading blob `sha256:6efffbdf1526d51a1e4c7076b41ce021454986ac5fc5ef6ed971aca1e445ee0d`.
- `df -h / /Users/taka`: 113 GiB available at preflight.
- Host interpreter `/run/current-system/sw/bin/python3.12` resolves to `/nix/store/p1b85dd3syy1yx8q039m1c6v2x2l4w0a-python3-3.12.13/bin/python3.12`, version 3.12.13. The frozen CPU-only candidate and auditor do not call Docker, the network, or a GUI.

The Python-image failures are retained as environment diagnostics. They are not scientific outcomes and did not cause a candidate/auditor retry; C02's host runtime and source were frozen separately before execution.
