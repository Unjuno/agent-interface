# Win32 supervised caller R54–R55 public result summary

R54 and R55 are two consecutive paired native-Windows fixture attempts on the user-authorized PC. Both used the public stdio MCP caller and source commit `0f6464adbb4d2c7331b8aae71ee148a638c0ae79`. The six relevant Win32 runtime files recorded by the frozen source hashes have no diff from that commit to current main `291b8c8c5880c8de4d8deaeee1ab0d5125c45c29`.

Each frozen preflight passed, each strict phase-1 release audit passed 11/11, and each combined audit returned `PASS_SCOPED` 14/14. Phase 1 issued one public dispatch and one cancellation while a Q-up callback remained held. Recovery returned Q-up and an independent same-generation state series observed it while the callback was still held. Phase 2 began only after that release gate and used a new fixture process, target generation, session, call and operation. The standard task verifier returned `status=verified, task_success=true`; exact fixture effect, neutral release/readback, cleanup and foreground restoration passed. The initial action receipt continues to leave runtime `task_success` null.

| Attempt | Callback held after cancel | Recovery Q-up returned | Independent Q-up observed | Eligible same-generation Q-up samples | SendInput entry → click WndProc | SendInput entry → save handler | SendInput entry → effect-file write return | Write return → oracle read start |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| R54 | 1,404.9483 ms | +619.7598 ms | +621.229 ms | 75 | 9.2367 ms | 1.3844 ms | 1.7620 ms | 238.8358 ms |
| R55 | 1,402.8097 ms | +632.4875 ms | +638.4985 ms | 73 | 19.3173 ms | 2.0544 ms | 2.4658 ms | 210.7989 ms |

All timing values use same-host `time.perf_counter_ns` software instrumentation. They measure API and fixture/file receipt points, not physical input-to-display latency or durable storage. The effect-file write-return to oracle-read-start interval differs from the write-return to oracle-observation interval reported in each local result; both endpoints are preserved in the original audit and are intentionally not conflated here.

R54's phase-2 activation API returned successfully, then its local receipt helper raised a path-construction `TypeError`. The exact window activation was manually recorded with the helper error retained, and the runner independently verified foreground HWND and owner PID before dispatch. R55 repaired and preflighted that recorder path. Neither attempt replayed input.

This is scoped evidence for the native Windows fixture only. It does not establish WSLc behavior, MAP01 or real-application transfer, matched efficiency, physical input timing, or a broad reliability estimate. R54/R55 phase-1 fixture effects occurred before cancellation and are not described as post-recovery task success; task success comes from the separate fresh-generation phase 2.

The full local raw packets remain in the experiment workspace and were not copied here because they contain machine paths, process/window identifiers and local session metadata. Their 71-entry SHA-256 manifests were verified against every local file before this summary was prepared. `PUBLICATION_CUSTODY.json` records the manifest digests and the scope of this redacted publication; it does not claim the private raw is independently available to public reviewers.
