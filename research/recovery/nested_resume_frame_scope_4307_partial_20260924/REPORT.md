# Issue #4307 — nested resume validation is frame-scoped

## Decision

**PASS_NESTED_FRAME_RECHECK_SCOPED**, allocation `nrs4307-c7e4-formal01`.

One prospectively source-frozen allocation completed 48/48 fresh private Tk/Xvfb
sessions in eight immutable six-case batches. Batch, worker, application and Xvfb
exits were all observed: eight batch exits0,48 worker exits0,48 app exits0,
48 Xvfb exits0. Reruns/replacements/exclusions/post-result tuning:0/0/0/0.
The full allocation audit passed446 checks; its separate raw audit passed8286
checks; both errors arrays are empty. Fourteen effective evidence corruptions,
including rehashed raw mutations, were rejected14/14. Source rehash matched12/12.

This is a scoped cooperative-GUI contract result. It is not a runtime promotion,
a demonstration of model usefulness, or completion of the repository ROADMAP.

## H / T / D / C / U

**H:** a successful child-frame currentness check cannot be reused as evidence
that another suspended frame remains eligible. The weak GLOBAL_SUCCESS_CACHE
may type a suffix despite a changed parent target/queue or UNKNOWN result.
PER_FRAME_RECHECK validates the requested frame each time.

**T:** two saved-stack depths(2/3), six directed scenarios, two policies and two
fresh repetitions. Real Tk Toplevel/Entry lifetimes and XTEST a/b input, private
Xvfb640x480x24 with per-case authentication and TCP disabled. Controller receives
only requested-frame saved/current receipts; the app journal is scoring evidence.
App/policy semantics are byte-identical to the earlier pilot. Phase namespaces,
batching and evidence-key/complete-allocation checks were changed before freeze.
Known pilot conditions are replication coverage, NOT held-out generalization.

**D:** every preregistered gate in PLAN.md passed without changing the source,
oracle, denominator or thresholds. Refusal is incomplete work, not task success.

**C:** the comparator is deliberately incomplete, not alleged deployed behavior.
Current dependency receipts and state changes are authored/cooperative. Global
invalidation or a correctly frame-keyed cache could implement equivalent safety.
This does not prove per-frame full recomputation is the cheapest implementation.

**U:** no hidden-dependency discovery, arbitrary-depth coverage, real lost-ACK
inference, check/use atomicity, arbitrary toolkit/platform, natural incident-rate
estimate, physical HID proof, learned model, token/latency benefit or product claim.
Independent means separate raw-only implementation by the same author, not external
human review. Timing is diagnostic only; calibrated combined uncertainty and a
coverage factor are unavailable rather than manufactured.

## Results

| Endpoint | GLOBAL_SUCCESS_CACHE | PER_FRAME_RECHECK |
|---|---:|---:|
| Complete fresh sessions |24|24|
| Emitted suffixes |44|30|
| Suffixes violating the current requested-frame contract |14|0|
| Actual wrong-target suffix effects |6|0|
| Cross-frame positive-validation reuse |26|0|
| Stable root-contract completion |4/4|4/4|

The14 weak unsafe suffixes comprise ROOT_TARGET_REPLACED4,
ROOT_QUEUE_CHANGED4, ROOT_PENDING_UNKNOWN4 and depth3 MID_TARGET_REPLACED2.
Six of these are actual wrong-target Entry effects; the eight queue/result cases
can still display `ab` but violate the continuation contract. Do not count those
as successful recovery. In depth2 MID_TARGET_REPLACED, both policies refuse on
their first complete check. All eight INNER_UNRESOLVED cases emit zero suffix.
Candidate stable completion is nonzero; the candidate is not an always-stop rule.

Concrete trace: in a root-target replacement case, the deepest child's valid
suffix completes normally. The weak policy then reuses that child's positive
validation and writes `b` into the root's replacement Entry, which is missing the
old prefix. The candidate reads the root's own current receipt and returns
REVALIDATE_TARGET before any root suffix. See raw CASE/APP/IPC records.

## Analytical statement and variables

| Symbol | Meaning (Japanese) | SI unit | Definition | Domain/assumption | Type |
|---|---|---|---|---|---|
| F,C,P | 保存フレーム・子・親 |1| immutable bound contexts | C and P distinct | record |
| S | 現在状態 | mixed fields | current receipt | correct complete declared fields | record |
| G | 復帰適格性 |1| all required binding/currentness checks pass | Boolean, no authority | predicate |
| E | 後続入力 |1| one permitted b press/release pair | requested frame only | event |

