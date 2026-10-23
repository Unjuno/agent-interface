# Public Win32 effect timing R01

## Question and scope

For one fresh owned Win32 fixture using the standard public stdio-MCP caller, what is the observed ordering and elapsed time from public dispatch start through fixture input, saved-effect file close, public dispatch response, and independent file readback? This is one descriptive sample, intended to close the missing timing instrumentation between R06's successful public path and its independent effect oracle.

The dispatch uses the same finite operation sequence as R06 and one new exact sentinel. The only operational change is that the packet-local fixture records `time.monotonic_ns()` for click, character, and save events and brackets the saved-effect file write. The probe records the public observe/dispatch request intervals and brackets the independent effect-file read. All timestamps use Python's system monotonic clock on the same Windows host.

## Frozen protocol

- One newly launched, visible process-owned fixture; only its HWND is configured.
- One public `interface_observe`, one validation, and at most one `interface_dispatch`.
- The task is `MCP-LIVE-R07-TIMING-ONLY`; it saves a single exact JSON effect.
- No retry or replay after a timeout or unknown result.
- Always post close to the owned HWND, wait for that process, and retain raw output even on failure.
- `conditions.json` identifies the runtime baseline and pins the probe, auditor, and packet-local fixture by SHA-256.
- `audit.py` is run after raw capture; it checks exact task effect, event counts, public completion, verified release, event ordering, readback ordering, and frozen-file hashes.

The key timing endpoints are dispatch request start/return, each fixture input event, save-write start/close, and independent read start/return. The release receipt has no exposed sub-call timestamp: its final state is observed in the public dispatch response, so the only claim is that a verified receipt was available by that response time. This experiment does not claim an exact release instant, a deadline, or a general latency distribution.

## Decision and limits

PASS means this one attempt produced the exact independent effect and event sequence, a completed public result with verified all-up release, all click/character/save event timestamps fell within the dispatch call interval, file close preceded dispatch response, and independent readback began after file close. Any missing or inconsistent evidence is FAIL/UNKNOWN and remains retained without rerun.

The result is one positive-path Windows fixture observation. It does not compare strategies or estimate a population distribution, and it says nothing about blocked platform I/O, recovery bounds, MAP01, model/token efficiency, or broad reliability. Timing may include scheduler delay, window message dispatch, fixture I/O, and MCP serialization.

## Run and audit

From the repository root on the authorized Windows host, run:

```powershell
python research/integration/win32_public_mcp_effect_timing_20261024_r01/probe.py
python research/integration/win32_public_mcp_effect_timing_20261024_r01/audit.py
```

The probe refuses to run if `raw.json` or `run/` already exists. The captured `raw.json`, `run/`, and `audit.json` are immutable attempt evidence after the run.
