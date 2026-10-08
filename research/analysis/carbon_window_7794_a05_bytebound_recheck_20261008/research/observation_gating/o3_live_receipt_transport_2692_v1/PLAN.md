# Issue #2692 — live observation receipt transport, first rung

## H / T / D / C / U

- **H:** a fresh read-only GTK/X11 transport can create observation/intent/region,
  coverage/freshness/effect, source-window and process-generation receipts from
  actual captured X11 bytes, deliver the exact receipt to the existing O3 gate,
  and preserve fail-open behavior for corrupted/stale delivery.
- **T:** 2 independent GTK surface processes × 2 regions (`entry`, `status`) ×
  9 frozen cases (`complete_current`, `stale_frame`, `missing_region`,
  `partial_coverage`, `focus_window_change`, `generation_mismatch`,
  `malformed_receipt`, `authority_bearing`,
  `contradictory_effect_binding`) = 36 rows. Every raw transport event and its
  every row has a unique observation ID and monotonically unique intent epoch;
  freshness uses a frozen one-second capture-to-arrival bound. Full/region
  bytes are written before delivery corruption; an arrival monotonic timestamp
  is recorded at the evaluator boundary. Focus is sampled
  before and after capture. A separate
  Python process checks the still-live X server, process start time, window
  geometry/title/PID/XID, current X11 frame bytes and all receipt/decision rows.
  The allocation exposes no input or model client.
- **D:** raw receipt JSONL, delivery JSONL, decisions JSONL, raw frame bytes,
  fixture/window metadata, manifest, independent audit, stdout/stderr, cleanup,
  pinned image/source identities and hashes.
- **C:** `PASS_LIVE_RELEVANT_REGION_FAIL_OPEN_SCOPED` only for 4/4 exact current
  receipts admitted, all 32 negative rows rejected and model-escalation eligible,
  independent X11/oracle agreement on all 36, complete denominator, and zero
  model calls/input/actions. Any lost identity/coverage/freshness/effect data
  yields HOLD; any negative admitted or oracle disagreement yields FAIL.
- **U:** one Xvfb server with two static GTK processes and two rectangular
  regions; no model, actions, app diversity, quality, latency, savings, task
  success, native desktop, or production claim.

## Allocation history — immutable evidence

- `allocation-01-hold/` ran exactly 36 live captures in the pinned OrbStack
  image and recorded all raw bytes and gate decisions. Its independent audit
  was incorrectly scheduled after the fixture/X server had been terminated;
  the oracle correctly failed to connect. This is retained as
  `HOLD_ORACLE_AFTER_SOURCE_CLEANUP`, not relabeled as a pass and not modified.
- **Allocation 02** is a distinct fresh run after that observed ordering defect.
  It is frozen below; its independent oracle is a separate process that runs
  before fixture cleanup. No retries or replacement within allocation 02.

## Frozen allocation 02

- ID: `o3-live-receipt-transport-2692-v1-live-oracle-20260921-02`.
- Branch: `research/issue-2692-live-observation-transport-v1`.
- Source base: `8085e682f6363ec4cd95648e55c16dfca9049dd0` (main re-fetched
  and fast-forwarded immediately before freeze; no overlap with this namespace).
- Existing gate: `research/observation_gating/o3_relevant_region_successor_v1/gate.py`,
  Git blob `50c27bd4e8651da74163c786daeb654928b08958`.
- Image: `sha256:8c37d3a0ff21d1205a00c567fd184184816ab00d81292cb0feee7be92d572f64`,
  inspected as `linux/arm64`.
- Runtime constraints: `--network none`, `--read-only`, only `/tmp` tmpfs and
  dedicated `/out` bind are writable, isolated `DISPLAY=:100`, no input API.
- Exact output path: `allocations/allocation-02-live-oracle/`.
- Frozen source SHA-256 (allocation driver and gates):

```text
case_schedule.json 8edd8e8229075c93ba5790c2ebd62e606d2fb8ccc24bba192c07a283c521b780
gtk_fixture.py 542a97f68e850ea55eb004ee88d53588d8a439833edd9b7f70aee7b330d1b4f5
transport.py 7e14fc38d0c7c93b3cb5c2df179db662395770283390ae7b23fd5b1df4d40eb9
adapter.py aee2508f2bc2cbbad58df06c8fd035fb781b61c2b2d5ad2f20813106a6a4f222
independent_oracle.py 105957713c8998690dfd0bb6a21597af6d48c0c5548b516d5201fff393ba0bca
runner.py 0001ad8584a990cdc185f72bf1aa8034e41bced0b33eca5cb89e1cfc95b866f5
```

The schedule is fixed in `case_schedule.json`. Construction check is syntax plus
36-row arithmetic in the pinned image; it is not part of the formal result.
The source hashes above, exact Docker argv, image ID/platform, exit status and
every raw result are retained. If the allocation fails, retain the result and
stop this allocation.
