# #7505 mode-flap evidence rescue reconciliation

This additive reconciliation preserves the original A01/A02 candidate, raw
data, frozen v1 auditor failure, post-run v2 result, STOP record, and first
publication hash ledgers. The original ledgers are retained as
`SHA256SUMS_FIRST_PUBLICATION.txt` and, for A02,
`MANIFEST_FIRST_PUBLICATION.json`; no candidate or raw evidence was rewritten.

## Independent checks on the exact published branch head

- Source head: `d228ce126dfd25d95695773c7fb4bc032dd0471d`.
- A01 first-publication `SHA256SUMS`: three declared hashes differ from the
  committed bytes (`formal_a01/candidate.end.json`, `candidate.start.json`,
  and `candidate.stdout.txt`). A01 remains `STOP_INFRASTRUCTURE` before
  candidate creation; it was not retried.
- A02 first-publication `SHA256SUMS`: ten mismatches, including
  `audit_v2.py` and the saved candidate/auditor start, end, and output
  receipts. The independent `MANIFEST.json` also disagrees with the committed
  bytes for those ten entries. The exact first-publication files are retained
  above rather than silently overwritten.
- The frozen `formal_a02/raw.json` matches its declared SHA-256
  `405e0c14bbae201628ed32840eac2dbd069335a6191893fffc47debe017425b7`
  and byte count. Its 288 episodes / 23,040 event rows were not regenerated.
- Re-running only the saved read-only `audit_v2.py` against the frozen
  `fixture.json` and `raw.json`, with output directed outside the evidence
  package, exits 0 and reproduces the saved `formal_a02/audit_v2.json` byte for
  byte (SHA-256
  `64de20c24f117052149cfb390f49e78fd99652e7e74b8007ca50b90938d2d955`).
  It reports `HOLD_AUDIT` because the candidate alarm map is incomplete for all
  288 episodes, and `FAIL_METHOD_SCOPED`; mode-flap does not beat all named
  comparators. The frozen v1 failure remains the original formal disposition.

The reproducible raw replay supports the scoped post-run analysis, but the
first-publication mismatches mean the historical start/end/stdout receipts are
not independently authenticated to their earlier declared hashes. No new
candidate, formal allocation, Windows/GUI input, or live experiment was run.
This package is evidence preservation and audit reconciliation only; it is
not a positive method result or runtime adoption claim.

The current `SHA256SUMS` and A02 `MANIFEST.json` are reconciled inventories of
the exact bytes present in this rescue commit. Their first-publication
counterparts remain available for forensic comparison.
