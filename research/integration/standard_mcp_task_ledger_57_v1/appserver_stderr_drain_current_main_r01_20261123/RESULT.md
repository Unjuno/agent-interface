# App Server stderr drain current-main R01

**Disposition: PASS for the frozen local contract; HOLD for live gates.**

## Change

The current App Server client now drains stderr concurrently into a bounded raw-byte tail, tracks total bytes/EOF/read errors, and joins the stderr reader within the existing close deadline before closing its stream. The native protocol suite registers the new regression module.

## Frozen experiment

See [CONDITIONS.md](CONDITIONS.md) for source baseline, exact conditions, and deviations. The first test used a local child that emitted 1 MiB binary/non-UTF-8 stderr before answering one JSON-RPC request. Before repair it timed out at 2.022 s as predicted. The second test caught close blocking on a stream owned by a reader when an orphan inherited writer held the pipe; after the bounded reader join, close times out without closing the stream and succeeds after the writer exits. Raw RED and GREEN output is retained in `raw/`.

## Verification

- The two R01 tests: 2/2 pass in normal and 2/2 under `-O` (Windows CPython 3.13.14).
- Related App Server protocol modules: 81/81 pass in normal and 81/81 under `-O`; 10 platform skips per mode.
- Wider native protocol attempt: 713 tests, 31 errors, 3 failures, 17 skips. Most errors are existing POSIX-only tests run on Windows; the MCP relay test also lacks `mcp==1.30.0`, and a relay pending-resume assertion failed. The runner itself then failed printing UTF-8 logs to a cp932 console before creating its summary or running harness/Win32 suites. The raw run is preserved as incomplete/FAIL and is not counted as validation pass.

## Scope

No real App Server/provider, model, GUI, Docker, WSL/WSLc, or allocation was invoked. This fixes and locally qualifies one transport deadlock/close ownership boundary. It does not establish caller task success/effect, recovery reliability, live efficiency, MAP01, Research Preview graduation, distributable-runtime acceptance, or clean repository triage; #57 remains open.
