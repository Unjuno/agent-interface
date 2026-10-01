# Recovery status: partial evidence, reproducibility HOLD

This additive recovery preserves the exact V2 files available on the remote
orientation branch at `170cde7b657cc394f96f5931a6949c807713bc01`. It does not
rewrite V1, claim a complete V2 package, or rerun either consumed allocation.

## Preserved evidence and limitation

The branch contains V2 metadata, `audit.py`, and encoded evidence fragments
`evidence.part00/02/03/04.b64`. Its `MANIFEST.json` describes 36 archived
members, including 2,562,794-byte oracle files for each formal allocation. The
fragment set is incomplete: `evidence.part01.b64` is absent. The exact V2
`run.py` is also absent; `SOURCE_IDENTITIES.json` records its expected size as
7,310 bytes, SHA-256
`65fdbad6f46e03d2e95fc29d78f3c1cb86e19211acf705b9780d61dadce4a9ca`, and Git
blob `9d45b9480d0f3ed5744a038fc45bba0830e95827`.

Consequently, the missing fragment prevents verifying/restoring the complete
manifest archive from this branch, and the missing runner prevents exact
source-complete reproduction. The Issue-reported V2 scoped PASS, V1
`FAIL_ORACLE_MISMATCH`, and their distinct allocation identities remain
historical reports; this partial package does not independently upgrade those
claims or satisfy the evidence-delivery gate.

## Verification performed for this recovery

- Confirmed every restored file is byte-identical to the source branch's Git
  blob; no predecessor file was changed.
- Confirmed the source branch has no `evidence.part01.b64` and no `run.py` Git
  object; therefore it cannot yield the complete manifest archive and frozen
  source set by itself.
- Preserved the branch's manifest, summary, reports, environment, source
  identities, auditor, and every available evidence fragment unchanged.
- No scientific process, Mindustry session, fixture acquisition, or formal
  allocation was run here.

Disposition: `HOLD_V2_EVIDENCE_FRAGMENT_AND_RUNNER_MISSING`. If the exact
missing fragment and runner are recovered, verify their published hashes
against the existing immutable manifest/source identities before making any
stronger reproducibility claim. Do not reconstruct them from Issue prose or
substitute V1 source.
