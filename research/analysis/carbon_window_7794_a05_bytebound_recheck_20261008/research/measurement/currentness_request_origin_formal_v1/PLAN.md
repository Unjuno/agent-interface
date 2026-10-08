# CURRENTNESS-REQUEST-ORIGIN-FORMAL-20260918-006

BASE: 20e83ba6a9afa36ecbf003098fcab2db63e0c3b8
PARENT: #1126 / PR #1231
EXACT CANDIDATE GIT BLOB: 3e9fc5474de9af820b653c36e5db5d912edfc076

H: hold the exact #1126 candidate byte-for-byte. A fresh corpus must preserve fresh current-epoch request installation/use while refusing every stale-origin response. Planner generation remains provenance only.

T: standard-library disposable container; fresh seed 112620260918106; 600,000 total transitions across four scopes. First 5,000 explicit stale-inflight stress traces (20,000 transitions), then fresh random traces for the remaining 580,000 transitions. Operations BEGIN_REQUEST / INVALIDATE / INSTALL_RESPONSE / TRY_USE. Independent history oracle compared after every transition. Exact #1118 and fresh-after-invalidation controls, malformed fail-closed controls, source-first publication/readback, primary1/reruns0.

D: PASS_CURRENTNESS_REQUEST_ORIGIN_FORMAL_SCOPED iff candidate/oracle mismatch0; stale-origin installs/admissions0; every 5,000 explicit stale stress response is refused; fresh installs/admissions>0; replay rebinds0; planner-generation influence0; duplicate invalidation double-advance0; cross-scope mutation0; authority promotions0; malformed controls pass; integrity/audit pass.

C: serialized synthetic lifecycle cannot establish real IPC cancellation/process failure/model/task behavior.

U: no GUI/X11/model/provider/network/task input/shared runtime. Fresh formal semantics only; PASS means eligible for later shadow/concurrent transport integration, not runtime promotion.
