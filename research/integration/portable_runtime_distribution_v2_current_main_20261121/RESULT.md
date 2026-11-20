# Portable runtime v2 distribution — latest-main check

## Current source pin: `038486e100ceeda578daa442388f686fd2eedc2f`

On 2026-11-21, rebuilt the portable `agent-interface-runtime.pyz` from exact
current main `038486e100ceeda578daa442388f686fd2eedc2f` using Windows Python
3.13.14. The archive is 784,932 bytes with SHA-256
`b164c77e0e6b1f9f13b4aabfe61296710b2acdc5fc82c2c5afddd042356f4e40`. Its
external manifest and embedded `BUILD.json` pin this revision and enumerate 69
source entries. A second build produced byte-identical output.

The preceding current-main packet pinned `b049316731b0c8ddf47ed22c3df28c37c9f5d396`.
All 69 executable source-entry paths and SHA-256 values match the new build;
only the source revision pin changed. The earlier archive and base-381a packet
remain in the packet's Git history.

The full `runtime/distribution_v2` suite passes 21/21 normally and 21/21 under
`-O` on Windows 11 Pro build 26300 with Python 3.13.14 (31.060 s and 29.493 s).
From a fresh working directory outside the checkout, the archive's `doctor`
and `validate --help` both exit 0. `doctor` reports the Win32 backend available
with `side_effect_authority=false`.

Conditions, exact source manifest, executable, logs, smoke outputs and checksums
are retained in this directory. The ignored local output folder contains the
independent repeat-build artifact and additional raw files.

## Scope

This qualifies deterministic archive construction and basic command startup on
this Windows host. It does not establish native input, live application effect,
target permission flow, Linux/WSL or macOS startup, provider/task behavior, a
public release, or complete research-preview graduation.
