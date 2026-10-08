# #59 occurrence-key occupancy successor T0

## H / T / D / C / U

- **H:** Assigning every press/release interval a stable `interval_id` will allow repeated occurrences of the same key in one action/epoch to produce separate conservative duration bounds, without weakening fail-closed handling of missing/duplicate identity, inconsistent action/epoch, ambiguous same-key overlap, malformed timestamps, or an invalid empty terminal.
- **T:** One frozen candidate invocation evaluates four valid cases (single pulse, two same-key pulses, three same-key pulses, and interleaved W/SPACE/W) plus seven invalid cases. A separately authored raw-only auditor independently reconstructs valid occurrence bounds and checks expected rejection classes. Candidate once, auditor once, retries zero.
- **D:** `PASS_METHOD_SCOPED` only if 4/4 valid cases return every exact occurrence separately with the mathematically expected bounds; 7/7 invalid cases return `UNKNOWN` with the frozen fail-closed reason. Any missing/extra/merged interval or accepted invalid case is `FAIL`.
- **C:** Based on the local boundary counterexample in PR #6105; independent pure-stdlib Python implementation. Main anchor `f0139613cb96d5f2d84e803b75961dff549d58c8`; Windows host, CPython 3.12.10, CPU-only. Docker Engine bounded query timed out; service Stopped/Manual. This is a local construction, not a live allocation.
- **U:** Finite synthetic schema and algorithm test only. It does not prove that real input-owner/XQueryKeymap evidence supplies sound timing brackets, that MAP01 emits these repeated pulses, or that an application consumes input. No live occupancy, useful effect, safety, latency, gameplay, GUI, physical input, model, GPU or container claim.

## Contract under test

Every `key_interval` is identified by `(action_id, epoch, interval_id)`; `key` is not unique. Same-key occurrences are bounded separately only when their retained witnesses prove strict separation (`previous.up_sample_ns < next.press_request_ns`). If order/separation is ambiguous, return `UNKNOWN`. Distinct keys may have overlapping intervals. Each duration remains `[release_request_ns - press_sync_ns, release_sync_ns - press_request_ns]`. Exactly one same-action/epoch verified-empty terminal must follow all up samples.

## Frozen execution

1. Run `python candidate.py` once and retain `results/t0-01/raw.json`.
2. Run `python audit.py` once in a separate process and retain `results/t0-01/audit.json`.
3. Do not retry either allocation. Corrections require a new successor path.
