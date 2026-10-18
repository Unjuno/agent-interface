# A01 plan — V39 startup edge identity join

## H — hypothesis

The retained deterministic V39 startup trace uniquely joins each admitted key
to its explicit UP and owner-thread release receipt through the program,
step, owner and intent identities, while preserving release order. If the raw
does not contain an actuation identity or independent effect interval, the
audit must withhold physical-occupancy and task-effect linkage claims.

## T — test

Use only the already-retained raw trace from PR #7881 A03, copied byte-for-byte
and pinned in `FREEZE.json`. Independently reconstruct one-to-one admission →
UP-transition → owner receipt joins; validate identity equality, key-specific
event order, timestamp containment/order, and the raw fake-X operation window
between UPs. Run the auditor's positive reconstruction and bounded mutation
controls for duplicate/mismatched identity and reversed chronology. Do not
rerun the candidate or start any live allocation.

## D — decision

The contextual join subcheck passes only with exactly two unique
identity-consistent admission/release/owner-receipt joins, complete timestamps,
preserved release order, and zero `query_keymap` calls between UP injections.
Any contradictory or ambiguous row is FAIL. The required
`PASS_INSTRUMENTATION` gate additionally requires a per-actuation link to an
independently observed task-effect interval. Since the fake seam does not
provide that evidence, the overall decision must be `HOLD_EFFECT_LINK` even
when the contextual join subcheck passes.

## C — counterexplanations

Repeated key names, missing owner history, reused intent tokens, and clock
ordering anomalies can create false joins. A server-side XSync receipt can be
mistaken for physical key occupancy or an application effect if the evidence
boundary is not kept explicit.

## U — limits

This is a posthoc audit of one deterministic fake-display trace, not a new
V39 experiment. The raw records XTest/XSync calls but no authoritative physical
occupancy, actuation ID, or independently scored application effect. No live
X11, model, DoomGame, OS input, bounded latency, threat-control, recovery,
MAP01 result, or human-tempo claim follows.
