# Private packet custody

The private raw packets are retained on the authorized Windows PC under the workspace's `private-packets/` directory. These identifiers are stable packet names; no per-user absolute path is published here. Each packet's `SHA256SUMS` covers all packet files except the manifest itself.

| Attempt | Private packet | File count | SHA-256 of `SHA256SUMS` |
|---|---|---:|---|
| R01 startup/observation stop | `win32_freedoom2_map01_ui_smoke_20261026_r01` | 19 | `f2f06dd660a97f3d7f08f1ece100639ee9c5350fbd55e4c73c6274028a82d5d0` |
| R02 direct MAP01 action | `win32_freedoom_map01_direct_launch_20261026_r02` | 16 | `bf2f7841e5c68e01f1acb36337a44978ae1758279011a5c02d2f33d7df075aaf` |
| R03 dense release horizon | `win32_freedoom_release_horizon_20261026_r03` | 26 | `7ac4aae73a486ad8e742ad2789af15ee541bc4891c6de05c9cfab9a7dc2680ed` |
| R04 zero-input control setup stop | `win32_freedoom_idle_control_20261026_r04` | 5 | `58e2595f1343c4fe86978ad75b88c256aeff310990b8e207b8465b9fd44050e2` |
| R05 zero-input control | `win32_freedoom_idle_control_20261026_r05` | 16 | `e5a3f9761dd24b119ea40f629c6fefef5bfc965b2cda9f0c6c7945a1980da7c0` |

The R02 timing correction is additive; its original raw records are unchanged. R03's `raw/TIMING_AUDIT.json` independently recomputes sample offsets, pixel deltas and raw-image SHA-256 values from the retained images. R05's `raw/AUDIT.json` independently recomputes the four sample hashes and RGB differences, and verifies zero runtime input calls/emissions. R04 preserves its pre-capture missing-dependency failure and zero-input cleanup. Each `CLEANUP.json` records test-owned process/window absence checks. These manifests establish local byte custody, not independent public access to the private images or host state.
