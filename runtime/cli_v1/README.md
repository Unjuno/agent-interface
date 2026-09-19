# Unified runtime CLI/API v1

This is the model/vendor-neutral local entry point over promoted Agent Interface backends.

```bash
python -m runtime.cli_v1 doctor
python -m runtime.cli_v1 dispatch \
  --program program.json \
  --targets targets.json \
  --current-observation-seq 7 \
  --current-binding-revision 3
```

`targets.json` remains explicit native target identity:
- Linux/X11: X11 window IDs;
- Windows: HWNDs;
- macOS: PIDs.

The CLI does not discover targets, rewrite leases/freshness, retry automatically, or grant authority. `doctor` is diagnostic only. `dispatch` delegates to `selector_v1`, then the promoted backend session, then `runtime/core_v1` admission.

Each `dispatch` owns its one-shot session and closes its native backend connection
when that backend exposes `close`, including after refusal or an execution error.
A close failure returns `runtime_failed` with `cleanup_error`, preserving any
execution result or original error. The CLI consequently exits nonzero. This
connection cleanup does not replace the backend's input-release checks.

Wayland-only Linux currently fails closed because no Wayland backend has been promoted. Linux/X11 requires the existing `python-xlib` dependency used by `x11-v1`.
