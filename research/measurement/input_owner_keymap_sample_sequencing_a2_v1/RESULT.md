# Issue #1035 A2 first construction outcome

Decision: **`PASS_OWNER_PHYSICAL_SAMPLE_SEQUENCING_SCOPED`**. Independent audit: **`PASS_AUDIT`**.

A2 preserved the A1 baseline/candidate/common SHA-256 identities exactly and changed only the ordering-auditor treatment of a `key_lookup=false` pre-sampling UP terminal. Fresh construction used 500,000 cases; audit used 100,000 distinct cases.

## Result

- non-sample semantic/state mismatches: **0**
- construction ordering errors: **0**
- sample-failure cases: **95,197**
- sample-failure semantic changes: **0**
- audit mismatches/order errors: **0 / 0**
- construction digest: `5e946b5e6b5c7d3e2c7c0d8e1eb7dc09b56df59a87270b417c8f9e4342b16674`
- audit digest: `8389d9501c1c387762389a7c172e90350964d70294e45e24329c495849d766cd`

The result supports only the scoped mechanics claim: best-effort raw physical-state samples can be placed at the #994/#992 owner-request ordering points in this model without changing baseline input decisions/state, including when sampling is unavailable.

## Boundaries

This does **not** establish real X11 keymap behavior, sampling latency, a physical edge, stable actuation identity, authority, application consumption, or live/MAP01 useful control. It does not unblock #998's identity requirement by itself.

Raw local RESULT: 25,953 bytes, SHA-256 `d251c9def96db055184dd9c3873873111c0aaf88a8b69cc8d4fb70779ba77f91`, not falsely claimed Git-retained.
