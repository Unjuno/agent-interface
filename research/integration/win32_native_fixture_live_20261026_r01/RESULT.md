# Native Win32 fixture UI trial — 2026-10-26

**Disposition: `PASS_SCOPED` (one sample; independent local audit 9/9).** On the exact current-main source tree, one owned Win32 fixture window received a click, the text `office`, and Ctrl+S through `Win32RuntimeSession`. The fixture's separate effect file recorded the frozen expected value `{ "saved": true, "text": "office", "clicked": true }`, and its event log showed ready → click → six characters → save.

The dispatch returned `completed`, captured one 300×140 observation (168,000 bytes; SHA-256 `e25e38b4c54e243a66a2ed482627d8ebd4b7b7f43740c1c9b3c75d570ca6c8cc`), and returned one verified terminal-release receipt with no held or unknown keys/buttons. The measured dispatch interval was 167.5589 ms. It is a single software-timed sample, not a physical input-to-display latency estimate.

The release witness was bound to one fixture window and process on the active desktop. The exact fixture process then exited with code 0, its HWND became invalid, and no matching window remained. Exact conditions are in [`PREREGISTRATION.json`](PREREGISTRATION.json); source hashes and tree identity are in [`SOURCE_FREEZE.json`](SOURCE_FREEZE.json); local raw custody is represented by [`PRIVATE_CUSTODY.json`](PRIVATE_CUSTODY.json).

This advances native Windows fixture input/effect/release evidence only. It does not qualify MAP01 or a real game, the standard public MCP caller, target-generation binding, blocked-I/O cancellation, bounded recovery, broad reliability, or matched efficiency. No WSLc allocation, Docker operation, model/provider call, or unrelated app window was used. The observation pixels were not retained; only dimensions and digest are public.
