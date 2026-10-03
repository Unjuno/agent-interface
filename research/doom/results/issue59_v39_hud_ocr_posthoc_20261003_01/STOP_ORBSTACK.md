# STOP — OrbStack container image read

- `orbctl status`: `Running`
- `docker context show`: `orbstack`
- Read-only check attempted:
  `docker image inspect python:3.12-slim --format '{{.Id}}'`
- Result: `Error response from daemon: rpc error: code = Unknown desc = blob
  sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f
  expected at /var/lib/docker/containerd/daemon/io.containerd.content.v1.content/blobs/sha256/f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f:
  open ...: operation not supported`
- Disposition: `STOP_ORBSTACK_IMAGE_BLOB_READ_UNSUPPORTED`. No container
  experiment was started, and no pull/build, reset, VM operation, or action on
  another worker's resources was attempted. The existing isolated container
  route was unavailable for this segment; the non-mutating CPU OCR analysis ran
  on the local host instead.
