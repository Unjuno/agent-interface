# Supplemental Docker Desktop replay of the compiled-GUI mechanics probe

This is an additive local regression replay for #3311, not a new preregistered scientific allocation and not a replacement for any retained result. The run did not use GitHub Actions.

## Provenance

- Repository main at replay: `d5a8efa79b6f8462c8ce97fc19ca4ddd5875fe68`.
- The three mounted source files matched GitHub main's Git blob IDs before execution:
  - `research/live_control/compiled_gui_interface_v1.py`: `0c02db714127c8e0f770f9d4ac03699749899d2b`.
  - `research/live_control/probe_compiled_gui_interface_v1.py`: `ad43121baf654f0279447833a4d2ec90b16ecbe2`.
  - `research/live_control/adaptive_acquisition_caller_v1.py`: `9c2200699243822fb11947ca3b4050433ada4b9f`.
- The probe's own SHA-256 receipt reports runtime `93e47e1ab5ae3450bb4acf9ec9d21c9abc44ca93ffaee25683b22039d9a722ca`, probe `963e932dfeb3a94521d600c867319d96ad40883d7ed7c1ad14e9050f4304f18d`, and caller `cba8667e316bbd09403ef01f5c0b4b26a891ef3d8612ff63efa90276dfc6d37d`.
- Local Docker Desktop image: `python:3.12-slim-bookworm`, image ID `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, `linux/amd64`.

## Local command and outcome

The exact main probe was run once in a fresh disposable Docker container with network disabled, read-only root and source mounts, a fresh output-only bind mount, 0.25 CPU, 512 MiB memory, and 64 PIDs. It exited 0 and printed `compiled_gui_interface_v1_probe_passed`. Its report records 15 passing mechanics scenarios and all 4 invalid-interface controls rejected. The complete generated report is retained beside this file; SHA-256 `abef335e3949476510e083b5692e95edec5c971818c44ae9232d943fd315db36`.

The existing result directory in the source checkout was masked by the fresh output mount; it was not modified. The two pre-existing shared Docker containers were neither entered nor stopped.

## Scope

This is a deterministic test-double regression check only. It covers positive two-action continuation, stale/unknown/ambiguous/no-progress stops, effect failures, cancellation, transition budget, uncertain delivery, release failure, changed observation/surface, and cold/warm shared-caller mechanics.

It does **not** use X11, Chromium, model/provider calls, or user input. It measures no tokens, live task quality, latency benefit, or amortization. Do not pool it with #57's retained three-arm result or count it as #3311 acceptance. The #3311 six-task cold/warm/invalidation/repair comparison remains outstanding; formal-06 remains the separately retained live X11 mechanics result in PR #5007.

This replay used Docker Desktop's AMD64 Python 3.12 image, not formal-06's pinned OrbStack/Python 3.11 image. It verifies only this probe's Python 3.12 compatibility, not the pinned formal environment.
