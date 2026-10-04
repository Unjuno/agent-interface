# Cancellation token handoff: finite #17 model

PASS_SCOPED_FINITE_HANDOFF_MODEL. All23 linear extensions in the declared atomic domain were enumerated once and independently checked from saved traces. The two shared-flag policies have counterexamples; a fresh sticky token has none in this finite model.

| Policy | Stale-target orders / false cancellation | Current-target orders / lost cancellation |
|---|---|---|
| publish new operation, then clear shared flag |6 /1|3 /2|
| clear shared flag, then publish new operation |6 /3|1 /0|
| fresh sticky per-operation token |6 /0|1 /0|

A current cancellation can be lost at P,C,W,I,R. An old targeted cancellation can affect the new operation at I,P,C,W,R with either shared-flag policy where legal. The fresh-token comparison preserves target identity; cancellation sets only its own permanently scoped token. Prior generation token objects are never reused in this model.

First native model child98737 and saved-only auditor child98739 at13:40:36UTC both exit0/empty stderr. Complete source, prospective PLAN/FREEZE, all23 transition traces, actual commands/PIDs/UTC/monotonic/stream hashes are retained. Audit rejects six copied corruptions: missing/duplicate order, observed/reference bit changed, intermediate state changed, target identity changed. Model raw20582B/SHA49457b61cf7acae4bf9d870ab0ea59f423858ba97b99d304f531acea46003499; audit683B/SHA503ff1707c4708332288a2ea8581f87630a80ebfd6d3f3b3a9013d2339a6be3f.

This is a new ordinary finite specification proof. It does not rerun the consumed7049 one-shot18 Linux cells or6996 hot-drain. Existing kernel cancellation-release epoch tests concern evidence timestamps rather than transport-generation association. No actual production caller defect is demonstrated. The fresh-token model assumes sequentially consistent atomic events, distinct persistent token identities and correct target binding. It proves no real memory ordering, thread/OS scheduling, fairness, wake reliability, admission authority, ABA across reused identifiers, physical release, task effect, performance or broad computer-control capability. There were no container/backend/GUI/model/input/native allocations and no runtime source changes.

Decision: retain the two counterexamples and require explicit per-operation cancellation-state custody before reusing one-shot transport evidence for operation handoff. This is a design requirement supported by a bounded abstract comparison, not runtime adoption. Prior evidence remains immutable. Content votes and current-base integration gates are separate; main requests0, goalACTIVE.
