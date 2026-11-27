# Compressed raw log custody

Each `.log.gz` below decompresses byte-for-byte to the captured local `.log` file. The original `.log` files remain in the local ignored workspace; this packet retains exact bytes in gzip form. `SHA256SUMS` covers the gzip artifacts, and this table records the uncompressed SHA256.

| Captured log | Preserved artifact | Uncompressed SHA256 |
|---|---|---|
| `runs/normal/container.stdout.log` | `runs/normal/container.stdout.log.gz` | `42e69024c541879dbdb3abc0b92d9f9db4d08e44b05e9d94182e42122b450c6e` |
| `runs/normal/test.log` | `runs/normal/test.log.gz` | `7537956f057d2bcb9f2c7c943710fcf689860648b285dfd5d8c7937fcd09ed35` |
| `runs/normal/xvfb-server.log` | `runs/normal/xvfb-server.log.gz` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/optimized/container.stdout.log` | `runs/optimized/container.stdout.log.gz` | `a1864fdc045f48ca2ef8cb5e9bd3d2f59967010200aeb3f4e87e62104f1e15f3` |
| `runs/optimized/test.log` | `runs/optimized/test.log.gz` | `94a42eafa799f9e2df50d7326a76a274e8e2d27499838707f8eeebe02d4b3579` |
| `runs/optimized/xvfb-server.log` | `runs/optimized/xvfb-server.log.gz` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
