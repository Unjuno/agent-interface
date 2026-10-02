# Recovery status for #4190 source-lifetime crash study

The original four-file source-freeze capsule is preserved unchanged. Its
base64-decoded archive is 10,324 bytes with SHA-256
`15e5e22a3972db6bb47a41e513dbf74a26579d7f5f504a8bc9b86874e25ec1da`, matching
the manifest, and contains 15 source/gate/construction files. This capsule was
created before formal execution (`formal_started: false`); it is not the
formal-result package.

The Issue later reports a 20/20 `PASS_SOURCE_LIFETIME_HANDOFF_SCOPED`, a
20/20 raw audit and 10/10 corruption controls. The formal raw/results are not
present in this branch or the preformal capsule, and the Issue's Actions-run
recovery notes say the formal artifacts were not available for retrieval.
Therefore the PASS remains an Issue-reported claim and is not independently
reproduced by this recovery. The capsule includes construction audit/control
summaries, but not their case-level RAW trees; its `test_audit.py` expects those
external RAW trees and cannot be used against the archived files alone.

Disposition: `HOLD_FORMAL_PACKAGE_MISSING`. No formal experiment was rerun and
the result was not reconstructed from hashes or summaries.
