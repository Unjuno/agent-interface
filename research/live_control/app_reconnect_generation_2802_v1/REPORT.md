# #2802 Allocation 06 — reconnect generation boundary

First formal disposition: **HOLD_AUDIT_CONTROL_INCOMPLETE**.

## Scientific row outcome

The prospectively frozen formal allocation ran exactly once and completed all18 cases. No formal retry, replacement or post-freeze tuning occurred. The retained rows match the frozen scientific table:

- SATISFIED: 6
- EXPIRED: 3
- UNKNOWN_GENERATION: 9
- all producer subprocess exits: 0
- unsafe timestamp-only comparator: SATISFIED15 / EXPIRED3

In all six RECONNECT_CROSS_B / RECONNECT_CROSS_AB cases the unsafe comparator accepted B across a producer-generation restart while the candidate returned UNKNOWN_GENERATION. All three MISSING_GENERATION_B cases also produced an unsupported unsafe SATISFIED while the candidate returned UNKNOWN_GENERATION. FRESH_AFTER_RECONNECT shows liveness: a new obligation begun by A in the new generation satisfied normally.

This supports the scoped mechanism hypothesis at the row level: a pending temporal obligation should not be silently inherited across producer generation change solely because labels and numeric timestamps remain plausible.

## Why this is HOLD, not PASS

The frozen independent auditor returned `errors=[]` but rejected only **7/8** copied-evidence corruptions. Its `timestamp` mutation selected `rows[-1]`. That happened to be `LATE_SAME_PROCESS_B` in the six-case construction order, but cyclic formal ordering changed the final row, so the mutation did not touch the intended scientific discriminator.

The frozen D gate required8/8 controls. Therefore the consumed formal allocation is retained as `HOLD_AUDIT_CONTROL_INCOMPLETE`; the complete scientific rows are not upgraded to a preregistered PASS.

A postformal `audit_v2.py` changes only the copied-evidence mutation selector to find the declared `LATE_SAME_PROCESS_B` row by scenario. It does not change candidate/oracle/scientific checks. Read-only v2 audit on the immutable formal RAW gives errors=[] and8/8 controls rejected. This repairs reviewability but does not rewrite the first formal disposition or rerun science.

## H / T / D / C / U

**H:** an obligation anchored in one producer generation must not be implicitly satisfied by a restarted producer generation. Missing generation evidence is UNKNOWN; a fresh post-reconnect A→B obligation remains live.

**T:** six scenarios ×3 cyclic repetitions=18 cases using actual separate producer subprocesses. Reconnect cases use two sequential processes and distinct generation IDs/PIDs. Same-process and late controls use one process. Bound1s; late control1.2s.

**D:** scientific row/count/exit gates matched, but frozen auditor corruption gate was7/8 rather than required8/8. First result is HOLD. Read-only audit v2 rejects8/8 without a formal rerun.

**C:** trusted serialized local producer and cooperative generation IDs. Generation identity is not authenticated. Process restart is explicit and not concurrent.

**U:** sequence wrap within one generation, generation-ID reuse/forgery, concurrent reconnect, dropped bytes, multi-producer ordering, cross-host clocks, GUI/model/task benefit, input authority, reliability rates and production promotion remain open.

## Integration relevance

For #2802/#2789 observation freshness, this allocation supplies a concrete generation-boundary constraint but not a promotion-ready PASS because its frozen integrity gate missed. Do not use it alone to promote a runtime reconnect policy. A future scientific allocation is not automatically required: if a production decision can be made from already qualified predecessor evidence, use that; otherwise a genuinely needed successor should separately freeze the remaining generation/wrap question rather than rerun this allocation merely to turn HOLD into PASS.
