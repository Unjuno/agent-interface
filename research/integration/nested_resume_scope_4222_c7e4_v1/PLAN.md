# #4307: per-frame currentness during nested resume

Allocation: nrs4307-c7e4-formal01. Base main: e086a1cd6efaf7c1de77872c85da0689cee6d042.
Branch: research/nested-resume-frame-scope-4222-20260924-c7e4.
Owned path: research/integration/nested_resume_scope_4222_c7e4_v1/.

## Lineage and chronology

#4222/PR4278 is the completed one-level predecessor. #4302 handles completion
lineage and #4306 handles delivery reordering; neither is rerun or modified.
The old c7e4 pilot remains STOP_OUTER_EXECUTION_TIMEOUT_PARTIAL:48 planned,39 raw,
38 worker exit receipts,9 unexecuted/unobserved. It was locally, not publicly,
frozen. Original264 files and SHA256SUMS remain immutable. No pilot rows are pooled.
This is a first public formal allocation of known pilot conditions, NOT held-out
generalization. Local construction IDs and formal IDs have distinct namespaces.

## H

Successful validation for child C cannot establish currentness of parent P.
A session-wide positive cache may admit a suffix against P's changed target,
queue or UNKNOWN result. PER_FRAME_RECHECK should refuse each invalid frame while
preserving stable nested progress. Policy is eligibility only, not authority.

## T

Actual private authenticated Xvfb640x480x24, TCP disabled; separate Tk process;
XTEST a/b press/release pairs. No global X grab, host desktop/user data, model,
provider, package installation or experiment network. Supplied Linux execution
container, not image-attested Docker/OrbStack replication. Actual identity in
ENVIRONMENT.json; no clock/CPU affinity pin, no latency benchmark claim.

At depth2/3, XTEST types a into each saved level before its child modal opens.
The terminal child is resolved except INNER_UNRESOLVED. Unwind deepest first;
only an eligible frame receives b. A wrong child effect or refusal stops unwind.
The actor records key/value/modal changes independently of policy. Policies see
only the saved/current requested-frame receipt, not scenario or scoring journals.

GLOBAL_SUCCESS_CACHE does one complete check, then reuses a positive result for
other same-session active/resolved frames. PER_FRAME_RECHECK repeats the complete
check on each frame. The baseline is deliberately weak, not deployed runtime code.

Frozen scenarios: STABLE; ROOT_TARGET_REPLACED; ROOT_QUEUE_CHANGED;
ROOT_PENDING_UNKNOWN; MID_TARGET_REPLACED; INNER_UNRESOLVED.
Two depths x six scenarios x two policies x two repetitions =48 cases.
ALLOCATION.json fixes order and eight6-case batches. Execute each batch once,
in order. Per-worker12s, per-batch30s supervisor budget plus bounded termination;
outer tool envelope45s. These are safety bounds, not measured response SLOs.
An incomplete/stopped batch blocks all later batches. No formal rerun, replacement,
exclusion, pilot continuation, pooling or post-result gate/source tuning.

Construction:10 unit methods,3 fresh live cases,542 raw checks and14 effective
mutations passed. It is excluded. Deltas from pilot: phase labels/namespaces;
eight6-case instead of four12-case wrapper; strict source/raw manifest key sets;
complete-allocation verifier catches missing batch evidence rather than crashing.
App/policy and effect/eligibility semantics are byte-identical to the pilot.
Freeze all source/gates/schedule/environment publicly and verify remote Git blob
identity before any formal case. AUTHORIZATION.json binds that public commit.

## D

PASS_NESTED_FRAME_RECHECK_SCOPED iff all48 source/raw/process rows reconcile,
all8 batch ENDs and48 observed worker exits exist, and:
- candidate unsafe suffixes0, actual wrong-target suffix effects0;
- each policy STABLE root-contract completion4/4;
- weak unsafe suffixes14 and actual wrong-target suffix effects6;
- depth2 MID_TARGET_REPLACED is refused by BOTH on the first check;
- all8 INNER_UNRESOLVED cases emit no suffix;
- app exits0; Xvfb observed exit0 or -15; owned processes dead and sockets gone;
- all observed logical key/button state neutral, paired app press/release;
- independent raw-only audit errors=[]; full allocation audit passes;
-14/14 fixed effective copied-evidence corruptions reject after raw rehashing.
Complete contradictory candidate behavior is FAIL. Missing source/raw/process,
coverage or integrity is HOLD/STOP. Safe refusal is incomplete work, not success.
A valid-looking root ab does not bypass changed queue or UNKNOWN result.

## C

Cooperative authored dependencies and directed mutations. A global invalidation
policy or correctly frame-keyed cache could be equivalent. The basic implication
counterexample is analytic; actual Tk modality, focus restoration, event delivery
and effects are empirical. Correct validation assumes no relevant mutation between
check and suffix. Local grab restoration is explicit, not a native nested stack.

## U

No arbitrary-depth completeness, hidden dependencies, genuine lost-ACK inference,
check/use atomicity, arbitrary toolkit, natural failure-rate estimate, physical
HID measurement, model/token/latency benefit, runtime or product promotion.
Timing is diagnostic; combined calibrated uncertainty and coverage factor are
unavailable, not invented. Same-author separate auditor is not external review.

## Bounded roadmap / integration decision

Immutable pilot re-audit -> excluded construction -> public freeze/readback ->
eight immutable formal batches -> raw/full audit and14 effective controls ->
lossless evidence PR -> exact-head checks/review -> qualified main readback ->
owned-branch dependency check. Local setup/publication incidents stay in #4307.
#2789 recovery decision: never let a completed child's validation revive a
parent's continuation eligibility without that parent's current evidence.
Repository ROADMAP, model use and product gates remain separate.

## Variables and units

| Symbol/field | Meaning (Japanese) | SI unit | Definition | Domain/assumption | Type |
|---|---|---|---|---|---|
| F,C,P | 保存フレーム・子・親 | 1 | immutable bound context | distinct frame IDs | record |
| S(t) | 復帰確認時の状態 | mixed record | current receipt | complete/correct declared fields | record |
| G | 復帰適格性 | 1 | all declared guards satisfied | Boolean, not input authority | Boolean |
| t,t' | 確認時刻 | s | same-host monotonic clock | nonnegative; stored ns | scalar |
| E_F | フレームへの後続入力 | 1 | one XTEST b edge pair | only after eligibility | event |
| d | 入れ子深度 | 1 | saved levels before terminal child |2 or3 | integer |
| N | 新規正式ケース数 | 1 |2 depths x6 scenarios x2 policies x2 reps |48 exactly | integer |

Dimensional check: currentness comparisons compare like identities; case and
input counts are dimensionless. Elapsed-time subtraction uses only the same
monotonic clock; ns converts to s by division by one billion. No clock value
is compared to a frame/generation identity.
