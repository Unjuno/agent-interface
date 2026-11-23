# Compressed raw log custody

Each `.log.gz` below decompresses byte-for-byte to the captured local `.log` file. The original `.log` files remain in the local ignored workspace; this packet retains exact bytes in gzip form. `SHA256SUMS` covers the gzip artifacts, and this table records the uncompressed SHA256.

| Captured log | Preserved artifact | Uncompressed SHA256 |
|---|---|---|
| `runs/normal/baseline/container.stdout.log` | `runs/normal/baseline/container.stdout.log.gz` | `2e22c331a55d157723b4020e63ad2d28554bd91bb02f268f69dac777cbb9f1d6` |
| `runs/normal/baseline/xvfb-server.log` | `runs/normal/baseline/xvfb-server.log.gz` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/normal/global_off/container.stdout.log` | `runs/normal/global_off/container.stdout.log.gz` | `2e0d3695337c5bd96708acdfd45492f70d688194e60c1c24bb2ec00e53324cd1` |
| `runs/normal/global_off/xvfb-server.log` | `runs/normal/global_off/xvfb-server.log.gz` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/normal/key_off/container.stdout.log` | `runs/normal/key_off/container.stdout.log.gz` | `460bef097922fad0178e4b34052582f5ce8e90f59d9e6740407a418024c41196` |
| `runs/normal/key_off/xvfb-server.log` | `runs/normal/key_off/xvfb-server.log.gz` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/optimized/baseline/container.stdout.log` | `runs/optimized/baseline/container.stdout.log.gz` | `7c20576715c33e9ebd056a340e6dd93df96e101a4c24c268f51d6648991d1fad` |
| `runs/optimized/baseline/xvfb-server.log` | `runs/optimized/baseline/xvfb-server.log.gz` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/optimized/global_off/container.stdout.log` | `runs/optimized/global_off/container.stdout.log.gz` | `80a2b13a261ac8ef04157cceff4cc8f7b9b306f355b8fa3633bcb03ba04282a5` |
| `runs/optimized/global_off/xvfb-server.log` | `runs/optimized/global_off/xvfb-server.log.gz` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/optimized/key_off/container.stdout.log` | `runs/optimized/key_off/container.stdout.log.gz` | `edfe482a4cbbcf0062b9dff4fc7db8eb59d3a4326ff09597935cc30245857196` |
| `runs/optimized/key_off/xvfb-server.log` | `runs/optimized/key_off/xvfb-server.log.gz` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
