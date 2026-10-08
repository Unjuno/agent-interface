# Recovery status — Issue #4265

## Disposition

This is an archival recovery of verifiable preformal material from the orphaned
remote branch `research/partial-multikey-recovery-2129-20260923`. It is not a
new experiment, a recovered formal-result package, or a change to the recorded
`HOLD_AUDIT_CONTROL_HARNESS` disposition. Do not interpret the 30/30 rows as a
scoped PASS: the frozen control harness failed its mutation-rejection gate.

## What was recovered and verified

- The exact `SOURCE_BUNDLE.b64` object from commit
  `7c58061ebed1e6d41a1357f7a1ea93b596b36907` decodes to the declared xz archive
  SHA-256 `68022009b3a486d50bdbf0d0664a2e6d2c0687afff7591d90eab8caee4d60bc1`.
- Its member list and all five frozen science-source files (`app.py`,
  `runner.py`, `audit.py`, `controls.py`, `PLAN.md`) were independently read
  from the archive. Each member SHA-256 matches `FREEZE.json` exactly.
- `FREEZE.json`, `SOURCE_BUNDLE.json`, `V2_EXECUTION.md`, and the evidence
  fragments are retained as their original Git contents; the historical
  branch is not rewritten.
- Evidence fragments 00–04 are recovered from historical commit
  `7c58061ebed1e6d41a1357f7a1ea93b596b36907`; fragments 05–07 are retained
  from the orphan branch tip `4876a6187118255904f7eb4a82b80815ef5c7bcb`.

## Evidence archive remains unrecovered

The Issue records the lossless archive as 54,980 bytes with SHA-256
`6bebe07dd4a9601c16baebf64ee180faf20dce1049dc09f914c2d7db756de91d`.
Concatenating the exact fragments in order yields 73,309 base64 characters,
54,981 decoded bytes, and SHA-256
`422fba61fde08299ed1dac6f6a6cd9f297e5a5b8296cb1fb2cd625a8c24e1fe4`.
Fragment 02 is 10,001 base64 characters (the other full fragments are 10,000),
so the concatenation has a one-character boundary anomaly. As a diagnostic
only, dropping its trailing character yields the declared decoded byte count
but SHA-256 `21df3929463681a4861b36ac29b03a72f7bf4463f08d79390d39a984c4ac52d6`,
still not the declared archive hash. No fragment was edited and no guessed
reconstruction is accepted as evidence. The complete raw results, process
records, audits, and archive remain missing from this recovered capsule.

## Integration boundary

Only this additive, clearly qualified capsule is suitable for review. Do not
merge the orphan branch wholesale: it is based on an obsolete tree and its
tip contains only fragments 05–07, while the exact source bundle and earlier
fragments exist only in its history. Do not delete the orphan branch until the
repository's retention/dependency policy explicitly permits it. No allocation
was rerun, and no formal gate was reopened.
