# GPU v6 transport readback results

Issue: #5455. This experiment validates the frozen PTY frame transport and GitHub file readback/ACK gate only. It makes no model inference calls and does not change Ollama configuration or installation.

## H/T/D/C/U

- H: A 13,449-byte UTF-8 JSON payload can be framed, committed to a fresh GitHub path, read back exactly, independently audited, and acknowledged.
- T: Run the frozen controller on new payload patterns, retaining every attempt and STOP.
- D: Exact bytes, expected frame count, readback SHA, independent JSON/length/SHA audit, and record commits read back before ACK.
- C: Frozen `row_frames.py` SHA256 `982034983289a7c2d5403eae355e148920d64b4fa6f2efa42bc6ba8fad490df1`; target payload 13,449 bytes; 561 data frames.
- U: Attempt 01's controller-side length mismatch cause remains unproven. This does not explain GPU fallback or establish inference behavior.

## Attempts

| Attempt | Outcome | Evidence |
|---|---|---|
| 01 | STOP before ACK: checker expected payload string length 13,438 instead of 13,435, despite successful GitHub readback. | `ATTEMPT01_STOP.md`, `ATTEMPT01_READBACK.json`, `POSTHOC_AUDIT.json` |
| 02 | STOP before ACK: PowerShell audit helper failed to parse apostrophes in command text. Post-hoc audit confirmed exact 13,449-byte payload. | `ATTEMPT02_STOP.md`, `ATTEMPT02_READBACK.json`, `ATTEMPT02_AUDIT.json` |
| 03 | PASS: immediate exact readback, independent audit, records verified before ACK, runner exit 0. No model calls. | `ATTEMPT03_RESULT.json`, `ATTEMPT03_READBACK.json`, `ATTEMPT03_AUDIT.json` |

Attempt 03: 8,468 ms to exact match; zero polls before match; 25,871 frame-file characters; 561 frames; readback blob SHA `f82186e45d8061cb60fdd7b3dd9db1902eaa8714`; payload SHA256 `25ccb782e28be8ae12fed4860d3a63653cee92172f64dced88c20b60d4ebf706`.

## GPU diagnosis context

In the GPU v5 pilot, Ollama returned HTTP 200 for one metadata-only request but reported 100% CPU; the RTX 3080 showed 0% utilization and 0 MiB. The read-only Ollama server log recorded bundled llama-server `--list-devices` crashes (`0xc0000005`) across CUDA 12/13, ROCm, and Vulkan probes, followed by CPU backend selection. A separate PyTorch CUDA matrix multiply succeeded on `cuda:0`, showing the hardware is available. This experiment did not repair or alter Ollama.

## Decision

Transport/readback gate: PASS on attempt 03, with two preserved controller STOPs. Reliable immediate readback was demonstrated, but attempt 01's mismatch cause is unknown. This is not GPU inference validation. Any new inference experiment needs a fresh successor with call-adjacent GPU enforcement and new preregistered seeds/source material.
