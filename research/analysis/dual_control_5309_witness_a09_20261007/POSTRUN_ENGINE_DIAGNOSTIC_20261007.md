# Post-run Docker engine diagnostic (2026-10-07)

This is a new, read-only observation made after the A09 STOP record. It is not an A09 execution log and cannot reconstruct the historical stderr, stdout, or exit statuses omitted from the original run. The original `STOP.md` remains unchanged and its historical evidence remains summarized rather than byte-exact.

No pull, container launch, repair, prune, deletion, or image mutation was performed. Commands below were run from the A09 research checkout; captured stdout was empty for both commands. Exit status and stderr are recorded exactly as returned by the shell command wrapper.

## Image inspect

Command:

```sh
docker image inspect python:3.12-slim --format '{{.Id}} {{.RepoDigests}}'
```

Exit status: `1`.

Stderr:

```text
Error response from daemon: rpc error: code = Unknown desc = blob sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f expected at /var/lib/docker/containerd/daemon/io.containerd.content.v1.content/blobs/sha256/f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f: open /var/lib/docker/containerd/daemon/io.containerd.content.v1.content/blobs/sha256/f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f: operation not supported
```

The digest matches the prefix preserved in the historical STOP note, but that does not establish byte-for-byte identity with the old command output.

## Image inventory

Command:

```sh
docker image ls --digests --format '{{.ID}} {{.Repository}}:{{.Tag}} {{.Digest}}'
```

Exit status: `1`.

Stderr:

```text
Error response from daemon: rpc error: code = Unknown desc = blob sha256:f0190b1db8563e63136a31bd90f065ba7139ef3fb1fc269ec57487c4a115e8c0 expected at /var/lib/docker/containerd/daemon/io.containerd.content.v1.content/blobs/sha256/f0190b1db8563e63136a31bd90f065ba7139ef3fb1fc269ec57487c4a115e8c0: open /var/lib/docker/containerd/daemon/io.containerd.content.v1.content/blobs/sha256/f0190b1db8563e63136a31bd90f065ba7139ef3fb1fc269ec57487c4a115e8c0: operation not supported
```

This inventory probe currently identifies a different blob. It must not be described as recurrence of the historical inventory blob, whose digest was not retained.

## Scope and interpretation

These present-time probes support only that both read-only Docker queries failed in this later observation. They do not establish historical output identity, diagnose the underlying engine, or satisfy the A09 restart gate. The separate Node image used by A12 is unrelated evidence and does not establish Python image health.
