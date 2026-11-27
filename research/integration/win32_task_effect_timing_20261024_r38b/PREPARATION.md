# R38 — timestamped task-effect observation

One native-Windows fixture-only task will measure the save-effect write interval and the configured oracle's observation time on the same host monotonic clock. The instrumented fixture is a packet-local copy; historical runtime source and R37 packets remain unchanged.

One observation, one validation, one dispatch, one exact-call result path, and one oracle call are permitted. No retry or replay. Before input, preflight must confirm the exact source commit, frozen packet hashes, native Windows, Python/MCP dependencies, a fresh empty run folder, no active fixture window, and an unchanged tracked source tree. A failed preflight means no input.

A successful oracle receipt must bind exact call, operation, target generation and oracle ID; the effect JSON and exactly one timestamped save event must match the preregistered token. The fixture records start/end around the effect-file write. The oracle samples its observation time before reading the exact effect and event. The resulting latency is an interval; it does not identify the interior physical transition more precisely. Cleanup must exit the owned fixture and restore the previous foreground window.

No WSLc or Docker use. This is one diagnostic timing sample, not matched efficiency, reliability, MAP01, or real-application evidence.

The preceding R38 attempt stopped before any fixture or input because its preflight dependency diagnostic raised `AttributeError` after importing Pillow. That exact failed preflight is preserved as the predecessor. R38b uses a fresh attempt ID, token, oracle ID and output folder; it does not rerun R38.
