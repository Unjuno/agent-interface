# Issue #2692 successor v2 — malformed clock type guard

## H / T / D / C / U

- **H:** a typed fail-open receipt adapter accepts only current well-formed
  capture clocks; string/list/missing/reversed/future or malformed arrival
  clocks must fail open without suppressing model escalation. This directly
  tests the review-found edge case without rewriting allocation 02.
- **T:** allocation
  `o3-live-receipt-typeguard-2692-v2-20260921-03`; 2 fresh GTK/X11 windows ×
  2 regions × 8 frozen cases = 32 rows (4 positive, 28 malformed-clock
  controls). Each row captures live bytes before delivery mutation. A distinct
  process independently checks X11/window/PID/frame evidence while fixtures
  remain alive. The adapter and oracle source hashes are frozen below before
  formal execution. One formal invocation; no retries or row substitutions.
- **D:** raw capture events, immutable frame bytes and hashes, delivered
  receipts, decisions, independent live-X11 audit, case counts, manifest,
  launch/image identity and cleanup status.
- **C:** `PASS_LIVE_MALFORMED_CLOCK_FAIL_OPEN_SCOPED` only if all 4 complete
  current rows admit; all 28 malformed-clock rows are rejected and escalation
  eligible; 32/32 independent live checks and lineages pass; no model calls,
  input events, or actions occur. Any admitted malformed row, mismatch, or
  missing denominator is FAIL; inability to retain live source evidence is
  HOLD.
- **U:** static GTK/Xvfb only; no application diversity, model behavior,
  latency, task quality, native desktop, or production claim.

## Frozen source and runtime

- Base: `a0f0ca37c88ad46f3f98485483453cedbe432723` (main at freeze).
- Predecessor v1 allocation 02 and its hashes/results remain unchanged.
- Image: `sha256:8c37d3a0ff21d1205a00c567fd184184816ab00d81292cb0feee7be92d572f64`,
  `linux/arm64`; network disabled, root/source read-only, dedicated output bind.
- Source SHA-256 values:

```text
case_schedule.json a833543ca69db980136e5f10d7d3c8e0cbc6bafce31a8051baefcc48acc2f565
adapter.py 29de9555298d3c150566e53aa0cf22751db4b00f819762317f093c734b461113
runner.py 4ae889024cf0703387338846b6c8d03905a39a149605131917b84e55d6b880bc
independent_oracle.py 4b8374e0ceea361db5822c82c0bd4754522820c1503bb8244f9eb2cec7cfcb21
```

Frozen after schedule/code review and before formal execution. Construction
checks do not count as results.
