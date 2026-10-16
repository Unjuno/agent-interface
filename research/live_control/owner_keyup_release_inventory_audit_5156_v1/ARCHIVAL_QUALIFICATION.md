# Archival qualification: release-inventory audit construction

## Disposition and immutable origin

Preserve all 24 published files from [source PR #5502](https://github.com/Unjuno/agent-interface/pull/5502), head `6b8d19df1ecedbc7f7eb84b029dd9e3b3f060c7b`, directory tree `af34544171faa8ec6cccddeba5d19ce799e44431`. The originals total 134,967 bytes and retain their paths, 100644 modes, Git blob identities, mixed line endings, reported results, and earlier limitations. This separate note qualifies the archive without modifying any original.

This is historical host-construction preservation. No archived code, test, runner, auditor, or mutation control was executed during preparation. Historical PASS/test/process claims below are attributed records, not fresh reproduction or independent authentication of the historical environment, source mounting, invocation count, or process separation.

## Retained results and failed boundaries

The original [RESULT.md](RESULT.md) reports `PASS_RELEASE_INVENTORY_AUDIT_CONSTRUCTION_SYNTHETIC_ONLY` for the exact-byte fake-Xlib run, with 14/14 owner tests, seven rejected omission/corruption controls, six matching key requests, seven XSync calls per owner version, empty fake key state, and three neutral terminal records. Retained raw SHA-256 is `019fb0fb2a01c3064ea8e88e8ad176b059f75cb67b201f444aeee08518dfe592` in [RUN_BYTE_IDENTICAL.json](RUN_BYTE_IDENTICAL.json).

The [prefreeze notes](PREFREEZE_NOTES.md) and [execution notes](EXECUTION_NOTES.md) retain an initial fixture-reference failure, earlier exploratory execution, and an execution copy whose line endings had been normalized. [RUN.json](RUN.json) and [AUDIT.json](AUDIT.json) remain separate from the later exact-byte output. The original plan says no retry, while the result describes an exact frozen-source rerun. Preserve that chronology and original wording; this archive neither reconstructs unretained process receipts nor independently certifies one-shot compliance. Original CRLF owner sources are unchanged.

The original v1 audit trusts the submitted `v10_v11_behavior_equivalent` Boolean rather than comparing both request arrays. The [reported copied-evidence counterexample](https://github.com/Unjuno/agent-interface/pull/5502#issuecomment-5912617474) changes the arrays to contradictory values while preserving that flag and still obtains errors=[]. This limits the request-parity subgate; it does not prove the pristine raw arrays were corrupt.

The additive [v2 report](audit_v2/REPORT_V2.md) records `PASS_REQUEST_SEQUENCE_PARITY_AUDIT_V2`, six focused tests, five rejected corruptions, and no pristine errors on the same retained raw. It rechecks the six-request sequence and strict integer types; it is same-author audit implementation, not independent human review. It does not replace v1 or promote all other audit subgates. The [later source-PR comment](https://github.com/Unjuno/agent-interface/pull/5502#issuecomment-5913192138) records subsequent retained-audit/test revalidation; those are historical claims, not executions performed for this archive.

## Frozen-document mismatch preserved

Static checks at the source head matched 10 of the 12 original `FREEZE.json` hash entries. Two documentation entries differ:

- `PREFREEZE_NOTES.md`: frozen `9a6a717319e2703c8b8f12e94f3ea8c6c2060e59eb8abfe8b0815622ff4f9272`; retained `1efbb2beaa4af8c00df57fb3c72dba305e8a1f5d15409e50414ca639b9de0c5c`
- `RESULT.md`: frozen `08d6fa559befb53b6bb9c4d948712db94a3dc48a6259946c5c210297f3c2e1ec`; retained `265cf06c2705239ff82fcc0ebfab7ecfb27074babe30a174091cddfe4752d474`

Both frozen values match their exact earlier files at [freeze commit 31976c4](https://github.com/Unjuno/agent-interface/commit/31976c4321e79dcc8afd3dd3cf28f1a7f6f680e2), where RESULT.md states NOT RUN. Git history records the notes update at `301bd14ad24dcd54b4bd87b3fe6352a8fef28fdf` and the later result update at `709cd77378e623f143eb89a98871740b47a5cdeb`. Thus the current tree must not be described as matching every v1 freeze entry. The archive preserves the stale freeze and later documents unchanged; no source-hash repair is inferred. All five `audit_v2/FREEZE_V2.json` artifact-hash entries matched.

## Coverage and owner boundary

At inspected main `4cf0a3dfde1219671b671bf0a9079a11dcb2e159` on 2026-10-01, this entire namespace was absent. Shared owner blobs elsewhere, the #5298 archive, and the separate #5415/#5467 archives do not preserve this package's 24-path provenance. Complete nontruncated source-tree enumeration and reconstructed Git blob identities verified all 24 originals. Hash agreement establishes bytes only.

No live X11, physical key-up, application consumption, held-input occupancy, MAP01/task effect, efficacy, safety rate, recovery quality, human tempo, or runtime promotion follows. The [owner issue #5156](https://github.com/Unjuno/agent-interface/issues/5156) remains separate; its [2026-10-01 integration-boundary check](https://github.com/Unjuno/agent-interface/issues/5156#issuecomment-5939309038) leaves the live nested-bracket gate unevaluated and a future allocation request ungranted. Later [PR #6260](https://github.com/Unjuno/agent-interface/pull/6260) is a separate synthetic construction package.

Source PR #5502 was open/Draft at inspection. Publication of this qualified archive does not ready, merge, close, reopen, or delete that PR/ref, clear owner gates, grant resources, or authorize a rerun. Recheck current owner/source/main state before later publication or disposition.
