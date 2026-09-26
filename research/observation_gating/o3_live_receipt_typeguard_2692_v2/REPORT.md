# Issue #2692 successor v2 — formal result

## H / T / D / C / U

- **H:** malformed/non-monotonic transport timestamps cannot suppress model
  escalation or raise before fail-open handling.
- **T:** allocation
  `o3-live-receipt-typeguard-2692-v2-20260921-03`; 2 GTK processes × 2 regions
  × 8 frozen cases = 32 unique observation/epoch rows. One pinned OrbStack
  `linux/arm64` run; network none, root and source read-only, dedicated output
  bind, isolated Xvfb `:101`; no retry.
- **D:** `allocations/allocation-03-live-typeguard/` contains raw X11 events,
  all frame bytes, receipts, decisions, case manifest, independent oracle,
  launch record, checksums and cleanup record.
- **C:** `PASS_LIVE_MALFORMED_CLOCK_FAIL_OPEN_SCOPED` — 4/4 current positives
  admitted; 0/28 malformed clock controls admitted; 28/28 negative controls
  model-escalation eligible; independent live X11 checks 32/32; zero audit
  errors, model calls, input events, action emissions. Container exit 0.
- **U:** static GTK/Xvfb transport adapter only; no model quality, application
  diversity, task outcomes, latency/savings, native desktop or production
  claim. The earlier v1 allocation-02 artifact remains unchanged; this v2
  successor specifically addresses typed timestamp exceptions.

## Frozen source and construction

Main base at freeze: `a0f0ca37c88ad46f3f98485483453cedbe432723`.
Pinned image: `sha256:8c37d3a0ff21d1205a00c567fd184184816ab00d81292cb0feee7be92d572f64`
(`linux/arm64`). Construction syntax/schedule check passed in the image using
read-only AST parsing; normal `py_compile` could not write `__pycache__` on the
deliberately read-only root and was not treated as a test failure or retried.

Frozen SHA-256:

```text
case_schedule.json a833543ca69db980136e5f10d7d3c8e0cbc6bafce31a8051baefcc48acc2f565
adapter.py 29de9555298d3c150566e53aa0cf22751db4b00f819762317f093c734b461113
runner.py 4ae889024cf0703387338846b6c8d03905a39a149605131917b84e55d6b880bc
independent_oracle.py 4b8374e0ceea361db5822c82c0bd4754522820c1503bb8244f9eb2cec7cfcb21
```

## Formal result

| Case | Rows | Admitted | Escalation eligible |
|---|---:|---:|---:|
| complete_current | 4 | 4 | 0 |
| capture_end_string | 4 | 0 | 4 |
| capture_end_list | 4 | 0 | 4 |
| capture_end_missing | 4 | 0 | 4 |
| capture_start_string | 4 | 0 | 4 |
| arrival_string | 4 | 0 | 4 |
| end_before_start | 4 | 0 | 4 |
| end_future | 4 | 0 | 4 |

The candidate adapter was called 32 times (`adapter_module=adapter`), and an
independent process verified each live frame/window and the denominator before
fixture cleanup. No model, input, or action interface was present. Raw evidence
and artifact hashes are retained beside this report.
