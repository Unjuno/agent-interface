# Reproduction commands

The scored run used a single fresh Docker process with the fixed image ID from `FREEZE.json`; source, engine and model mounts were read-only, `/tmp` was a 64 MiB tmpfs, and only `/out` was writable.

```powershell
docker run --rm --network none --read-only --memory=2g --cpus=2 --pids-limit=64 `
  --tmpfs /tmp:rw,nosuid,nodev,size=64m `
  -e NEEDLE3_LIB_PATH=/opt/engine/libneedle.so -e HF_HUB_OFFLINE=1 `
  -e HF_HOME=/tmp/hf-empty -e NEEDLE_TELEMETRY=0 -e DO_NOT_TRACK=1 `
  -e PYTHONDONTWRITEBYTECODE=1 `
  -v <experiment-source>:/opt/experiment:ro `
  -v <runtime-cache>/native:/opt/engine:ro `
  -v <pinned-model-file>:/opt/model/needle3.cact:ro `
  -v <formal-output>:/out:rw `
  cactus-needle3-action:v1-frozen --model /opt/model/needle3.cact --out /out/raw.json
```

The independent audit ran in a separate network-disabled, read-only container process against the raw JSON, frozen manifest, mounted source directory, and exact local image ID. The two pre-run failures are retained and described separately; neither loaded the model or evaluated a case.
