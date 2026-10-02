# vj01 source-only preservation for #5274 / #5282

## Disposition

This package preserves 14 original source, fixture, plan, freeze, auditor and construction-test files (70,641 bytes; 13 distinct Git blobs) from branch `research/verification-evidence-5274-20260929-vj01` at `2a9ebfb0af252f55dbf195567886f8905ff480e3`. It adds an archive under an existing namespace; it does not modify the original paths, source ref, frozen source or current runtime.

- **Generic vj01 #5274:** `STOP_DUPLICATE_SCOPE_BEFORE_FORMAL`, formal invocations 0. The original 534-case / 2,496-schedule freeze is preserved, not restarted or repurposed.
- **Distinct #5282 namespace allocation:** the owner reported `PASS_VERIFIER_LOCAL_ID_NAMESPACE_SCOPED` after a consumed one-shot run, but its exact raw/process/audit/construction packet is absent from this branch. Delivery remains **HOLD_RECOVERY_INCOMPLETE / historical result not independently verified here**. The reported raw is 47,644 bytes, SHA256 `92ead437d67d30a8d75fbfe329fc6dd692741ac2ba11ee763d604b15e4086d15`. No raw is reconstructed from summaries.
- **Canonical general reducer #5274:** this is a different allocation, already merged through [PR #5283](https://github.com/Unjuno/agent-interface/pull/5283). Its formal evidence is present on current main at `research/verification/evidence_reducer_5274_v1/`. It must not be confused with vj01 or called missing solely because vj01 has no raw.

Issues #5274, #5282 and #5267 remain open. This is a source/STOP preservation PR, not a verified-result delivery, execution authorization or scientific promotion. No experiment, construction test, formal candidate, historical auditor, GUI, model or resource allocation was run by this rescue.

## Lineage and source records

1. [Original generic vj01 ownership and plan](https://github.com/Unjuno/agent-interface/issues/5274#issuecomment-5891232518)
2. [Generic scope collision and zero-formal STOP](https://github.com/Unjuno/agent-interface/issues/5274#issuecomment-5891528179)
3. [Distinct namespace placement](https://github.com/Unjuno/agent-interface/issues/5282#issuecomment-5891555478)
4. [Namespace exact freeze](https://github.com/Unjuno/agent-interface/issues/5282#issuecomment-5891688790)
5. [Owner-reported namespace first outcome](https://github.com/Unjuno/agent-interface/issues/5282#issuecomment-5891708365)
6. [Namespace publication HOLD and no-rerun boundary](https://github.com/Unjuno/agent-interface/issues/5282#issuecomment-5921221465)
7. [Later #5274 branch audit requiring lineage qualification](https://github.com/Unjuno/agent-interface/issues/5274#issuecomment-5953260892)

The stopped generic preparation's 12/12 construction checks, earlier DNS/missing-source setup failure and namespace construction-v2 6 tests are historical statements from the linked records; their absent raw logs are not manufactured or called independently recovered. This archive leaves those first outcomes unchanged. The later #5274 audit's claim that its canonical formal REQUESTS/RESPONSES were absent is corrected narrowly by the current-main byte observations below; #5282's separate missing-packet HOLD remains valid.

## Exact preservation and static verification

[MANIFEST.json](MANIFEST.json) maps each original source path to `original/<source_path>`, Git blob, byte count and SHA256. All 14 source blobs were fetched at the immutable head, materialized and rehashed. All 12 entries in the two frozen file maps agree in Git blob, SHA256 and byte count. Two paths intentionally use the same unchanged reducer blob.

[HISTORY.json](HISTORY.json) records all seven branch-only commits and each changed-file blob. Every change is an addition and every added blob remains unchanged at the source head, so there is no intermediate version omitted by the final 14-file mapping. This file is provenance metadata; the source commit ancestry is not merged into main. Retain the original branch and all original commits.

[VERIFICATION.json](VERIFICATION.json) also records a static, in-memory reading of the existing canonical #5283 archive from main `9a327d0511f02c7b8ebd175e20f96a43028578ca`: all six parts match Git blobs; the combined archive is 68,036 bytes / SHA256 `7fb949e3fe109494377d1b108212876c4b4d5d703f13758bfb59d3a999b99016`, with 44 members. Its formal REQUESTS and RESPONSES hashes match the original #5274 claim. No archive member was executed, and this check does not rerun or independently validate its scientific semantics.

To independently check this archive without executing research code, from this directory run:

```python
import hashlib, json, pathlib
root = pathlib.Path('.')
manifest = json.loads((root / 'MANIFEST.json').read_text())
for entry in manifest['entries']:
    data = (root / entry['archive_path']).read_bytes()
    assert len(data) == entry['bytes']
    assert hashlib.sha256(data).hexdigest() == entry['sha256']
    assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == entry['git_blob']
print('Preserved bytes verified; no research code executed')
```

## Publication boundary

Publication base main: `89c67103de1e3061ff070c62825dac12041c5333`. The source ref is unchanged. This archive is not placed at either historical active-allocation path. No tag, source-branch restoration, deletion, workflow edit, allocation rerun or dispatch is performed.

[WORKFLOW_SAFETY.json](WORKFLOW_SAFETY.json) records all 227 exact current-main workflow identities. Archive paths match no branch-push or main-push workflow. The broad create and formal-PR workflows have exact-other-branch guards that are false for this rescue branch. Opening the PR can run only the existing deterministic replay unittest gate; it is not a scientific allocation. Fresh hosted check state and exact-head review remain separate delivery gates.

## Remaining recovery need

Find the existing exact #5282 raw/process/audit/construction packet through an authorized source and compare it to the published freeze and raw hash. Do not regenerate it, rerun the consumed allocation or promote the historical PASS on the strength of this source-only archive. The branch-only source is now reviewable without treating missing formal evidence as recovered.
