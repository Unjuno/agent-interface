# Compressed raw log custody

Each `.log.gz` below decompresses byte-for-byte to the captured local `.log` file. The original `.log` files remain in the local ignored workspace; this packet retains exact bytes in gzip form. `SHA256SUMS` covers the gzip artifacts, and this table records the uncompressed SHA256.

| Captured log | Preserved artifact | Uncompressed SHA256 |
|---|---|---|
| `runs/optimized-timeout-1s/container.stdout.log` | `runs/optimized-timeout-1s/container.stdout.log.gz` | `e3b1065a47bcdd4e3cee27b2140f2c1840f1d66df9802e7616f3d52a06b7ef5c` |
| `runs/optimized-timeout-1s/test.log` | `runs/optimized-timeout-1s/test.log.gz` | `b8de9e890e674b975f6e4357e6f98f775701ae118b005893ebb0a0d77fd19d76` |
| `runs/optimized-timeout-1s/xvfb-server.log` | `runs/optimized-timeout-1s/xvfb-server.log.gz` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
