# V39 per-key measurement consumer A05

A05 is a separate offline identity-type follow-up to A03. The A03 candidate
and independent auditor accept an up-row step of `2.0` when the down-row step
is the integer `2`. They also accept a down-row integer `1` paired with up-row
boolean `true`. A05 requires both rows' program ID, step, owner, intent, and key
fields to have their exact expected types before comparing identities.

The retained A03 pair is read-only and remains unchanged. A05 has its own
candidate, independent raw reconstruction, mutation tests, freeze, and audit.
The four regression methods pass in normal and optimized Python. The audit
passes and confirms the A03 source and raw input hashes remain unchanged.
Stack refs, source freeze identity, and validation output are in
`results/a05/COMPOSITION.json` and adjacent result files.
No physical key duration, application effect, live feedback, game, recovery, or
MAP01 claim follows from this narrow source-contract check.
