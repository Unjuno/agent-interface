# Compressed raw log custody

Each `.log.gz` below decompresses byte-for-byte to the captured local `.log` file. The original `.log` files remain in the local ignored workspace; this packet retains exact bytes in gzip form. `SHA256SUMS` covers the gzip artifacts, and this table records the uncompressed SHA256.

| Captured log | Preserved artifact | Uncompressed SHA256 |
|---|---|---|
| `runs/optimized-01/container.stdout.log` | `runs/optimized-01/container.stdout.log.gz` | `80b683dd9ce1a4ef88ae1cb94aaea52a88dce61a5f58cca0dc9122a48f2f6c93` |
| `runs/optimized-01/test.log` | `runs/optimized-01/test.log.gz` | `5db429abc601cac0ff3eb23975eab0f828615cfa887d9126607919e6487e070e` |
| `runs/optimized-01/xvfb-server.log` | `runs/optimized-01/xvfb-server.log.gz` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
