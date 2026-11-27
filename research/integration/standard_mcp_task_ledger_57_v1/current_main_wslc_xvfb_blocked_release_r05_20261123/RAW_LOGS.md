# Compressed raw log custody

Each `.log.gz` below decompresses byte-for-byte to the captured local `.log` file. The original `.log` files remain in the local ignored workspace; this packet retains exact bytes in gzip form. `SHA256SUMS` covers the gzip artifacts, and this table records the uncompressed SHA256.

| Captured log | Preserved artifact | Uncompressed SHA256 |
|---|---|---|
| `runs/normal/container.stdout.log` | `runs/normal/container.stdout.log.gz` | `81c6bb23bd93936b99361d656e947837859ee394583a1cd6cd6d404563da78ff` |
| `runs/normal/test.log` | `runs/normal/test.log.gz` | `9a87e9b7d2057d81d4f3d86b429c072c9099f98d5c4a9aa346cec74a8b2cde39` |
| `runs/normal/xvfb-server.log` | `runs/normal/xvfb-server.log.gz` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/optimized/container.stdout.log` | `runs/optimized/container.stdout.log.gz` | `fdce7eed1b91363943f9830a9acd9fc53e1cd3f4655fde48d13bee59ca99be12` |
| `runs/optimized/test.log` | `runs/optimized/test.log.gz` | `626b57790a56dbd77b361b3682af61af8ba5186cdabe5d1acdb1e75a3963008e` |
| `runs/optimized/xvfb-server.log` | `runs/optimized/xvfb-server.log.gz` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
