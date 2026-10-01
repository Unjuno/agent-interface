# Issue #3764 — server/client XKB map diagnostic

Allocation: `issue3733-german-xkb-map-diagnostic-formal-01`.

## H / T / D / C / U

- **H:** Determine whether the pinned OrbStack Xvfb server's effective XKB dump and a newly connected Python-Xlib client's full core map agree after `setxkbmap -layout de`, or whether the previously observed German server query/dump with unchanged Xlib core-map fingerprint is a persistent disagreement. A fresh US server is the control.
- **T:** On three separate fresh Xvfb servers, capture baseline `setxkbmap -query`, `xkbcomp -xkb`, and two sequential new Python-Xlib `get_keyboard_mapping` connections; apply German once; recapture the same channels and key-symbol placements (Y/Z/equal/asterisk). Run one fresh US control with baseline and after captures but no layout mutation. Retain exact stdout/stderr, full core maps, fingerprints, process identity/cleanup and file hashes. The runner does not import Agent Interface candidate code and sends no XTEST/native input.
- **D:** `PASS_DIAGNOSTIC` only when all four rows complete, both fresh Xlib connections agree at each phase, server query matches requested layout, and XKB server-dump changed/unchanged status agrees with the direct core-map changed/unchanged status on every German row. Any method disagreement is a truthful `STOP_SERVER_CLIENT_MAP_DISAGREEMENT`, not a candidate PASS/FAIL. Tool/startup/query/cleanup/integrity setup failure is STOP. No retry under this allocation.
- **C:** Exact pinned image `agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, linux/arm64, Python 3.12.3, Xvfb/XKB/XTEST image capabilities as installed (XTEST is not invoked), `--network none`, read-only root/source, private Xvfb only, isolated writable output, 1 CPU/512 MiB/32 PID cap, no capabilities and no-new-privileges. No host display, candidate backend, GUI app, key/button/text event, model, network or system package change. The image has no `xmodmap`; use direct Xlib core mapping plus `xkbcomp` server dump and `setxkbmap -query` instead. The image entrypoint is `python3`, not `python`; an initial tool-path probe failed before process start and was corrected as a construction STOP, not formal evidence.
- **U:** Private Xvfb server/client map state only. No German text delivery, candidate backend correctness, real application effect, keyboard hardware, GUI, or product claim.

## Construction evidence

In a network-disabled pinned container with source mounted read-only, three synthetic/parser construction tests passed. They cover the layout-query parser, synthetic keycode/level symbol extraction, and canonical/sensitive map fingerprint. These tests start no X server and send no events. Exact hashes are in `FREEZE.json`.

## Formal run protocol

Commit and preregister the freeze before one invocation. Recheck main/image/script hashes, assert a fresh empty output directory, mount source read-only and output separately. Preserve the first formal stdout/exit record separately from all later audit commands. Audit evidence read-only and write to a separate result mount. Any setup/audit issue after the allocation runs is retained as such; do not rerun the diagnostic.
