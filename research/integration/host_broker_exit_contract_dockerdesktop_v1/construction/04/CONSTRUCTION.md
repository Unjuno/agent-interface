# Construction 04 — Docker bind-mount mode syntax

Classification: `PASS_DOCKER_MOUNT_SYNTAX_AND_WRITABILITY`.

After allocation 01 stopped before container creation, a separate non-formal container invocation exercised the corrected mount syntax. The source study directory was mounted with `readonly`; the output directory was mounted writable by omitting a mode suffix (Docker `--mount` defaults to read/write). Docker Desktop accepted both mounts, the network-none/read-only-rootfs container wrote `/out/probe.txt`, and the host read back the exact marker `rw-bind-mount-ok\n` (SHA-256 `a1213ce0d2f12052e3548e3f43b040031235a1533d6b9c26423b4454c29f9a95`). The container used `--pull=never --platform linux/amd64 --network none --read-only`, 1 CPU, 256 MiB, 64 PIDs, all capabilities dropped and no-new-privileges; it was `--rm` and no container remained.

This construction check ran no broker, fake Codex executable, or formal case. It validates only Docker CLI mount syntax and host evidence write/readback. The changed runner also uses Docker's `readonly` mount option for the independent audit input and a default writable output mount. Formal allocation 02 is a separate, prospectively frozen output path; allocation 01 remains the STOP above and is not rerun.
