# Portable runtime v2 distribution — latest-main check

## Archive source pin: `038486e100ceeda578daa442388f686fd2eedc2f`

On 2026-11-21, rebuilt the portable `agent-interface-runtime.pyz` from exact
main `038486e100ceeda578daa442388f686fd2eedc2f` using Windows Python
3.13.14. The archive is 784,932 bytes with SHA-256
`b164c77e0e6b1f9f13b4aabfe61296710b2acdc5fc82c2c5afddd042356f4e40`. Its
external manifest and embedded `BUILD.json` pin this revision. The archive has
69 entries, including 64 Git-managed source files. A second build produced
byte-identical output.

The preceding current-main packet pinned `b049316731b0c8ddf47ed22c3df28c37c9f5d396`.
All 64 Git-managed source-entry paths and SHA-256 values match the new build;
only the source revision pin changed. The earlier archive and base-381a packet
remain in the packet's Git history.

After this archive was built, main advanced to `cc722677cd51035339d4182103223ba76d4dd154`.
All 64 source file hashes in the archive manifest match the Git blobs at that
current main as well as the preceding `b049316` and `381a21a` packets.

The full `runtime/distribution_v2` suite passes 21/21 normally and 21/21 under
`-O` on Windows 11 Pro build 26300 with Python 3.13.14 (31.060 s and 29.493 s).
The same suite passes 21/21 normally and 21/21 under `-O` in Ubuntu WSL with
Python 3.12.3 (175.236 s and 158.625 s). From fresh working directories
outside the checkout, the archive's `doctor` and `validate --help` both exit 0
on Windows and WSL. The Windows doctor reports Win32 available; WSL reports
X11 available. Both report `side_effect_authority=false`.

The WSL test run used Python `3.12.3`, Git `2.43.0`, and an Ubuntu WSL2 kernel.
`python-xlib` was present; Pillow was absent. No packages were downloaded.

Conditions, exact source manifest, executable, logs, smoke outputs and checksums
are retained in this directory. The ignored local output folder contains the
independent repeat-build artifact and additional raw files.

## Scope

This qualifies deterministic archive construction and basic command startup on
Windows and Ubuntu WSL. It does not establish a live X11/Win32 target, native
input, application effect, target permission flow, macOS startup,
provider/task behavior, a public release, or complete research-preview
graduation.
