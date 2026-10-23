# Public Win32 effect and visual response R04

## Question and scope

For one fresh owned Win32 fixture using the standard public stdio-MCP caller, what is the observed ordering and elapsed time from public dispatch start through fixture input, saved-effect file close, public dispatch response, and independent file readback? This is one descriptive sample, intended to close the missing timing instrumentation between R06's successful public path and its independent effect oracle. R01 was refused before input because it omitted the current caller's required target-generation token; R02 proved the forwarded value succeeds but exposed the 15.625 ms GetTickCount64 resolution. R03 used Python's QueryPerformanceCounter-backed `perf_counter_ns()` and found the 300 px final image clipped the sentinel tail. R04 keeps the corrected caller and high-resolution clock, and widens both public observation regions to the fixture's full 420 px client width.

The dispatch uses the same finite operation sequence as R06 and one new exact sentinel. The probe extracts `receipt.source.raw_report.target_generation` from the public observation and passes it under `source.target_generations.fixture`. The packet-local fixture records `time.perf_counter_ns()` for click, character, and save events and brackets the saved-effect file write. The probe records the public observe/dispatch request intervals and brackets the independent effect-file read. All timing timestamps use Python's `QueryPerformanceCounter()`-backed monotonic performance clock on the same Windows host; the authority lease continues to use the runtime-required `time.monotonic_ns()` clock.

## Frozen protocol

- One newly launched, visible process-owned fixture; only its HWND is configured.
- One public `interface_observe`, one validation, and at most one `interface_dispatch`.
- The task is `MCP-LIVE-R07-VISUAL-R04`; it saves a single exact JSON effect.
- No retry or replay after a timeout or unknown result.
- Always post close to the owned HWND, wait for that process, and retain raw output even on failure.
- `conditions.json` identifies the runtime baseline and pins the probe, auditor, and packet-local fixture by SHA-256.
- `audit.py` is run after raw capture; it checks exact task effect, one click, the complete expected set of timestamped events, public completion, forwarded observation generation, verified release, event ordering, readback ordering, and a retained 420x140 post-action image whose artifact hash matches the report. Full visible sentinel content is also inspected from the frozen image after the run.

The key timing endpoints are dispatch request start/return, each fixture input event, save-write start/close, and independent read start/return. The release receipt has no exposed sub-call timestamp: its final state is observed in the public dispatch response, so the only claim is that a verified receipt was available by that response time. This experiment does not claim an exact release instant, a deadline, or a general latency distribution.

## Decision and limits

PASS means this one attempt produced the exact independent effect and event sequence, a completed public result with verified all-up release, all click/character/save event timestamps fell within the dispatch call interval, file close preceded dispatch response, and independent readback began after file close. Any missing or inconsistent evidence is FAIL/UNKNOWN and remains retained without rerun.

The result is one positive-path Windows fixture observation. It does not compare strategies or estimate a population distribution, and it says nothing about blocked platform I/O, recovery bounds, MAP01, model/token efficiency, or broad reliability. Timing may include scheduler delay, window message dispatch, fixture I/O, and MCP serialization.

## Frozen R02 outcome

The public observation returned a matched target generation, which the probe forwarded unchanged in `program.source.target_generations.fixture`. The public stdio-MCP dispatch was accepted and completed once. The independent effect file contains the exact R02 sentinel with `saved=true` and `clicked=true`; the event journal contains one click, 23 matching character events, and one save. The release receipt is verified with empty key/button down and unknown sets, and the owned fixture exited 0 after close. The frozen auditor passes 25/25.

The recorded coarse-clock intervals are 78 ms from dispatch start to save-file close, 141 ms to public response, and 94 ms from save close to independent read start; the read took 15 ms. Windows Python reports this host's `time.monotonic_ns()` implementation as `GetTickCount64()` with 15.625 ms resolution. The save-write duration measured as 0 ms, which is below that resolution and must not be read as zero physical time. R03 uses the available `QueryPerformanceCounter()`-backed `perf_counter_ns()` for finer endpoints. R02 establishes only one positive caller/generation/effect/release path; the coarse timing values are retained as bounded-resolution observations.

## Frozen R03 outcome

The frozen high-resolution trial passed 25/25 checks. Its matching observation generation was forwarded unchanged; the standard public stdio-MCP call completed once. The independent file and event journal agree on one click, all 23 exact characters, and one save. The verified release receipt has no keys or buttons down or unknown, and the owned fixture exited 0 after close.

Using the recorded `QueryPerformanceCounter()` clock (100 ns reported resolution), click arrived 5.5515 ms after public dispatch start, first text at 46.9063 ms, last text at 60.5935 ms, and the file write closed at 61.8722 ms. The file write interval measured 0.3032 ms. Public dispatch returned at 122.9508 ms; the independent read started 106.1251 ms after file close and took 4.1535 ms. This remains one sample and includes scheduling, message handling, and serialization; no comparison, tail estimate, or general performance claim follows.

The retained post-action MCP image shows the fixture reflecting typed input, but its 300 px crop clips the tail of the sentinel after the visible `MCP-LIVE` prefix. R03 therefore confirms a visual response began, while the exact full on-screen sentinel remains unverified. The independent file and complete event journal still confirm the exact task effect.

## Frozen R04 outcome

The initial public observation failed before validation or dispatch with `Win32BackendError('capture outside client bounds')` because 420 px was the fixture's outer width, not its client width. `dispatch_attempts` is 0 and the event journal contains no input events. The owned fixture close was posted and it exited 0. R04 is UNKNOWN/FAIL and was not retried. The successor measures `GetClientRect` on the owned HWND, uses that exact client size for both observation calls, and uses a short exact sentinel that fits the visible row.

## Frozen R01 outcome

The single public dispatch was refused with `TARGET_GENERATION_REQUIRED` before invoking input. The public observation had returned a matched target generation, but the probe omitted it from `program.source.target_generations`. The independent journal contains only the fixture's `ready` event; no click or character event was received, no effect file was written, and the owned fixture exited 0 after close was posted. The retained runtime result reports `input_dispatched=false`, `operation_invoked=false`, and `replay_allowed=false`. This is a failed compatibility attempt, not a timing sample, and it was not replayed.

The frozen auditor reports 11/20. Its `timing_events_inside_dispatch` check is vacuously true when there are no click/character/save events; this check does not make the experiment pass because the independent effect, save, and release checks fail. A successor auditor requires the complete expected set of timestamped events. R01 `raw.json`, the public MCP call records, its audit output, and SHA-256 manifest retain this result.

## Run and audit

From the repository root on the authorized Windows host, run:

```powershell
python research/integration/win32_public_mcp_effect_timing_20261024_r01/probe.py
python research/integration/win32_public_mcp_effect_timing_20261024_r01/audit.py
```

The probe refuses to run if `raw.json` or `run/` already exists. The captured `raw.json`, `run/`, and `audit.json` are immutable attempt evidence after the run.
