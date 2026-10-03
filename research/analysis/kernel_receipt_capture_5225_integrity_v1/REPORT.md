# #5225 additive capture serialization correction

**PASS_CAPTURE_SERIALIZATION_SCOPED.** The exact retained Git matrix uses LF and
hashes to `679cdc76a8d87812e49c003b0b14df12d7e433ddf77210190cc83e932333cd0f`.
Replacing each LF with CRLF, without any other byte change, produces
`a7f50a716b48313f2214da3cd097f1674225dc03ddbec74fefc81324453cb700`, exactly the
historical manifest pin. The matrix is byte-identical at the original #5232
merge `6195c0f762bfa333836242ae80fe2facdd5fb9ac` and intake main
`11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d`.

This is a supplementary integrity record. No historical file, hash, output or
scientific disposition is replaced. Missing `effect_at_900` and the conflicting
`effect_at_700` interpretations remain HOLD. No kernel experiment ran, and no
runtime adoption, GUI correctness, OS timing, performance or safety is claimed.

## Evidence and correction manifest

`FREEZE.json` pins 15 original Git blobs and their exact byte SHA-256s, the
canonical matrix hash and its explicit CRLF reconstruction. It is the additive
correction manifest; the original MANIFEST.json stays unchanged. All six original
study-source hashes and six frozen-input hashes match their LF Git bytes.
`verify.py` consumes exact Git objects rather than newline-dependent checkout
representations. `audit.py` is a separate implementation using independent
Git hash-object checks and a distinct byte reconstruction. It imports neither
the new verifier nor any historical study, kernel or probe.

Executed on Windows / CPython 3.11.9, one host CPU, no container/GPU/model/GUI.
Command templates, platform, UTC start/end receipts and first exit/output are in
`evidence/commands.json` and `evidence/canonical-export-command.json`.
Local absolute paths use `$PYTHON`, `$GIT`, `$REPO` and `$EXPORT` in the public
receipts; unredacted originals remain privately retained. PUBLICATION.json
records original/public hashes and the exact redaction scope.

| Verification | Result |
| --- | --- |
| Six byte-boundary regression controls | 6/6 pass |
| Supplementary exact-Git verifier | exit 0; 15/15 identities; 40 distinct retained mutation rows held |
| Separate report/Git-object auditor | exit 0; errors=[]; 5/5 actual corruptions refused |
| Original verifier on first Windows checkout | exit 1; matrix CRLF pin matches; all six checkout study-source hashes mismatch |
| Original verifier on a separate exact-Git LF export | exit 1; only manifest_matrix_hash_matches fails |

The first checkout result exposed a second representation boundary: the local
Windows checkout uses CRLF for the six study sources, whose manifest pins LF.
The original intake sources have preserved bytes. This first output remains
in `legacy-verifier.stdout.json`; it was not overwritten. The distinct canonical
export validation retains all exact Git inputs and reproduces the reported
single matrix-pin failure in `legacy-canonical.stdout.json`. Neither validation
invokes `run_audit.py` or the kernel probe; these are repeatable read-only checks,
not a consumed scientific allocation.

The hash relation and the historical runner's default `write_text` newline
behavior are consistent with Windows serialization followed by Git text
normalization. The relation alone does not prove the original capture's creation
chronology or recover an independently preserved pre-publication file.

## Reproduce

From a Git checkout containing the frozen source and historical merge objects:

```text
python -B -m unittest discover -s research/analysis/kernel_receipt_capture_5225_integrity_v1 -p test_verify.py -v
python -B research/analysis/kernel_receipt_capture_5225_integrity_v1/verify.py
python -B research/analysis/kernel_receipt_capture_5225_integrity_v1/audit.py research/analysis/kernel_receipt_capture_5225_integrity_v1/evidence/supplementary-verifier.stdout.json
```

Pass `--git` with the Git executable path when Git is not on PATH. The verifier
prints JSON and does not overwrite retained outputs. New files have a local
`.gitattributes` byte-preservation rule. `SHA256SUMS` binds the complete additive
package, excluding the checksum file itself.

## Intake deviations and delivery boundary

An exploratory byte comparison preceded the ordinary-repair freeze, as disclosed
in PLAN.md. No prospective scientific discovery is claimed. An overly broad
sparse-checkout add was interrupted before study execution; the two resulting
empty locks were confirmed to belong to this worktree with no active Git process,
then preserved under new names in its metadata. A narrow checkout recovered.
The initial Issue claim's pre-send local operation journal was omitted and was
recorded retrospectively; the accepted comment was not resent. These operational
errors do not alter the original evidence or study result.

PLAN's no-shared-index-edit intent was adjusted only for the single necessary
generated navigation row for this new retained REPORT; all prior index rows are
preserved. No workflow is changed. Main delivery still requires FINAL-v5 fixed
non-author content review and conditional application. This record does not
close #5215/#5225/#5229 or satisfy the distinct raw-row adjudication gate in #5229.
