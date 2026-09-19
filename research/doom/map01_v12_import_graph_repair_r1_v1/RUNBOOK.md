# R1 import-only smoke

Run from a clean checkout of this branch:

```bash
python research/doom/map01_v12_import_graph_repair_r1_v1/import_smoke.py \
  --repo . --out /tmp/map01-v12-import-smoke
```

The gate compiles the retained `research/live_control/*.py` files and imports
`session_v8` with only `research/live_control` providing its legacy bare
module names. It verifies that `Backend` comes from live-control v8, its
predecessor comes from live-control v7, the suite symbol exists, the DOOM
entrypoint was not loaded, and retained source hashes are recorded.

This is a construction/import result only. It must not be promoted to MAP01
scientific, GUI, model, latency, gameplay, or runtime correctness evidence.
