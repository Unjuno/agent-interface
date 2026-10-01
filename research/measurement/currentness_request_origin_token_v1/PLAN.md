# CURRENTNESS-REQUEST-ORIGIN-TOKEN-20260918-005

BASE: 4d3d6152958079f9d38511950b9ff8342c3282c1
PREDECESSOR: #1118 FAIL_INFLIGHT_STALE_RESPONSE_LAUNDERED
PARENT CANDIDATE BLOB: bebbc8cade7a4e338e68467355d1be9cb636008e

## H
Add exactly one repair factor to the runtime-owned currentness-epoch barrier: BEGIN_REQUEST stores the runtime current epoch in an opaque request record. INSTALL_RESPONSE can install only if the stored origin epoch still equals the runtime current epoch for that request scope. Planner generation is provenance only and cannot affect currentness.

## T
Standard-library disposable container. Four scopes. 600,000 deterministic mixed valid transitions over BEGIN_REQUEST / INVALIDATE / INSTALL_RESPONSE / TRY_USE with delayed responses, duplicate invalidations, unknown responses, consumed-response replay, cross-scope uses, and planner generations in {0,1,2,100,1000000,2147483647}. Candidate and independently structured history oracle are compared after every transition. Separately run bounded exhaustive symbolic traces of length <=5 and frozen directed controls including the exact #1118 stale in-flight pattern. Malformed controls are outside the positive corpus. One primary invocation after source-first publication/readback and ownership reread; reruns/replacements/tuning0.

## D
PASS_CURRENTNESS_REQUEST_ORIGIN_TOKEN_SCOPED iff candidate/oracle mismatch0; old-origin response installs0; old-origin response admissions0; valid fresh current-epoch installs and uses occur; planner-generation influence0; response replay creates/rebinds0; duplicate invalidation double-advance0; cross-scope mutation0; authority promotions0; malformed controls fail closed; source/result/audit integrity passes.
FAIL_STALE_RESPONSE_ESCAPE for any old-origin install/admission. FAIL_REQUEST_ORIGIN_FORGERY if planner-controlled input changes origin. FAIL_RESPONSE_REPLAY if a consumed request installs/rebinds a decision.

## C
Request-start epoch is conservative. A pending planner that legitimately receives fresh evidence needs a new runtime-owned request/origin token rather than implicit laundering. Real cancellation, transport concurrency and process loss remain outside this pure contract.

## U
Synthetic lifecycle only; no model/provider/GUI/X11/network/task input/user data/shared runtime. This is scoped semantics, not latency/token/human-tempo or production ABI evidence.

## Stop
Retain first primary outcome and audit. No post-result semantic tuning. A later fresh formal allocation remains required before runtime promotion.
