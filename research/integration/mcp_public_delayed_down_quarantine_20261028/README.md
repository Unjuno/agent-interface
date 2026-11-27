# Public MCP delayed-input quarantine composition (2026-10-28)

## Question

Does the opt-in Win32 late-input horizon remain connected through the public MCP route when an old input reappears after a neutral readback, and does the owner keep the operation quarantined?

## Setup

`SupervisedBackendCompositionTests.test_public_cancel_keeps_old_generation_quarantined_after_delayed_down` runs the public `create_server` path in `supervised-win32` mode with an actual `OperationCancellationSupervisor` configured for a 100 ms late-input horizon. The test admits one CTRL-down program, blocks its producer after the inert fake API accepts the DOWN, then cancels through public `interface_cancel`. The recovery helper sends UP. The observer returns one neutral sample; only after the supervisor requests a second observation does the helper inject the old CTRL-down and return a non-neutral sample.

The trace retains producer retirement, recovery UP, the delayed DOWN, and repeated observer requests. The test reads the terminal record through public `interface_results`.

## Result

The public cancellation record reaches `unknown`; it does not claim release confirmation or task success and denies replay. The operation owner refuses admission of a next generation. This covers a composed synthetic schedule that the standalone horizon test did not connect to the public route.

Focused command ran 1/1 in normal Python and 1/1 under `-O`. The full `runtime.cli_v1.test_mcp_supervised_backend_composition` module ran 4/4 in each mode. All four captured exit-code files contain 0. Exact stdout/stderr, commands, and exit codes are retained in this packet. Runtime: Windows CPython 3.11.9. Source checkout HEAD: `0897421623612f13d83c1994ab06dd21408a2855`; the source hashes below pin the uncommitted composed test and relevant runtime files.

## Scope

`FakeUser32` supplies state and records input calls. This does not establish a real Windows `SendInput` late-delivery trace, continuous neutral state between samples, a hard release deadline, live GUI/task effect, or MAP01 completion. The public configuration defaults to a zero horizon; native evidence is still required before selecting a finite production default. No Docker or WSLc runtime was used.

Reproduce with the four commands listed in `COMMANDS.txt`. `SHA256SUMS` covers packet files except itself, plus the composed test, route/owner/supervisor/backend implementation, fake API harness, and architecture note.
