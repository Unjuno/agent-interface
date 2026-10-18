# Construction and source-freeze history

The first frozen packet is preserved as `SOURCE_FREEZE_INITIAL.json` (SHA-256
`e54f1baa3bcf2caee3d0068e74ce56f95e71708b7c277c90095291aa1a821803`). Before
raw collection, its auditor was exercised in both Python modes. Normal mode
passed 4/4 tests. Optimized mode exposed three defects in the testable auditor:
Python `assert` statements were removed under `-O`, so two mutation controls
did not reject corrupted records and a missing-case input leaked `KeyError`.

The auditor now uses explicit `AssertionError` checks for every acceptance
condition. Its mutation tests passed 4/4 in normal Python 3.11 and 4/4 under
`-O`. No probe run occurred before this correction. `SOURCE_FREEZE.json` is the
pre-collection v2 packet: it pins the corrected auditor and includes the initial
freeze by hash, preserving the construction failure and repair without changing
any collected raw data (none existed at that point).
