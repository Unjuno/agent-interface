# Construction and candidate commands — Issue #6354

Construction test (executed; CPU-only, no GPU exposed):

```powershell
wslc run --rm --pull never --network none --cpus 1 --memory 2g --user 65534:65534 `
  --mount "type=bind,source=<absolute-source-dir>,target=/src,readonly" `
  --workdir /tmp pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime `
  python -B -m unittest discover -v -s /src -p 'test_*.py'
```

Formal candidate (stored for reproducibility; **not authorized or executed**):

```powershell
wslc run --rm --pull never --network none --gpus all --cpus 1 --memory 2g `
  --user 65534:65534 `
  --mount "type=bind,source=<absolute-source-dir>,target=/src,readonly" `
  --mount "type=bind,source=<absolute-frozen-input-dir>,target=/input,readonly" `
  --mount "type=bind,source=<fresh-empty-output-dir>,target=/out" `
  --workdir /tmp pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime `
  python -B /src/candidate.py --dataset /input/dataset.json `
  --freeze /src/FREEZE.json --source-dir /src --output /out/candidate.json
```

The stored command is not a lease and must not be run until #5085 contains an exact owner/allocation/window grant and immediate gates pass. Rootfs read-only is not available in WSLc. Kernel reports swap/cgroup memory enforcement unavailable. The independent auditor must be a separate invocation with `--gpus` omitted and network disabled, only if the candidate exits 0.
