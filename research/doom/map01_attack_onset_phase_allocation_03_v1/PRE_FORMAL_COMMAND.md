# One-shot local Docker command (not yet invoked)

The image is local and frozen by ID in `FREEZE.json`. Run from the repository root after the formal gate is authorized. `results/formal/` must not exist before the invocation; the runner itself creates it with `exist_ok=False`.

```powershell
$exp = Join-Path (Get-Location) 'research/doom/map01_attack_onset_phase_allocation_03_v1'
docker run --rm --network none --read-only --tmpfs /tmp:rw,size=2g `
  --cpus 4 --memory 8g --pids-limit 128 `
  -e MAP01_SOURCE_ROOT=/tmp/runtime-source `
  -e MAP01_V12_ROOT=/exp/dependencies/v12 `
  -e MAP01_EXPERIMENT_ROOT=/exp/source `
  -v "${exp}:/exp:ro" -v "${exp}/results:/evidence" `
  map01-attack-onset-phase-a3:20260927-r1 sh -lc `
  'mkdir -p /tmp/runtime-source && tar -xzf /exp/inputs/runtime-source.tar.gz -C /tmp/runtime-source && python /exp/source/formal_runner.py --source /tmp/runtime-source --v12 /exp/dependencies/v12 --out /evidence/formal'
```

The image entrypoint starts private Xvfb `:99` and Openbox with TCP disabled. The container has no network, a read-only root and source mounts, bounded `/tmp`, and only the evidence parent is writable. One `formal_runner.py` invocation contains the frozen eight-session counterbalanced schedule; do not retry or resume a partial invocation. The existing Ollama container is not part of this experiment and must not be stopped or modified.
