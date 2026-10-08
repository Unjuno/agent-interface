# Archived O3/G2 release-edge telemetry alternate

**Historical alternate source. Not an update to the current InputOwner v11 or DOOM release backend.**

Source commit: `fe16ee248f9a0f0d6b624094417bcdd362699685` on `orchestrator/O3/G2-release-telemetry-f678afa8`; parent/base: `f678afa8eb7b1db1da7cfd9a15ff65d4c146d74d`. Source integration proposal: PR #697. Prior semantic reconciliation: merged PR #268.

## Why this must not replace current code

PR #268 already retained the design note while explicitly rejecting in-place replacement of the three conflicting historical code files. Direct source inspection confirms the difference: this alternate instruments only `up` and emits `input_release_ack` with `release_requested_ns`/`release_ack_ns`; main's retained InputOwner v11 also instruments `button_up` and emits `input_release_rpc` with an explicit transition interval. Replacing the current file would change the receipt interface and remove button-release instrumentation.

The historical alternate remains useful for understanding the raced/superseded release-attribution design. It is preserved here as exact original blobs, not silently merged into the current import paths. No existing runtime, research implementation, workflow or release ref is changed by this archive.

## Evidence boundary

The original note reports 11/11 deterministic offline regressions in its historical container. It explicitly reports no live X11 input episode for that gate. This maintenance archive does not rerun the old allocation, establish physical-transition timing, establish application consumption, or promote production readiness. The legacy test assumes the three Python files are colocated; the archive preserves that arrangement, but this is not an installed runtime entry point. Any reconstruction still requires compatible dependencies and explicit isolation.

## Exact identity and original locations

| Archived file | Original path | Original Git blob SHA-1 |
| --- | --- | --- |
| input_owner_v11.py | research/live_control/input_owner_v11.py | 4d1b6b02d4bf4babefd06eea23341cb153ae2f9a |
| doom_typed_release_backend_v2.py | research/doom/doom_typed_release_backend_v2.py | 1b3e59ca6aa2028c21348cebdcd0b0423bf7c0b6 |
| test_doom_typed_release_backend_v2.py | research/doom/test_doom_typed_release_backend_v2.py | 0207e9b4e401387f6b3755b838b2f5336c8c90c7 |
| RELEASE_EDGE_TELEMETRY_V1.md | research/orchestration/o3-g2/RELEASE_EDGE_TELEMETRY_V1.md | 4aef47b8506bb9c8c7db737e1b28d41edf91965b |

The design note already exists at its original main path through #268; its copy here binds the alternate source to its own historical description. This README is the only new authored content. Keep historical code immutable and use a new version/allocation for future changes.
