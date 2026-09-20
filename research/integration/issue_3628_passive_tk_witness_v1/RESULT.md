# Result — Issue #3628 passive Tk event witness

## Decision

`PASS_TK_EVENT_WITNESS_AND_PUBLIC_MCP_CONTINUATION_SCOPED` for the preregistered fixture-level gate. This is not a host/model-visible acknowledgement result and does not close #3370.

## Execution

The construction allocation `formal-05b63c13820e` and its seven adversarial controls passed before the formal freeze was recorded. Exactly three formal Linux/arm64 OrbStack allocations then ran, each in a fresh no-network container with the pinned image. Each used one public stdio MCP session with one initial observe, one dispatch, and one explicit post-action observe. All three recorded one ordered passive `Control_L`,`s` sequence; the independent effect JSON exactly matched its unique marker; the dispatch completed and verified release empty; the post-observation ID/image was fresh; and child/socket cleanup completed. No formal row was retried or replaced.

## Audit trail

- The inherited #3618 raw-only auditor was run once and returned `HOLD_OR_FAIL` (122 checks; three failures), because its historical `fixture-received-exact-marker` and save-chord criteria inspect the later all-bindtag logger rather than the new passive-tag receipt. This output is retained as `evidence/audit-invocations/original-122-check-HOLD_OR_FAIL.json`; it is not overwritten or reinterpreted.
- A first invocation of the #3628-specific raw-only auditor stopped before reading evidence because its output directory already existed. The STOP is retained as `evidence/audit-invocations/output-path-exists-STOP.json`.
- The corrected, preregistered #3628-specific auditor ran once against the same immutable formal rows and passed all 102 checks with zero failures. Its `AUDIT.json` hash is `eb29a825f4551a0b3cd46843b789d3011305afb2fc6cc1da07268964c97ccca3`.

The new audit evaluates the passive event witness exactly once in order and uses the fixture effect file as a separate oracle. It does not promote event logs alone to proof of effect. The seven preflight negative controls separately reject missing, duplicated, reversed, wrong-key, no-effect, and no-event evidence.

The committed raw manifest contains 95 canonical evidence files (407,148 bytes). An earlier packaging mistake introduced an 89-file nested duplicate tree; all duplicate files were byte-identical to canonical paths. The follow-up cleanup removes the tracked duplicate copies only; canonical raw evidence remains unchanged, and the manifest now covers canonical files only.

## Supplemental validation boundaries

The attempted native-image unittest command did not reach unittest: that image has a fixed entrypoint to an unrelated `/workspace/research/live_control/native_mcp_v1.py`, absent from this checkout. A portable-image invocation with its entrypoint explicitly set to Python reached the requested suite, but all 9 tests were skipped because this invocation did not provide `DISPLAY`; this is recorded as NOT RUN/skip, not a suite PASS. The three formal MCP/Xvfb allocations and the 102-check raw audit are the validation for this issue's gate.

## Allocation IDs

- `formal-13404b8c9d4b` — marker `orb3587-2daf80055565`
- `formal-c768374eecc6` — marker `orb3587-5d600c1bb95b`
- `formal-9eceb344ed5a` — marker `orb3587-cb5f4dc85b62`

All raw requests, reports, images, event receipts, process logs and allocation records are under `evidence/`. #3587, #3618 and #3620 evidence/outcomes remain unchanged.
