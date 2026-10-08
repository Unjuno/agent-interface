# InputOwner v12 physical-edge telemetry — offline mechanics result

Task `INPUT-OWNER-V12-OFFLINE-IMPLEMENTATION-20260918-002`, Issue #998.

## Decision

**`PASS_INPUT_OWNER_V12_OFFLINE_MECHANICS_SCOPED`**, with one explicit post-primary audit-coverage limitation described below.

This is source/offline/mock evidence only. No X11/Xvfb/XTEST/GUI/model/provider/network/task-input/live authority was used.

## Frozen sources and scope

BASE `3c34e3cea2a39e961e097b41444ff4a7563a4170`; reservation branch `research/input-owner-v12-offline-20260918-002`.

Pinned parent identities:
- InputOwner v10 Git blob `341b3c01649943ddaad5f28431a792c4889cc36e`;
- InputOwner v11 Git blob `842071284156d3ccc647f47135ee62a9e512cb56`;
- #994 press bracket blob `9dcb1890b955019dd3880c1b09689213bbb84a58`;
- #992 release bracket blob `15008b58e5389b2e1d3b530abf029982686e6bc0`;
- #996 dual-edge adapter blob `a1344409ea6383c6394e991ac0b59fa7689978ef`;
- #1048/#1054 auditable physical-hold identity model blob `bdf68b88111ddb61297cdec29be394d7fd4dd060`.

The v12 scientific source was source-first frozen before primary. `input_owner_v12.py` SHA-256 is `b63e8a925a5ff741385fb69b8cf20ac07e01a520f34607778d8d28a0256c1508`.

## Mechanics retained

The research-only v12 keeps v10 focus/lease/cancel/expiry/pointer and ordinary key admission semantics and adds only ordinary-key measurement/lineage mechanics:
- best-effort pre/post keymap samples inside the same serialized owner request at the #1035 ordering points;
- a stable owner-local physical-hold `actuation_id` following the #1048/#1054 lifecycle;
- #994/#992-compatible physical DOWN/UP status/interval classification;
- exact-lineage #996 composition compatibility;
- aggregate verified cleanup may terminate an active lineage but does not fabricate a per-key cleanup physical edge.

Sampling failure removes measurement evidence only; it does not change an otherwise valid control decision.

## Excluded construction

Actual v10/v12 fake-backend owner-thread fixed tests: **10/10 PASS** after one construction-only harness repair: matched baseline/candidate lease deadlines were frozen to one identical value instead of being generated at two different wall times.

Excluded toy random construction: 500 sequences / 3,175 events; control mismatch0, measurement mismatch0, identity mismatch0, parent mismatch0; 109 exact-lineage physical actuations composed. Primary seed was untouched.

## Primary first outcome

Frozen seed `99820260918002`; one invocation; reruns0.

- sequences: **120,000**
- events: **778,607**
- baseline/candidate control mismatch: **0**
- candidate/oracle measurement mismatch: **0**
- identity lifecycle mismatch: **0**
- parent-contract mismatch: **0**
- unsupported/false physical intervals: **0**
- authority errors: **0**
- cleanup per-key edge laundering: **0**
- exact-lineage composed physical actuations: **26,167**

Primary RESULT SHA-256: `6ae5aa92e1eedf802aa9f215c0b1608a8ae769b02aa37b2155b0a334450c2792`.
Frozen audit: `audit_pass=true`, errors `[]`; AUDIT SHA-256 `20fef1d34892ee4694acea82688d0a6661cf0f311af64fc6ab8f645689a87c81`.
Frozen-source post-primary rehash: all exact; SOURCE_REHASH SHA-256 `369a6094de815cd49b9d00eabc24d38f2415b025d0d4ef130e8cef1b4220ddae`.

## Integrity limitation retained, not hidden

Post-primary copied-result corruption checks exposed a narrow limitation in the frozen summary auditor. It rejected decision-critical mutations 5/5, but replacing only `digest_sha256` with another syntactically valid 64-hex value was not rejected because `audit.py` validates digest shape, not a regenerated event-stream digest. Therefore the original frozen-auditor corruption matrix is **5/6**, not 6/6.

No primary row/result was rerun or changed. A read-only artifact-integrity outer layer was added afterward: exact SHA-256 of `RESULT.json` is pinned in `RESULT_MANIFEST.json`. Under the combined frozen semantic audit + exact result-file identity layer, all six copied-result mutations are rejected **6/6**. This proves copied artifact integrity, not an independent reconstruction of the descriptive event-stream digest semantics.

The descriptive digest is not a promotion gate; the decision-critical counts and source identities remain independently audited and unchanged. The scoped PASS therefore retains this audit-coverage limitation explicitly rather than relabelling the original corruption control.

## Boundary / stop

This closes only the #998 offline source/mechanics rung. It does not establish real X11 physical truth, real sampling overhead, application consumption, useful effect, MAP01 benefit or production ABI.

The next distinct step requires a fresh #60-authorized private-X11 matched live allocation using the exact retained v12 source, with independent terminal keymap/release and application-effect scoring. Do not reuse this allocation or infer live evidence from the mock PASS.
