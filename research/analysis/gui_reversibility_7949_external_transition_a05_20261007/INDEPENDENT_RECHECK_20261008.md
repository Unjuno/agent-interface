# #8297 saved-evidence recheck — 2026-10-08

## Disposition

`HOLD_AUDIT_COVERAGE`. This is a post-hoc, read-only recheck of PR #8297 at
head `4b0d0e6f7b9553ea1a00422a777fc95e46eeab20`. It preserves every original
package and result unchanged. No candidate wrapper, one-shot auditor, or
container was rerun.

## A03 custody discrepancy

The retained A03 `STOP.md` declares the second-call raw SHA-256 as
`abcf391ce22ba973a0fe9abb19d15c8a03fbc606893afbf03f8a3b760d7f7e18`.
Hashing the committed `results/candidate.raw.json` bytes yields
`abcf391ce22ba973a0fe9abb19d15c8a03fbc606893afeb03f8a3b760d7f7e18`.
These values differ. The first invocation's stdout is described as retained
only in an execution-tool record and is not independently available in this
package. Therefore the mismatch is not corrected by substituting a new hash:
the recorded A03 custody claim remains unresolved. A03 already records two
candidate invocations, zero auditor invocations, and no scientific result;
this recheck does not change that STOP or infer a hypothesis outcome.

## A05 byte and outcome reconstruction

For A05, the committed candidate raw SHA-256 is
`e0472769b92b4fa0b8f41e31ec23b5bdd2d2d8485c21f29a08e785d10b6e497f`,
matching both REPORT.md and audit.json. The committed audit JSON hash is
`a15abb5dd9fe7b65577fa13fd01eb818c86305af278d699f4e61f5233908d4cf`.
All seven source/input files listed by A05 FREEZE.json match their declared
hashes. The three retained rows match the authored finite transitions and the
committed audit binds the exact raw hash.

However, direct offline mutation probes against the frozen `audit_core.verify`
return no errors for a duplicated case row, a fabricated recovery operation,
or a missing recovery sequence where the model requires one. These are
independent-auditor coverage gaps, not evidence that the retained raw contains
those mutations. Consequently the historical A05 PASS remains historical
output; this recheck does not independently accept its claimed gates.

## Other retained scope

A04 remains `HOLD_AUDIT` as recorded. A01/A02/A03/A04/A05 are kept as separate
immutable records. This recheck makes no GUI, application, runtime, authority,
authenticity, semantic restoration, or safety claim. It does not adjudicate
the unavailable first-call A03 stdout or repair the A03 digest discrepancy.
