# Issue #5752 allocation-04 recovery — pre-candidate STOP, not a result

This is an evidence-preservation integration of the exact frozen allocation-04 package. It does not resume, retry, or adjudicate the GPU HUD hypothesis.

## H / T / D / C / U

- **H:** the frozen issue hypothesis concerned exact CPU/CUDA HUD-output parity and a scoped speed threshold on retained Freedoom frames. Allocation-04 did not test it.
- **T:** allocation `GPU-HUD-CUDA-5752-20261001-04`, reserved for 2026-10-01 08:05–08:15 UTC, stopped at 07:42:01 UTC before the reserved window. Candidate=0, CUDA workload=0, auditor=0; no raw scientific result.
- **D:** `STOP_INSUFFICIENT_DISK_SPACE`; scientific outcome `NOT_EVALUATED`. The typed gate is a resource/provenance STOP, not a CUDA, parity, speed, HUD, gameplay, or MAP01 result.
- **C:** C: had 0 free bytes at three checks against the frozen 67,108,864-byte durable-output reserve. No alternate writable volume was available. No cleanup, file staging, process termination, container/model use, or retry occurred. The local WAD identity was read-only checked and matched the freeze; no input was staged.
- **U:** CPU/CUDA parity, CUDA latency, live HUD recognition, gameplay, MAP01 survival/exit, and any useful control effect remain unobserved for allocation-04.

## Immutable source and separate later allocation

- Original source branch tip: `31cbd21a23d32f3e583d254aaac149666aeea758` (`research/gpu-hud-cuda-5752-20261001-04`). The twelve original files in this directory are preserved byte-for-byte.
- Exact STOP receipt: `STOP.json`; it records all three zero-byte observations, the 64 MiB reserve, early release, and `retry: false`.
- Later A05 is a distinct allocation and package, merged through PR #5979. Do not transfer A05's historical claim to A04. The Issue's later static review also records integrity and unmatched timing-endpoint HOLDs for A05; none of this changes A04's terminal STOP.
- No candidate, CUDA kernel/workload, auditor, model, container, game, GUI, or input was run during this recovery.

Issue #5752 remains open for broader work. Any future execution needs a fresh, owner-bound allocation and current-main/source/resource gates; this recovery does not authorize one.
