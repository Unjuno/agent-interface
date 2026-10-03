# Publication recovery and forensic qualification

Source: `research/amendment-effect-6219-t0-cpu-20261002` at
`c9743221a9478b0a7d2bb3cbf9cd4cde87ca9cb3`, Draft PR #6644.

## What changed the previous recovery STOP

All fourteen published blobs are invalid UTF-8. Re-encoding each blob as
base64 exposes the same leading ASCII `t` followed by an intelligible base64
payload. Removing that leading symbol and decoding with added padding yields
readable UTF-8 without replacement characters. This is an observed reversible
publication pattern; the exact publishing command/cause is not established.
Earlier claims of literal stored U+FFFD characters are contradicted by the
actual Git blobs and the reconstructed text, and are not promoted here.

The inverse can lose a trailing byte. It is accepted as exact recovery only
when the decoded prefix, or that prefix plus one of 256 possible single bytes,
has a unique match to a pre-existing declared SHA-256. Nine frozen source/input
hashes and the two PR-recorded output hashes all match. README, test_method.py
and candidate_raw.json require the trailing byte `0x0a`; this is selected by
hash equality, not by guessing textual content. The audit output matches
`8fde90b8353467faacd89e5407611d6bceafcdd9c1da26aa0c2ccaf4485c3023`;
raw matches `23012f286e31b6e96d1b7ad5167d0ef36dba2bb050c80efc2bff8e38986ba376`.

The recovered freeze's reference table is itself a decoded prefix without an
external byte-level digest. Its nine hash declarations provide internal
source-consistency checks, while the two independent PR-body digests provide
external output references. Neither proves host attestation or a pre-run
timestamp by itself. FREEZE.json, RUN_RECEIPTS.json and RESULT.md prefixes have
no pre-existing complete-byte hash here; they remain explicitly unbound and
are stored as `.decoded-prefix.txt`, not silently declared fully restored.

## Historical failure remains failure

The hash-bound fixture replaces an already completed irreversible `download`
effect with `archive` while the oracle labels it an addition and expects
continuation. The independent rule reports impossible-to-fully-satisfy. The
retained audit says `METHOD_FAIL` with `ORACLE_CONTRACT:case_addition` across
36 rows. Retrospective function-level replay of the saved raw must match that
entire audit result, not make the method pass. Original three construction
tests exercise a separate small fixture and are not proof that the formal
contract passed.

No formal command/allocation is repeated and no historical result is edited.
No runtime, GUI, model, product, safety or benefit conclusion follows.

## Delivery/custody checks

`RECOVERY_MANIFEST.json` maps all 14 original Git blob IDs and SHA-256 values
to preserved binary files, and records each derivative's identity and binding
status. The deterministic inverse and unique-match search are retained in
`recover_publication.py`. Tests rederive every prefix, verify all eleven
reference-bound restorations, and reproduce the exact stored METHOD_FAIL
through the separately implemented checker function. Package-local `-text`
prevents byte changes across platforms. Original binary evidence and complete
source commit are retained before any superseded branch/PR is retired.

The first local whitespace gate flagged trailing blank lines in the recovered
original oracle_truth.json and run_audit.py. Their pre-existing SHA-256 values
include those exact bytes, so they are intentionally preserved rather than
trimmed. Recovery-owned edits are checked separately from the eleven original
hash-bound files. The warning stopped delivery before commit/push.