Choose a state S in which C's dependencies are unchanged and P's target instance
has changed. By the declared contract G(C,S) is true, while G(P,S) is false.
Therefore G(C,S) does not imply G(P,S), even with no elapsed time. A global positive
Boolean loses the binding information required to justify parent eligibility.

If every E for F is preceded by G(F,S), the receipt is complete/correct and no
relevant change occurs between that check and E, then E meets this declared
eligibility contract: each conjunct required by the contract has been checked for
that exact F. Removing any of those assumptions invalidates the implication.
This is a conditional admission argument, not OS-global atomicity. The experiment
measured the residual real Tk focus/modal/input/effect composition.

Unit check: frame IDs, Boolean guards and event counts are dimensionless. Time
measurements are retained as same-host monotonic nanoseconds; no timestamp is used
as a frame identity or treated as calibrated physical latency evidence.

## Backend / environment

Provided Linux x86_64 execution container, CPython3.13.5, Tk8.6,
Python-Xlib0.15, Xvfb640x480x24. CPU reports Intel Xeon Platinum8573C and five
logical CPUs; neither frequency nor affinity is pinned. No model/GPU invocation.
Docker/OrbStack CLI/image attestation unavailable locally; this is not claimed
as image-attested replication. No host/user desktop, network experiment or
production runtime mutation. X-server logical key/button neutrality and app
press/release journals agree; no physical HID telemetry claim.

Tk local grabs are explicitly restored during pop; this fixture does not assume
that Tk itself provides a nested grab stack. See the frozen ANALYSIS.md for the
primary Tk/Xlib reference distinction. Native input acceptance is not itself an
application effect or successful root continuation.

## Chronology and old STOP preservation

Intake main: e086a1cd6efaf7c1de77872c85da0689cee6d042.
Successor Issue #4307 and the owned branch were created before this allocation.
Preformal source archive SHA256:
`9d39d91744de2b74a8ac01a5612624401be882bdaa163228d9664e0bb3534c25`.
FREEZE SHA256:
`6d65325295457f52b4e794240559d27fa6bddb5e80c7359713de38489f4ecf75`.
Public source/plan head:
`3d414c82424d820069967b4490a85c5eebbf4378`.
All three source-capsule Git blobs and readable PLAN matched local identities
before AUTHORIZATION.json was written and before the first formal worker.

Excluded construction:10 unit tests,3 fresh live cases,542 raw checks and14/14
controls. They are not counted in the48 formal sessions.

Old pilot is unchanged:48 planned,39 raw cases,38 worker exits,9 cases without
execution evidence. Its first disposition remains STOP_OUTER_EXECUTION_TIMEOUT_PARTIAL /
HOLD_INCOMPLETE_48_CASE_ALLOCATION. Its missing fourth-batch END and missing worker
exit were NOT inferred, repaired or replaced. Read-only audit reproduces39 cases /
6500 raw checks / errors0 but does not promote the pilot. Original ZIP301380 bytes,
SHA256 `9746fe87affaaa662c4fe46a9f809ddda8d6bd79e5f460e7613427fda8d7de14`.
All264 original expanded files and their manifest remain byte-identical.
The new formal result has its own48 IDs and contributes no replacement pilot rows.

## Integration decision and remaining gates

Before composing nested recovery into #2789's desktop path, bind each successful
validation to the frame whose continuation it justifies. A completed child's
receipt is neither restored parent eligibility nor new input authority. Preserve
pending-result reconciliation, current target and queue checks on each unwind.

#4302 completion lineage and #4306 delivery reordering are separate contracts;
this result neither reruns nor establishes their composition. The project main
README/CURRENT_GOAL/ROADMAP were inspected; broad model-in-loop efficiency and
product gates remain separate. Evidence transport/PR/CI are delivery gates, not
additional scientific trials. No foreign branch or shared runtime file is changed.

Related transfer ideas: programming-language effect/capability scopes can bind
continuation checks; transaction systems can validate each suspended read set;
human-computer interaction recovery can distinguish dialog closure from task
readiness. These are implications of the contract, not measured cross-domain gains.
