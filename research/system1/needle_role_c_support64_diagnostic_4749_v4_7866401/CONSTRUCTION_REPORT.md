# Zero-training construction result

Pinned Docker image: `needle-pilot05:local`, `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, linux/amd64. Network disabled, root/source read-only, 1 CPU, 2 GiB, 64 PIDs. No output volume mounted and no optimizer code called.

Command:

```powershell
docker run --rm --pull=never --network none --read-only --cpus=1 --memory=2g --pids-limit=64 --mount "type=bind,source=<scratch>\needle-role-c-support64-diagnostic-4853-v1,target=/src,readonly" -e NEEDLE_SEED=7866401 -e NEEDLE_OUTPUT=/unused --entrypoint python needle-pilot05:local /src/construction_test.py
```

Stdout: `CONSTRUCTION_PASS seed=7866401 prefix_exact=True sentinel_bytes=True corrupted_prefix_rejected=True optimizer_updates=0`.

The image emits PyTorch's expected optional NumPy-initialization warning because NumPy is not installed; this construction check uses only PyTorch and passed. First attempt failed the exact runner Git-blob check due to an extra local terminal blank line; that preflight failure is retained in `CONSTRUCTION_FAILURES.md`. No training occurred on either attempt.

