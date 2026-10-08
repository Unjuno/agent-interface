# T11 preregistration — T7 publication bytes, auditor regression follow-up

Preregistered before the sole formal T11 CLI invocation. This is an offline, read-only continuation under the existing #6975 question and open evidence PR #6983. It does not create a new Issue, edit T7/T8/T9/T10 results, or rerun the WSLc allocation.

## H / T / D / C / U

- **H (hypothesis):** T10 stopped because its auditor classified each of the 11 files into an output list but failed to retain `classification` on the corresponding `by_name` row. That is the direct cause of the `KeyError: 'classification'` in manifest verification. T11's one-line data-flow correction will let the frozen 11-file snapshot complete; expected classification is 0 exact-source files and 11 source-plus-CRLF files.
- **T (test):** Use the already-frozen snapshot for immutable T7 PR #6983 head `684831240f9848e850736781edb98322949e8d8a`, exactly the 11 entries under `research/analysis/wslc_retained_audit_5309_t7_20261003/`. Run the formal command exactly once: `python -B audit_publication.py --input inputs/t7_remote_blob_manifest.json`, using Python 3.12.10. Candidate trials=0; WSLc executions=0; Docker executions=0; formal invocations=1; retries=0. The input is the T10 snapshot copied byte-for-byte; T11 makes no new GitHub fetch.
- **D (decision rule):** `PASS_T7_PUBLICATION_BYTES_CLASSIFIED` is accepted only if the one invocation exits 0, validates all 11 frozen local source lengths and SHA-256 values, validates every remote Git blob as exact-source or source-plus-exactly-CRLF, verifies all six source-manifest checksums, and reports the frozen expected counts (0 exact, 11 source-plus-CRLF). Any exception, exit 1, mismatch, or different classification is recorded as the first T11 STOP/FAIL with no retry.
- **C (controls):** The immutable T7 PR head and remote blob IDs/byte counts are fixed in the input snapshot. The exact local/public source bytes and checksums are embedded in that same snapshot. T10's first formal STOP and T7's original formal STOP remain historical controls and are not rewritten. T10 was never rerun as a formal audit; its `KeyError` was reproduced only by T11's pre-freeze regression test.
- **U (uncertainty/scope):** A T11 PASS classifies only these 11 artifacts and six manifest claims. It cannot identify the publication step that caused a byte change, establish connector-wide behavior, revise T7/T8/T9, validate the scientific claim behind T7, compare Docker with WSLc, or support any performance or memory conclusion.

## Frozen execution materials

| Material | Bytes | SHA-256 |
|---|---:|---|
| `audit_publication.py` (T11) | 7,575 | `4b7d16949d0a1d54269932387c0a09b8a714cd9a7e0bff88c419bf6924bda7a0` |
| `test_audit_publication_v2.py` | 3,121 | `2c26536dc28acb6be088e51c09dc87af059fa6fa57bf1071655a4bcfec024e5e` |
| `inputs/t7_remote_blob_manifest.json` | 33,398 | `82edb155d9452a28ddbd1d6cb7bb76a74e7496cf44826ddc6de51c037a48c444` |

The input's byte length and SHA-256 were independently checked against T10's copy and are identical. It contains the complete 11-file source-to-remote mapping, pinned commit, source base64, source hashes, Git blob IDs, and remote lengths. T10's auditor (7,528 bytes; SHA-256 `c03edbb3f22a85e80f01c46c67f5544888f0feb5f811365e4dcd0efc24d6f316`) is preserved unchanged in its T10 directory. T10's first formal invocation exited 1 with `KeyError: 'classification'` at manifest verification; this remains T10's formal STOP.

Before this freeze, the T11 nine-test suite was run once against T10's unchanged auditor and reproduced that regression (one expected failing regression test; eight tests passed), then once against the T11 auditor and all nine tests passed. Those are construction/regression checks, not formal T11 invocations. No source, test, or frozen input changes are permitted after preregistration; a needed change requires a separately versioned successor.
