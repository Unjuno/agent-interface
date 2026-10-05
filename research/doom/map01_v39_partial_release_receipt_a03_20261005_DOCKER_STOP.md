# A03 Docker revalidation STOP — 2026-10-05

The OrbStack daemon responded to a read-only `docker --context orbstack info --format '{{.ServerVersion}} {{.OSType}}/{{.Architecture}}'` probe with `29.4.0 linux/aarch64`.

The first image inventory read, `docker --context orbstack image ls --format '{{.Repository}}:{{.Tag}} {{.ID}}'`, failed while reading the image store:

```
Error response from daemon: rpc error: code = Unknown desc = blob sha256:a5db9d0eaec4f9e2ea55a975ba4b8103e2eec9df1d093d136f5b2525e32f467c expected at /var/lib/docker/containerd/daemon/io.containerd.content.v1.content/blobs/sha256/a5db9d0eaec4f9e2ea55a975ba4b8103e2eec9df1d093d136f5b2525e32f467c: open /var/lib/docker/containerd/daemon/io.containerd.content.v1.content/blobs/sha256/a5db9d0eaec4f9e2ea55a975ba4b8103e2eec9df1d093d136f5b2525e32f467c: operation not supported
```

No image pull, build, container start, or retry was attempted. Disk availability was 19 GiB on `/` at observation time. The containerized candidate revalidation is STOPPED because Docker's content store cannot enumerate its local image metadata. The prior A02 host-side test results remain as recorded; this probe supplies no container evidence. Resume only after the image store is independently repaired or becomes readable, then use an already-present digest-pinned Python image without pulling or building.
