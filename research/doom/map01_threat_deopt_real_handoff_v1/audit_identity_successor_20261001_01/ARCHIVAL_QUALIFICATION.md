# Archival qualification: retained T0 provenance STOP

This append-only qualification permits preservation of the original PR #5878
package as a terminal failed-provenance record. It does not make the package a
verified successor, replace the formal auditor, authorize execution, or change
any frozen source, plan, result, or historical checksum list.

## Retained outcome and source discrepancy

The allocation remains `STOP_LEGACY_SOURCE_HASH_MISMATCH`. Its candidate and
new auditor were each reported invoked once on six synthetic rows. The local
`PASS_AUDITOR_IDENTITY_BINDING_SCOPED` and legacy mutation outputs do not satisfy
the allocation-level source-identity condition and are not formal/live results.

Static verification of the published bytes at original head
`f75c9a4bfd8ebaa5f39f5219a74c698780bf16b1` confirms all 14 historical
`SHA256SUMS` entries. `legacy_audit.py` hashes to
`14a5f6a8c7a5ba208aa15d24b983735486e29f8519a817cf640399b5314e950d`.
The exact original auditor identity is
`7ab3d8895c9e8d7c80cf4ff463bac0623fb39247f8aa0d65f34941a1f8c48a40`.
The latter is recorded consistently in this package's frozen files and the
original #626 freeze, and is independently confirmed by hashing the retained
`legacy_audit_exact.py` from the separate T1 package on main
`b6c16aa4e505f6bc2c206bf9d078e3042be91ce9`. No auditor was executed for this
qualification.

The PR body and [owner comment 5926518661](https://github.com/Unjuno/agent-interface/issues/626#issuecomment-5926518661)
contain a separate one-character transcription error in the expected hash:
`...0d65d349...` should read `...0d65f349...`. The original narrative and frozen
files are retained. Correcting that narrative typo does not repair the actual
T0 legacy-source mismatch or change its STOP.

## Distinct successor and scientific owner

[PR #5883](https://github.com/Unjuno/agent-interface/pull/5883) separately
preserves the exact-source T1 differential under
`../audit_identity_successor_20261001_02/`; it merged as
`8da9346c3505673256f96a0d967b3325149dc16c`. That T1 result and its publication
correction do not overwrite, retrospectively authenticate, or erase this T0
STOP. The `_01` package was absent from main at the archival review; T1's reuse
of selected input bytes is not preservation of the whole T0 failure record.

[Issue #626](https://github.com/Unjuno/agent-interface/issues/626) remains the
open scientific owner with formal sessions at 0/6. No runtime, Docker, guest,
GUI, model, input, candidate, auditor, or source-capsule invocation is authorized
by archival integration. No scientific, benchmark, efficacy, or product claim
is promoted. Any future research remains separately authorized and gated.

`ARCHIVAL_INVENTORY.json` records the original 15-file published inventory,
including the historical checksum list. It is a current custody inventory,
not a replacement freeze or evidence of recovering additional historical bytes.

The earlier Draft/do-not-merge wording continues to prohibit treating this
package as verified research. With this qualification, repository integration
is preservation-only through ordinary review and CI gates; it does not close
Issue #626 or satisfy its formal execution gates.
