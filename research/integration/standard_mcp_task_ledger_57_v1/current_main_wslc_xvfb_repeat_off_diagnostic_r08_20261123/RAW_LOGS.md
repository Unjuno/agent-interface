# Compressed raw log custody

Each `.log.gz` below decompresses byte-for-byte to the captured local `.log` file. The original `.log` files remain in the local ignored workspace; this packet retains exact bytes in gzip form. `SHA256SUMS` covers the gzip artifacts, and this table records the uncompressed SHA256.

| Captured log | Preserved artifact | Uncompressed SHA256 |
|---|---|---|
| `runs/normal/container.stdout.log` | `runs/normal/container.stdout.log.gz` | `c4d295a88e2ed56d37c2bf4f9d4e507ba2c4bf3ab67dd46604783b5f096aa66b` |
| `runs/normal/test.log` | `runs/normal/test.log.gz` | `9a4f24cbe304ded63f164bd50e0419e767d0ac941531617b62ddc30fd7c4e54d` |
| `runs/normal/xvfb-server.log` | `runs/normal/xvfb-server.log.gz` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/optimized/container.stdout.log` | `runs/optimized/container.stdout.log.gz` | `e1f87d0571eb0022762aef0f53e8e82a4fd443b79244a26846510cc6c7726728` |
| `runs/optimized/test.log` | `runs/optimized/test.log.gz` | `f2d728393ec5531098f0264e21a32cff5970519af39e9845902d8de0b573b79d` |
| `runs/optimized/xvfb-server.log` | `runs/optimized/xvfb-server.log.gz` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
