# INPUT-OWNER-V12-OFFLINE-IMPLEMENTATION-20260918-002

BASE: 3c34e3cea2a39e961e097b41444ff4a7563a4170
Issue: #998
Reservation: research/input-owner-v12-offline-20260918-002
Execution: disposable container only; no X11/Xvfb/XTEST/GUI/model/provider/network/task input.

## H
Integrating the already-retained #1035/#1039 best-effort owner-thread pre/post physical sampling order with the #1048/#1054 stable physical-hold generation contract into the exact v10 ordinary key down/up path changes no non-measurement control semantics. Physical intervals are emitted only when the exact #994/#992 conditions are observed; stable actuation identity is minted only by a confirmed new physical DOWN edge, reused only for the same known active hold, and retired only by a confirmed matching physical UP or verified aggregate-neutral cleanup. Measurement uncertainty never grants authority or fabricates lineage.

## T
1. Pin current v10 blob 341b3c01649943ddaad5f28431a792c4889cc36e, v11 blob 842071284156d3ccc647f47135ee62a9e512cb56, press contract blob 9dcb1890b955019dd3880c1b09689213bbb84a58, release contract blob 15008b58e5389b2e1d3b530abf029982686e6bc0, dual-edge adapter blob a1344409ea6383c6394e991ac0b59fa7689978ef, identity model blob bdf68b88111ddb61297cdec29be394d7fd4dd060.
2. Build research-only input_owner_v12.py from the normalized semantic mirror of v10. Allowed code changes: add pure measurement/identity helpers; add owner-local identity bookkeeping; insert best-effort samples into ordinary key down/up at the retained #1035 positions; terminate identity after existing verified aggregate cleanup. Do not alter pointer, focus, lease, cancel, expiry or admission guards.
3. Fixed fake-backend tests execute actual v10 and v12 owner threads without X11, comparing non-measurement outcomes/inject+sync effects on clean down/up, repeated down, no-op/foreign up, sample failure, backend failure, missing lineage and cleanup.
4. Primary mechanics corpus: seed 99820260918002; 120,000 independent sequences, length 1..12, keys F8/F9, same/other leases, authored external physical-state perturbations, guard/sample/backend success/failure. Candidate and independently structured oracle must agree on measurement classification/identity; baseline and candidate must agree on all non-measurement outcome/state/backend effects. This is construction evidence, not live/formal authority.
5. Source-first freeze exact v12/tests/runner/oracle/auditor before primary; read back exact branch bytes; mandatory Issue/branch/PR ownership reread; one primary invocation, reruns/replacements/tuning0.
6. Post-primary independent audit, source rehash, copied-result corruption controls only.

## D
PASS_INPUT_OWNER_V12_OFFLINE_MECHANICS_SCOPED only if:
- actual-source fixed tests pass and v12 py_compile passes;
- primary candidate/oracle measurement+identity mismatches=0;
- baseline/candidate non-measurement control/state/backend mismatches=0;
- false physical intervals=0; identity false mint/reuse/cross-lineage retire=0;
- repeated same hold preserves ID and emits no second confirmed-DOWN interval;
- preexisting physical DOWN and already-UP/no-op release never fabricate fresh edge identity;
- confirmed matching down/up can compose under #996 exact lineage/order; incomplete/mismatch cannot;
- sample failure changes no baseline admission/release semantics and emits no confirmed interval;
- cleanup may retire active identity only after existing aggregate neutral verification and emits no per-key physical edge interval;
- authority/application-consumption claims remain false; source/result/audit integrity passes.

FAIL_AUTHORITY_REGRESSION for any control admission expansion/restriction caused by measurement; FAIL_FALSE_PHYSICAL_EDGE for unsupported interval; FAIL_ACTUATION_ID_LIFECYCLE for mint/reuse/retire violation; FAIL_RUNTIME_SEMANTIC_DRIFT for non-measurement divergence; FAIL_INTEGRITY for source/result mismatch.

## C
Best-effort keymap sampling can be unavailable; this should reduce measurement evidence without changing control. A confirmed physical edge still does not prove application consumption. Aggregate cleanup final-neutral verification can end a lineage without proving that cleanup created a fresh physical edge. The fake backend can miss real X11 scheduler/server behavior.

## U / Stop
Offline/mock/source mechanics only. No real X11 physical truth, real timing-width distribution, application effect, MAP01 usefulness, production ABI or live authority claim. Stop after one retained offline outcome. Any live transfer requires a fresh #60-authorized allocation.
