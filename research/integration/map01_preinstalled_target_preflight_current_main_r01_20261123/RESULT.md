# MAP01 target availability preflight R01

## Frozen scope

- Source baseline: current `origin/main` `e67ca18cd3e8a5ccb0288b41ed2f5d0bb94bc6c7`.
- Question: is a preinstalled GZDoom executable discoverable in common Windows install paths, `PATH`, the process table, or uninstall registry entries?
- Method: run `preflight.ps1` once; read-only inspection only. No executable was launched, no WAD or runtime was installed/downloaded, and no input was sent.
- Search bounds: six explicit executable paths listed in `raw.json`, command lookup, running-process name, and three Windows uninstall-registry hives. This is not a complete disk search and does not establish whether assets exist elsewhere.
- Host: Windows `10.0.26300.0`, captured at `2026-11-23T06:39:08.6337621Z`.

## Result

No candidate path existed; command lookup, process list, and uninstall-registry match list were empty. No target was available through the inspected locations. The MAP01 live threat-exposure experiment remains blocked at target discovery; this preflight is not a control, task-effect, or runtime acceptance result.

An exploratory recursive filename scan over broad user/program folders was stopped after it produced no output for roughly one minute. It is excluded from this result; only the bounded checks in `preflight.ps1` and `raw.json` are counted.

## Retained evidence

- `preflight.ps1`: exact bounded inspection command.
- `raw.json`: unedited JSON output from that command.
- `SHA256SUMS.txt`: hashes for both files and this result.

The next valid live step requires an exact preinstalled target path plus its intended IWAD/map assets. Do not treat user permission to use the PC as evidence that those assets are present.
