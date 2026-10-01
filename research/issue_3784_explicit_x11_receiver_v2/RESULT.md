# Issue #3791 formal-02 result

## Disposition: STOP — baseline layout parser rejected valid output

The frozen runner ran once in the pinned no-network container. All four explicit receivers passed focus readback and the corrected XTEST control oracle: each logged a KeyPress and KeyRelease for keycode 38, keysym 97, with XLookupString text `a` on both event types. All four Xvfb processes were reaped.

The next gate stopped all rows at the baseline. `setxkbmap -query` returned exit 0 and the US layout, with output line `layout:     us`. The runner's parser used exact equality against `layout: us`, so its `layout_ok` flag was false. No German layout application, unsupported-payload check, candidate planning, or formula emission occurred. This does not answer the delivery hypothesis and is not a candidate FAIL.

The frozen audit-v1 then raised `UnboundLocalError` while building a STOP summary because local variable `ev` was not initialized for a row that had not reached candidate delivery. Its preregistered SHA and exception are not overwritten. A separate read-only forensic audit-v2 used whitespace-tolerant query validation and early-stage gates; it confirms the parser STOP with zero integrity errors. This audit addendum is post-result and does not replace the frozen audit-v1.

## Evidence

- Formal raw SHA-256: `eced38b64c1c1e1f78c5bfd5dc30dcede5c5c9563f8bac73b71e29d4d98ed689`
- Frozen runner SHA-256: `ffe1b5d081775c511de50a0a626b6e43ff6f4e094069b3d40baa9e33b334246b`
- Frozen audit-v1 SHA-256: `fa0033c4706843e4680268d466da5b45dbd0e5f10a721d58a5cd33a4ff27a2d2`
- audit-v1 outcome: runtime exception, `UnboundLocalError: cannot access local variable 'ev' where it is not associated with a value` while processing an early STOP.
- Forensic audit-v2 SHA-256: `fe498a338bdee4124596e830c8d67885f12eb043463f0771262ddf44d91abc6b`
- audit-v2 disposition: `PASS_AUDIT_CONFIRMED_HARNESS_STOP`, zero errors; it binds all four raw rows, receiver events, US query/dump/map, source/runner/manifest and cleanup.

## Next gate

Preserve formal-01 and formal-02 unchanged. A successor must fix the whitespace-tolerant layout parser and add it to construction coverage, exercise the complete baseline/DE map transition before formal execution, and make the independent auditor safe for early STOPs. Only then run a new, preregistered allocation toward the candidate formula. Do not infer any German delivery success or failure from these two setup STOPs.

