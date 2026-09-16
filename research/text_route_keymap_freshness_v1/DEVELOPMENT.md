# Development record

1. Initial fixture run failed before any input: XKB output subdirectories were not created before `xkb_projection.resolve_xkb()` wrote its files. No formal ID was consumed. The fixture-only repair creates the directory first.
2. Repaired development matrix passed all three cases.
3. US→US: stale compiled plan and safe execution both produce exact `@`; fresh routing remains direct.
4. US→German: stale US plan produces `"`; retained execution-time preflight rejects `@` as `TEXT_NOT_REPRESENTABLE_IN_KEYMAP` with zero direct emissions; fresh transparent selection is no-route; fresh clipboard-authorized selection pastes exact `@`.
5. US→French: stale US plan produces `2`; the same safe/fresh behavior holds.
6. Stop tuning and freeze the three-case discriminator.
