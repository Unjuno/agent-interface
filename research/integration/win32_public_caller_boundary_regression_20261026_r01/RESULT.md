# Selected Win32 public-caller regression R01

At source `76088cf3460c7e62da780fc03a6940ccedf6e066`, five relevant suites covering the public compiled caller, Win32 composition, target-generation admission, supervisor helpers, and owned-session custody ran locally under Python 3.13.14.

- Normal Python: **53 tests passed**, exit 0.
- Optimized Python (`-O`): **53 tests passed**, exit 0.

Both runs emitted asyncio slow-task diagnostics in composed route tests; neither run failed. Full combined outputs, exact invocations, conditions, and SHA-256 manifest are retained in this packet.

These are selected local regression tests, not native blocked-I/O evidence, a live GUI/MAP01 task, WSLc evidence, or a reliability estimate. No application, GZDoom, WSLc, or Docker process was launched for this check.
