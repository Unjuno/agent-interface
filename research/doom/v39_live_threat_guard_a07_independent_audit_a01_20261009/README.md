# Independent raw custody audit of live allocation A07

This package independently reconstructs the input-cancellation custody portion of A07 from the private raw `events.jsonl`, controller report, scorer summary, and terminal score. It does not import A07's `audit_live.py` or `audit_live_v2.py`, and it does not modify or copy the private raw allocation directory.

## Result

`PASS_RAW_CUSTODY_RECONCILIATION`; the overall live research gate remains `HOLD`. All 2,358 files in the raw allocation manifest match; the manifest and event-stream SHA-256 values are pinned by the auditor. Of 10 matched cancellations, six had input and four occurred before any input admission. The six input-bearing cancellations had 30 held-key events: 25 were paired to complete per-key release transitions and five to verified cleanup key-up attempts (`server_key_down_before=true`, `server_key_down_after=false`). All ten terminal releases were verified empty. Three in-memory mutation controls (drop one cleanup key-up, make a terminal nonempty, invalidate an explicit key-up receipt) were all rejected.

The original A07 auditor's FAIL was too broad for the four pre-admission cancellations; the allocation's additive audit v2 classified the release-custody portion as passing and the overall research gate as HOLD. This independent implementation confirms the per-key accounting more tightly: every admitted held key in a cancelled cover has matching release evidence. It does not promote the A07 episode to a live-control PASS.

## Audit contract

- **H:** Determine whether the original cancellation FAIL reflects a missing release or an audit join that incorrectly requires a release event when no input was admitted.
- **T:** Verify the complete private A07 manifest; for each cancellation, match admitted key identities to held-key records and require one of a complete same-step key-up receipt or a verified cleanup keymap transition; require a verified empty terminal after every cancellation. Independently inspect the recorded hard-health invalidation, scorer summary, and final score.
- **D:** Custody passes only if all 10 cancellations are matched, every held input has per-key release evidence, no-input cancellations have no input transition, every terminal release is verified empty, the manifest is complete, and all three mutation controls fail as intended. Overall research PASS is out of scope for this audit; this result remains HOLD.
- **C:** Server-side X11 `query_keymap` receipts do not prove physical device state or that the game consumed a key. A changed scene or alive terminal cannot substitute for a hard-health guard event or useful scorer event.
- **U:** The live run had no hard-health guard exposure and no positive useful scorer event. Physical key state, independent feedback efficacy, recovery benefit, and MAP01 exit remain unproven.

## Scope boundary

The 49 raw `input_release_transition` rows all mark physical verification as non-authoritative. The five cleanup key-up attempts use `x11_query_keymap`; these are server-side receipts, not proof of physical hardware state or game consumption. A07 had 10 planner turns, no hard-health guard exposure, zero positive useful scorer events, and ended alive but unfinished with no MAP01 exit. Thus the fresh live threat-control gate remains HOLD. No VM, GUI, app-server, model, or input was started by this audit.

The A07 raw set remains in its original local, ignored allocation directory and is not included here. To reproduce, pass that unchanged directory as `RAW_ROOT`; the auditor fails closed if the pinned manifest or event-stream hash differs.
