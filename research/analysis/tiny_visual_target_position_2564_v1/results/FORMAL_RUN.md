# Formal local Docker run receipt

- Allocation: `tiny-visual-target-position-support-2564-20260927-01`
- Invocation count: exactly one; container image was addressed by pinned image ID, with `--pull never`.
- Exit code: `0`; `stdout.log` contains the JSON receipt below; `stderr.log` was empty (0 bytes).
- Container constraints: network none; CPU 1; memory 2 GiB; PIDs 64; cap-drop ALL; no-new-privileges; read-only root filesystem; 64 MiB noexec/nosuid `/tmp`; source bind read-only; output only to a new empty host directory; GPU not requested.
- Exact command template: see `formal_command` in the preregistered `FREEZE.json`.
- Local output: `work/tiny_visual_target_position_2564_v1_formal_output_20260927/`.

```json
{
  "allocation": "tiny-visual-target-position-support-2564-20260927-01",
  "external_model_api_requests": 0,
  "fits": 10,
  "formal_seeds": [8962800, 8962900, 8963000, 8963100, 8963200],
  "host_gui_or_authority": false,
  "image_id": "sha256:ba509e8a38d311c07539c49a7a2970b6f19869de42b8008be07a85568e2c9824",
  "local_model_fits": 10,
  "network_expected": "none",
  "numpy": "1.24.2",
  "platform": "Linux-6.6.114.1-microsoft-standard-WSL2-x86_64-with-glibc2.36",
  "prediction_rows": 2400,
  "python": "3.11.2",
  "training_wall_seconds": 5.730326241000512
}
```

