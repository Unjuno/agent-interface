# Reproduce A29

One preregistered candidate invocation was made; do not rerun into this output directory. Frozen image `sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592`; WSLc `--pull never --network none --cpus 1 --memory 512M --user 65534:65534 --rm`; `INPUT` mounted read-only and `results/a29-01` separately writable. The exact combined log, raw result, exit code, and before/after container inventory are retained. WSLc warned that host cgroup/swap controls are unsupported.

Run the independent audit only:

```powershell
python audit.py
```
