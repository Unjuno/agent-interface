# Issue #5265: semantic coalescing finite construction record

Allocation: `DOT-5265-CONSTRUCTION-20260930-01`
Publication namespace: `research/coordination/effect_coalescing_5265_dot_v1/`.
Source intake: `eddcf7a47c1f3c47165288037e66f66da0c3138a`.
This is an immutable retrospective record of construction plus a prospective
formal specification. The construction matrix was run once before source freeze;
it is NOT preregistered formal evidence. Formal invocations remain zero.

## H — hypothesis and explicit assumptions
Under an atomic admission/effect/release finite-state model, coalescing on an exact
semantic tuple removes duplicate independently authored proposals without losing
any required effect after a changed intent, target/incarnation, parameters,
operation, opportunity, session, or verified observation generation.
The primary competing hypothesis is that an existing content-bound common semantic
work-ID ledger plus fresh ordinary admission already provides the same result.

Assume authored exact semantic fields and current generation/incarnation/revision
facts are available. Every proposal separately passes ordinary admission before
reuse. No reused decision confers authority. The effect is one abstract
non-idempotent increment associated with an independently authored fixture goal.
Atomic serialized proposal processing represents an admission linearization;
arrival permutations are enumerated, not real concurrent execution. No thread,
process, native input, app, durable receiver or production runtime is tested.

## T — frozen finite case contract
`CASE_MANIFEST.json` contains all concrete proposals, transitions, schedules and
independently authored oracle goal/denial labels: 49 traces in 35 families,
47 shared-ID primary and 2 missing-common-ID sensitivity traces, four policy arms,
196 arm rows. `build_manifest.py` authors the finite fixture without policy imports.
No random draws or redundant sample inflation. Longest trace is four events.

Fields: session, producer/retry/attempt identity, common work ID, intent revision,
observation generation, target incarnation, operation, effect opportunity,
canonical exact parameters, deadline, authorization and identity certainty.
Deadline equality is valid; `now > deadline` is expired, matching the pinned core
contract's boundary. Parameters changed under a NEW work ID are distinct work;
changed content under the same producer retry intent is a conflict, never replay.
A verified satisfied postcondition is SUPERSEDED; stale generation/incarnation,
unauthorized/revoked and expired proposals reject before looking up any reuse.
Missing/ambiguous semantic identity yields conservatively. Explicit release and
terminal cleanup are independent of deduplication state. No identity TTL revival
is modeled: records last for this <=11-tick finite trace; proposal deadline expiry
never refreshes itself. Tables cap at16 entries each; traces cannot hit capacity.

Arms:
1. NO_CROSS_PRODUCER: content-bound producer-local retry ledger only.
2. COMMON_WORK_ID: same local retry rule plus content-bound externally authored
   common semantic work-ID ledger, scoped by session, after ordinary admission.
3. ONE_PER_GENERATION: local retry plus one effect per session/generation;
   conservative serializer comparator, deliberately exposed to legitimate distinct
   work in a single generation.
4. SEMANTIC: local retry plus exact tuple (session, revision, generation, target,
   incarnation, operation, opportunity, canonical parameters). Producer identity
   is deliberately absent from the cross-producer equivalence key.

All arms receive identical schedules and current admission facts. Oracle fields
are stripped before policy invocation. The oracle counts independent fixture goal
labels; it neither imports model.py nor constructs semantic equivalence keys.
The auditor reads retained raw decisions against the fixture without running arms.
Expected negative controls include no-cross duplicate effects and one-per-generation
lost valid work. Missing-common-ID sensitivity is reported separately: it tests
availability of identity, not superiority of a second execution/dedup ledger.

## D — decision gates
For the primary matrix, require SEMANTIC duplicate count0, missing valid effects0,
unauthorized effects0, cross-goal merge0, oracle/denial errors0, neutral resources,
no authority creation, bounded memory and independent audit agreement.
If COMMON_WORK_ID satisfies the same primary gates, model interpretation is
`HOLD_EXISTING_IDEMPOTENCY_ALREADY_SUFFICIENT`. This does not establish that common
semantic IDs can always be assigned in a real application. The two sensitivity
traces must be shown even if they constrain the redundancy interpretation.
Any semantic missing effect => FAIL_FALSE_COALESCE_VALID_REPEAT; any semantic
duplicate => FAIL_DUPLICATE_EFFECT_REMAINS; cross-goal merge =>
FAIL_CROSS_INTENT_OR_TARGET_MERGE; integrity/provenance issues => typed STOP.

Issue #3352 requires a real container command/image and real target boundary for
formal execution/merge promotion. Docker/Podman are unavailable in the supplied
cloud execution environment. Therefore the current overall disposition is
`STOP_CONTAINER_RUNTIME_UNAVAILABLE_NO_PROMOTION`; zero formal allocation spent.
A parent-approved, published freeze and a suitable pinned container allocation
are prerequisites to any future formal invocation. No formal invocation is
currently authorized; do not use runner.py's formal mode in this allocation.

## C — competing explanations
The common semantic work ID performs the same distinction as the tuple; deriving
it from the tuple makes the ledger algebraically equivalent rather than a new
mechanism. A one-per-generation rule alone loses distinct work at one generation.
Atomicity and exact field availability are assumed. The model does not expose an
in-flight effect or delayed feedback interval; unknown outcomes are outside this
rung and must retain #24's uncertainty rules rather than automatically replay.
The hand-authored oracle can encode a wrong domain contract, despite implementation
independence; source and fixture review is necessary.

## U — uncertainty and non-claims
This is finite analytical construction, not a statistical benchmark, hidden/fresh
formal corpus, real concurrency test, Docker result, real GUI/product evidence,
exactly-once guarantee, storage durability proof, latency/token benefit, or general
semantic identity discovery. No new runtime abstraction is recommended on this
record. #5265 stays open at the environment/formal gate; missing shared identity
remains a residual applicability question.

## Resources, commands and retention
Python standard library only; one CPU process pinned to one allowed CPU, no child
processes/threads, RLIMIT_AS512MiB, RLIMIT_CPU60s, wall alarm60s. Measured construction
max RSS and elapsed time are retained in RESULT.json. No packages were installed.
`python test_construction.py` red then green results remain separate.
`python runner.py --phase construction --output construction/matrix-c1` ran once.
Retain RAW.jsonl, RESULT.json, STARTED.json and stdout/stderr unchanged. All later
audit/corruption commands are read-only with respect to first outcomes and never
invoke the policy model. Corruption controls alter temporary copies only, including
recomputing transport hashes so checks are not checksum-only.

The source and raw manifest freeze occurs after construction, before independent
audit/publication. Audit policy was corrected before freeze to expect construction
formal0 rather than formal1; no raw outcomes or simulation source changed.
