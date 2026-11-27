# Compressed raw log custody

Each `.log.gz` below decompresses byte-for-byte to the captured local `.log` file. The original `.log` files remain in the local ignored workspace; this packet retains exact bytes in gzip form. `SHA256SUMS` covers the gzip artifacts, and this table records the uncompressed SHA256.

| Captured log | Preserved artifact | Uncompressed SHA256 |
|---|---|---|
| `runs/key-off/container.stdout.log` | `runs/key-off/container.stdout.log.gz` | `961964e5968198647595f10561ce4ae602d80822beacf6d2067c19964e2338b5` |
| `runs/key-off/xvfb-server.log` | `runs/key-off/xvfb-server.log.gz` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
