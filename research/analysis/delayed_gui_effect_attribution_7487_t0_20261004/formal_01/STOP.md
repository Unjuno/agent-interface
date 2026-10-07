# OrbStack container preflight STOP

- Status: `STOP_ORBSTACK_DAEMON_BLOB_READ`
- One read-only command: `docker image ls --format '{{.Repository}}:{{.Tag}} {{.ID}}'`
- Result: `Error response from daemon: rpc error: code = Unknown desc = blob sha256:68ca3975c1576d18f8cf52bcb6e153ce31516ce22cd75a38fd5cee6c572a7882 expected at /var/lib/docker/containerd/daemon/io.containerd.content.v1.content/blobs/sha256/68ca3975c1576d18f8cf52bcb6e153ce31516ce22cd75a38fd5cee6c572a7882: open /var/lib/docker/containerd/daemon/io.containerd.content.v1.content/blobs/sha256/68ca3975c1576d18f8cf52bcb6e153ce31516ce22cd75a38fd5cee6c572a7882: operation not supported`
- Container candidate/auditor invocations: 0/0.
- No pull, build, daemon restart, or repeated image inventory was attempted.
- This infrastructure STOP does not equal a scientific fail. The separate host-only candidate/auditor result is recorded in `../RUN.md` and is not promoted to container/isolation evidence.
