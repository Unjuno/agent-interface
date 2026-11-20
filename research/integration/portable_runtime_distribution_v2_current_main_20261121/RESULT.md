# Portable runtime v2 distribution — current main `b049316`

## Result

The distribution builder produced `agent-interface-runtime.pyz` from exact current main `b049316731b0c8ddf47ed22c3df28c37c9f5d396`. The archive is 784,932 bytes with SHA-256 `b5d6a72aba1fe7ecd9238cf37432f8faf2f44279c031a8d239bc5c138933efa3`; the external manifest and embedded `BUILD.json` both identify this source revision. The runtime source tree is byte-for-byte unchanged from the previous base `381a21a`; this rebuild updates the pinned revision and preserves the current-main claim.

On Windows 11 Pro build 26300 with Python 3.13.14, `runtime/distribution_v2` passed 21/21 normally (42.994 s) and 21/21 under `-O` (37.404 s). From a fresh working directory outside the checkout, the archive's `doctor` and `validate --help` both exited 0. `doctor` reported the Win32 backend available and `side_effect_authority=false`.

The previous base-381a packet is retained under `base_main_381a21a/`.

## Scope

This qualifies deterministic archive construction and basic command startup on this Windows host. It does not establish native input, live application effect, target permission flow, Linux/WSL or macOS startup, provider/task behavior, a public release, or complete research-preview graduation.
