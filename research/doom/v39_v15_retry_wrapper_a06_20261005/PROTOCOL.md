# A06: retry-owner composition through the V15 release-batch wrapper

Successor to A05, which stopped before candidate start because its pinned Python 3.11.9 linux/arm64 image was absent locally. A06 changes only the container runtime identity to the already-cached Python 3.12.15 linux/amd64 image; the frozen candidate, source snapshots, hypothesis, fake-server disturbance, auditor, and decision gate are unchanged. A05 remains STOP and is not rerun.

## H/T/D/C/U
- **H:** The current-main release-batch backend v1 and transition-owner v4/v3 composed around PR #7974's input-owner v12 recover a dropped first key-up and publish a verified empty two-key batch; keymap sampling is inserted between explicit UP injections, violating A04's no-inter-UP-query invariant.
- **T:** One FakeXlib execution through the actual release-batch backend, using DOWN(a), DOWN(b), UP(b), UP(a), with only the first keycode 31 KeyRelease dropped. No real X server, game, model, GUI, or OS input.
- **D:** Retain raw ordered trace, release rows, owner receipts/attempts, post-batch state, and independent audit. PASS requires every check in audit.py, including successful retry, complete verified release, and an observed keymap query between first and last UP injections. Otherwise retain FAIL/STOP without rerun.
- **C:** Candidate/audit/wrapper dependencies from current main `6a2826d391b77496b69752609a6f07b6971b4b6f`; input-owner overlay from PR #7974 `4d1cb80a5018cc4f392146eae880d98c33a84bde`; local WSLc image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (Python 3.12.15, linux/amd64), network none, one CPU, configured 512 MiB memory and 32 MiB tmpfs, with only the candidate bundle bind-mounted read-only. WSLc exposes no read-only-root option in its run help. Preflight reported that the kernel does not support swap limits or cgroup is not mounted; memory limit is without swap and enforcement is not inferred from flags.
- **U:** Synthetic owner/wrapper composition and call-order evidence only. Not V15 session startup, actual X11, physical/application state, V39 threat exposure, useful task feedback, latency, real-environment recovery, or live allocation evidence. A06 does not supersede A04.

## One-shot gate
Run runner.py once after source hashes validate and local image preflight passes. Preserve candidate and auditor output. No pull, no live resource use, and no rerun after candidate start.
