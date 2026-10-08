# V39 import-only runtime preflight (A01)

The 2026-10-09 A03 allocation stopped before app-server/game startup because the guest Python environment lacked Pillow while importing `map01_overlap_controller_v39`. The repository's broad `research/requirements.txt` already declares Pillow, so this is a guest-runtime assembly gap, not a controller-source defect. A03 remains preserved as STOP and is not retried or modified.

This small successor utility checks the exact failure boundary before any app-server request, game initialization, model request, or physical input. It requires the expected Pillow version as an argument, checks the installed distribution version, then imports the pinned V39 controller module. It does not initialize ViZDoom or call the controller's runtime entry point. Run it inside the fully assembled guest environment, after placing the frozen source tree, and before starting any runner:

```sh
python research/doom/v39_live_import_preflight_a01_20261009/import_preflight.py <Pillow-version-from-FREEZE>
```

Exit 0 / `IMPORT_ONLY_READY` means only that the pinned controller import works in that interpreter. A missing module, distribution, or version mismatch returns exit 20 / `STOP_IMPORT_PREFLIGHT`. This is setup readiness only and does not authorize or count as the live allocation.

## Local reproducer

At parent main `23d1807ffad8359e0f89421ee2b9bf5783c9d5f4`, a clean venv with no Pillow reproduced the exact `ModuleNotFoundError: No module named 'PIL'` at the V39 controller import. The bundled Python 3.12.14 runtime with Pillow 12.3.0 passed the import-only gate. Both raw outputs and exact commands are retained in this directory. This is a local environment-boundary reproduction, not a guest/VM validation or live result.
