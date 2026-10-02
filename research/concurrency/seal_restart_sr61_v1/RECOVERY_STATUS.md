# Recovery status — 2026-10-01

The original source capsule restores 10 frozen study members without executing
them. Exact archive SHA-256: `b7e3b259329dfcd2642c7e225e254a5dcc2cd7f8883ebca6aafc071fc0ed34c0`;
expanded size: 45,993 bytes. The restored 10 contract tests pass and all three
Python files pass syntax compilation on the available host.

**Formal result publication: HOLD.** The original branch head retains only the
source/freeze package; it contains no formal raw DB/journal/wire/body records,
result capsule, or controls output. Issue #4332 reports a 24-case scoped PASS,
but those reported outcomes are not independently reconstructable from the
GitHub branch. This recovery does not claim that PASS as verified evidence.

No formal case or audit was rerun, no allocation was changed, and no raw rows
were inferred from the Issue summary. This source-only record preserves the
frozen implementation and explicitly leaves the scientific-result delivery
gate open. It makes no power-loss, production, or product claim.
