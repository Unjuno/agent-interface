# Same-revision autosave and explicit Submit — #4373

**PASS_SUBMIT_PURPOSE_BOUNDARY_SCOPED**, research evidence only.

One publicly source-frozen 40-case/92-request SQLite process allocation completed
with all80 actor/observer exits and the outer runner exit0. No formal retry,
replacement, exclusion, postfreeze edit, GUI/model/native input or runtime change.

| Policy | Cases | Requests | Document updates | Explicit submission records |
|---|---:|---:|---:|---:|
| Exact REVISION_ONLY |20|46|24|4|
| SUBMIT_EVENT |20|46|24|10|

The extra six records represent a distinct SUBMIT after AUTO already stored the
same revision/value. They do not rewrite the document. Exact job replay remains
idempotent; stale/conflicting/foreign/Boolean requests refuse. The original sink
remains correct for its narrower document-revision contract. New submission
records are private database events, not external business effects or input authority.

Source/plan/cases/environment were published and read back before execution at
`f60def520eb3737e84528ed403fb35b0b866da2e`; Issue#4373 comment5832598338 precedes
formal execution. First result: comment5832615366. Separate raw-only audit1248
checks/errors0; twelve effective rehashed mutations rejected normally; twelve
excluded unit methods. Same-author separate implementation/process, not independent
human review. REPORT.md and the unchanged PLAN.md specify H/T/D/C/U and limits.

## Complete new evidence; offline reproduction only

Six base64 parts and PACKAGE.json restore all199 original source/raw/construction/
process/result files,1,326,886 member bytes. XZ33,112bytes SHA256
`412125941620027e27a5dca2d36a10e513fc485bcfbaa0bdd3dc853412e530c3`.
Fresh local restoration matched every member and reproduced AUDIT/CONTROLS
byte-for-byte; ten package tests passed. Local checks are not GitHub CI.

From this directory, choose a destination that does not exist:

```sh
python -S -B test_restore.py
python -S -B restore.py /tmp/submit-purpose-new-review
cd /tmp/submit-purpose-new-review
python -S -B audit.py formal-01 > /tmp/submit-purpose-audit.json
cmp AUDIT.json /tmp/submit-purpose-audit.json
python -S -B mutations.py formal-01 > /tmp/submit-purpose-controls.json
cmp CONTROLS.json /tmp/submit-purpose-controls.json
python -S -B test_contract.py
```

Do not rerun consumed run.py. The restorer executes no study. Source/destination
parents must be trusted and quiescent. Integrity digests are not authentication.

## Preserved predecessor and adoption limit

#4368 records the older16-session GUI allocation and its unchanged re-audit.
Its complete1,843-file corpus is NOT inside this new199-file package; only the
exact required old sink and re-audit metadata are included. Do not infer full
predecessor publication from this PR.

Provided Linux/x86_64,CPython3.13.5,SQLite3.46.1,stdlib,DELETE/FULL/BEGIN IMMEDIATE;
no Docker/OrbStack image attestation. One trusted epoch/document and retained job
identity. No restart/epoch reuse,multiple editors,power-loss,external-effect
atomicity,GUI/model integration,token/latency benefit or production promotion.
The application owner must define whether Submit means more than saving bytes.
Global ROADMAP remains uncompleted by this experiment.
