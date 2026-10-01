# Cache artifact maintenance contract — first formal outcome

Issue #4029. **PASS_CACHE_MAINTENANCE_CONTRACT_SCOPED**, provided execution
container, one publicly hash-frozen allocation in two fixed24-case batches.
This extends a support assumption; it does not invalidate the original sink's
exclusive-output-directory contract or any previous replay result.

## Result

| Policy | Exact image | Wrong/invalid | Collision refusal | Reused | Newly created |
|---|---:|---:|---:|---:|---:|
| ORIGINAL |8|6|2|10|4|
| BYTE_PIN_REPAIR |14|0|2|2|12|
| PIXEL_CHECK_REPAIR |14|0|2|4|10|

Counts concern the second publication only. All48 first outcomes remain.
Initial publications and24 excluded rep100 construction cases are not pooled.
The original six wrong/invalid outcomes are the two truncated, two wrong-pixel,
and two wrong-geometry cached PNGs. They violate ONLY the newly proposed
maintenance contract, not the documented original ownership assumption.

Both wrappers rebuilt all six unsuitable cached artifacts, through the exact
unmodified ImageArtifactSink. Missing cache and changed-frame controls also
regenerated. All six occupied next-name sentinels refused without overwrite.

The two lossless re-encodings differed in encoded bytes but retained the exact
RGB samples and dimensions. BYTE_PIN_REPAIR regenerated both; PIXEL_CHECK_REPAIR
reused both. ORIGINAL also reused them correctly. This is a representation/work
count distinction, not a measured performance advantage or default choice.

## Execution and evidence

Intake main1f798cbb60b929e738c6bf8a5912470b38b45ff4. Full unchanged vendor files:
image_artifact.py blob73bb38b23b1857636c7cf1ddc5bd4a4e474def60;
exact_gate.py blobd2629bc94d40cc0a8e1bf9e053585549218629ed.

Public FREEZE commitd041be44cf98d141dcc070f52d6ff267e8cbaa38 and Issue comment
5767567392 preceded all formal cases. This published hash commitments; full
source bytes are delivered with this report, not falsely backdated as already
public. Freeze SHA256:
`114ddc8c1c45bb894ae8ea0fc5c5741c4a68df759d3fda78830fe4ab8d8a8af2`.

batch0 raw SHA256:
`d2f3337a59debfeb39b3f838287e99221bee2a0c767e4499bd75fa1fcd964a7b`.
batch1 raw SHA256:
`17f90d113868bb7a52f467b3834f73fc7c317b81a09c60515d174a6749651746`.

Each batch had24 real trial workers and21 separate read-only byte collectors.
All90 actor PIDs were distinct; actual child waits, both runner exits and both
supervisor shell exits are0, stderr empty. Postformal process-presence check
found no remaining actor. No formal retry, replacement, dropped row or source
change. Supervisor execution spans are diagnostic, not image latency.

Frozen raw-only independent audit:1434 checks/errors0; decoded PNGs with a
separate stdlib CRC/deflate/filter implementation, independently reconstructed
requested frames, checked retained actual files, responses and process/source
bindings. Audit SHA256:
`b5d72e691b8a9d77ca0de592a7c0adb9ab1c416e2af6fabb0d5ab3a4b89ebda3`.
Twelve semantic/type/source/process in-memory evidence corruptions reject in
each batch,24/24. Raw bytes stay unchanged. Same author/separate implementation
and process is not external human review or an independent trust root.

Four construction unit methods pass, covering all five PNG filters, CRC/tail
refusal, candidate behavior, full construction and twelve mutations. Construction
24-case raw and its original654-check audit remain separately retained. A
preformal metadata AttributeError for built-in zlib.__file__ and the draft
freeze are retained in CONSTRUCTION.md; corrected before public freeze, no
science re-execution and no wrapper-only successor.

## H / T / D / C / U and conditional argument

PLAN.md and PLAN.json retain full pre-result protocol, exact gates, controls,
field/unit table and conditional argument. H is the cache ownership/validation
boundary; T is the48-case fixed process/codec matrix; D is exact artifact and
refusal reconciliation; C is quiescent cooperative RGB storage; U includes
concurrency, color metadata, host/model utility and unmeasured validation cost.

Actual runtime: Linux x86_64, CPython3.13.5, Pillow12.3.0; version/binary/module
hashes in ENVIRONMENT.json. Docker/OrbStack CLI/image identity unavailable; not
an engine-replication or attested network-none result. CPU frequency/load are
uncontrolled; no timing benefit is estimated. No model/provider, GUI/input,
network experiment, user document, credential or shared-runtime mutation.

## Integration decision

Keep the existing exclusive-owner contract unless the integration owner
explicitly chooses maintained/shared artifact storage. In that expanded route,
file existence and a repeated Frame alone are insufficient artifact evidence.
A bounded completed-decode check can distinguish wrong cached samples from an
equivalent PNG re-encoding, under the tested quiescence assumption. This report
does not deploy a wrapper, infer model viewing, make a new input authority,
restore observation freshness or guarantee displayed colors with arbitrary
profiles. New helper state touches only its own sink instance.

The report closes only the bounded support-envelope question after evidence
integration. #2979/#3370/#2789 and the global ROADMAP are not closed by it.
Prior e58c matches existing #3978/PR #4024; no duplicate publication/allocation
was made. Parallel inode/FD/cursor/epoch/GUI work remains unchanged.
