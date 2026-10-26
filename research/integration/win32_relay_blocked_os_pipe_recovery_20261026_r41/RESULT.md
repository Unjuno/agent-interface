# R41 first outcome: relay startup failure

- Attempt: `win32-public-relay-os-pipe-r41-20261026`
- Source: origin/main merge `51f4652e59acdfcf3709916340f584ab083a7a82`; checkout HEAD at preregistration `bc50f10998bb96a31d14e6a8f0fcba01255bf1d2`.
- Classification: `FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED` (harness/setup failure; no recovery observation).
- Preflight: newly owned fixture HWND `4853246`, its target generation was recorded, fixture foreground matched, and SHIFT was independently up. Fixture exited 0; original Codex foreground HWND `10486926` was restored.
- Cause: relay child exited while constructing the server with `ValueError: supervised-win32 test factories must be injected as a pair`. The runner then raised `KeyError: 1` because no observation response arrived. It did not reach dispatch; no input was sent, no pipe pressure was created, and no cancellation/recovery gate was measured.
- Evidence: [`run/result.json`](run/result.json), [`run/relay-stderr.bin`](run/relay-stderr.bin), [`run/fixture/events.jsonl`](run/fixture/events.jsonl), [`run/SHA256SUMS`](run/SHA256SUMS). Raw is local-only.
- Integrity: frozen preregistration and source hashes are in [`PRETRIAL_SHA256SUMS`](PRETRIAL_SHA256SUMS); the runner/child and listed source modules were byte-hash checked before the attempt. Result and raw files are covered by the run checksum manifest.
- Scope: synthetic owned fixture only. No GZDoom/MAP01, WSLc, Docker, MCP subprocess transport, task effect, efficiency, or reliability evidence.
- Follow-up: correct the paired factory wiring only in a new attempt packet and run ID; do not replay R41.
