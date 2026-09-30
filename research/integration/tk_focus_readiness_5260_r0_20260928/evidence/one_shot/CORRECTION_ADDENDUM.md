# Data-only correction to the #5260 r0 STOP record

Date: 2026-09-30  
Reviewed PR: [#5293](https://github.com/Unjuno/agent-interface/pull/5293)  
Reviewed head: `30e8d281d08c27d71c0eebae35bb0e1db0557b16`  
Allocation: `tk-first-char-focus-order-5260-r0-20260928-01`

## Correction

The retained `STOP_RECORD.md` and original PR synopsis say that all 32 recorded
click coordinates were `(0,0)`. Decoding the hash-verified raw archive shows:

- Row index 0: `(0,0)` — 1 of 32 rows
- Row indices 1–31: `(240,148)` — 31 of 32 rows

Consequently, unresolved zero geometry cannot be asserted as the common cause of
all 32 failed input observations. The first row does contain zero coordinates;
the other 31 contain nonzero coordinates. Neither proves that the pointer moved
to, clicked, focused, or delivered keys to the intended widget. The retained
records do not independently establish the causal explanation for the failures.

## Disposition unchanged

**STOP_PROVENANCE_OR_RUNNER remains the correct retained disposition.**
The first-character/focus hypothesis remains untested by this allocation.
The following independently counted facts are unchanged:

- All 32 application processes exited 0, but all 32 target Entry values were empty
- No target `KeyPress` event was recorded
- All 16 busy-worker rows recorded exit `-15`, whereas the frozen auditor requires 0
- The retained audit lists 16 worker-exit errors and 32 mismatched input rows
- The Xvfb setup log records a Unix-listener bind failure; private-display provenance
  is therefore not established by this evidence

Nonzero recorded geometry does not convert this STOP into a scientific PASS or
FAIL, establish delivery, or justify repeating the consumed allocation.

## Data-only verification and immutable evidence

Read from the exact PR head above using GitHub MCP:
`research/integration/tk_focus_readiness_5260_r0_20260928/evidence/one_shot/raw.json.zip.b64`.
The archive was decoded and its `raw.json` member parsed as data. No study import,
runner, auditor, GUI, model call, or experiment was executed for this correction.

- Decoded ZIP SHA-256: `9cc9b7b3ad24d903ba23b280653faf9c6d33b2e41a3aeb873f99d825662071e3`
- Uncompressed `raw.json`: 60,935 bytes; SHA-256
  `ae934766d424bd5617fd0f1de22b9a285d265b60f6381bc44a7dada24e39b6d6`
- Retained `audit.json` SHA-256:
  `13a3782e0b9dc59426e821204a7254c430557388095f71678d807c1774175474`
- Decoded setup-log ZIP SHA-256:
  `3e2f8c5ae012a8719a434fd51ec65563cac0df0c7224178a743289e6d4b0b372`
- All three current source hashes match the retained `FREEZE.json`, and the raw
  source-identity map matches that freeze

This note corrects the interpretation additively. The original raw, freeze, audit,
logs, STOP record, and allocation outcome remain unchanged.
