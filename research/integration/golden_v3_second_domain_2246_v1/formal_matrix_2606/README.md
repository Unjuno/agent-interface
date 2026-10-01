# Formal GTK eight-case matrix harness (#2606)

This directory is an additive contract harness for the successor experiment
described in Issue #2606. It is deliberately **not** the formal #2492 live
acceptance result.

The harness fixes the case order and the evidence boundary before a live
fixture runner is introduced. It accepts only receipts containing:

- session/window identity and matching observation/binding revisions
- ordered input ledger
- independent effect receipt
- cleanup receipt
- zero authority grants at this contract boundary

It preserves the declared distinction between unavailable, refused, no-effect,
partial, repaired, ambiguous, useful, and cleanup-failure outcomes. Ambiguous
delivery is terminal for the case and cannot be replayed. Cleanup failure can
never be classified as success.

The live runner still must provide a fresh private GTK fixture, actual event
traces, independent effect evidence, release/neutrality evidence, and one
fixed-order execution of all eight cases. Until then, this harness must not be
described as live GTK acceptance, model/provider evidence, or production
validation.
