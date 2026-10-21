# Reproduce A28

One preregistered invocation was performed; do not rerun into this output directory. The candidate, immutable image, exact command parameters, raw data, exit record and container inventories are retained here. The command used the frozen image `sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592`, `--pull never --network none --cpus 1 --memory 512M --user 65534:65534 --rm`, read-only `INPUT` and separate writable `results/a28-01` mounts. On this host WSLc warned that cgroup/swap limits are not supported.

Run only the independent auditor against the preserved result:

```powershell
python audit.py
```
