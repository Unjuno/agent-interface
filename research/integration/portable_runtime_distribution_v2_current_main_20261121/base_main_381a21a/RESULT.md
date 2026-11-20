# Portable runtime v2 distribution check — 2026-11-21

## Result

The distribution builder produced `agent-interface-runtime.pyz` from exact current main commit `381a21ace42891c2cd1e9cff3e231bec763ec2ba`. The committed archive is 784,932 bytes with SHA-256 `0b8ebae5976cb103621c61f94cf6aa086a22faa7ab802c4aa3848e5bec29b579`; the external manifest and embedded `BUILD.json` both pin that same source revision.

On Windows 11 Pro, Python 3.13.14, the full `runtime/distribution_v2` test suite passed 21/21 normally (29.988 s) and 21/21 with `-O` (32.811 s). The built archive then ran `doctor` and `validate --help` from a fresh directory outside the checkout; both exited 0. `doctor` reported the promoted Win32 backend available while `side_effect_authority=false`.

## Scope

This qualifies deterministic local archive construction and basic command startup on this host. It does not establish native input, live application effect, target permission flow, Linux/WSL or macOS startup, provider/task behavior, a public release, or the complete research-preview graduation gate.

The executable, source manifest, checksum, commands, conditions, raw test logs and outside-checkout command outputs are retained here.
