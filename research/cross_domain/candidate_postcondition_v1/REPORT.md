# A write-scope check does not establish the intended after-state

## Decision and scope

RETAIN the request-bound candidate postcondition gate for this native-Git, authored one-file-edit fixture. HOLD production promotion, general GUI claims, automatic goal discovery, and security-boundary claims.

Task: CANDIDATE-POSTCONDITION-20260916-001. Read-only publication base: `0dd239b7db10831a4e8ac078d3a32d4be6370e3d`. New intended path: `research/cross_domain/git_postcondition_gate_v1/**`. No shared runtime, historical result, active allocation or user repository was modified. PR334 remains a separate draft research result; this work does not merge it.

GitHub MCP reading succeeded. The create_issue action returned `Resource not found` twice, including after rediscovery; create_branch returned the same error. These are action-resolution failures, not evidence of a denied repository permission or a safety-policy block. No new remote issue, branch, PR or commit is claimed. The experiment was source/plan-frozen in local Git before scored execution, at `b178331f1e3348a6aea538441b6030ed5a256695`. Plan SHA256: `8d6777275018361c9004eeea29902e2cf1b4d0d89a2bd29246b3ef3ac588587b`. This is local preregistration, not GitHub preregistration or a globally exclusive lease.

## Stage 1: inspect the actual caller boundary

The preceding work fixed stale whole-snapshot replacement by constructing a one-file patch from the current tree, checking read/write preconditions, and using final current-OID CAS. Its `experiment.py` checks the exact changed-path list before publication. Its fixed builder also writes the requested blob directly and produced correct results. This follow-up does NOT allege that the previous exact builder, current product, or Git has a new defect.

The narrower question is whether the publication gate would detect an error in a replaceable candidate constructor. A list containing only the permitted path tells us where a change is made, not whether its bytes or entry attributes are what the caller requested. These are authored construction-error controls, not naturally sampled agent failures.

## Stage 2: one-factor comparison

The trusted fixture request says: update `output/effect.txt` to the declared exact bytes as a normal non-executable file; preserve all other current entries and current ancestry; do not overwrite a conflicting read/write state or a ref changed after validation.

Both policies perform the SAME read/write preconditions, exact changed-path check, single-current-parent check and native `git update-ref` with the inspected old OID. The sole policy difference is whether equality to the requested after-entry gates publication. Both policies compute the extra equality for diagnostics, so this experiment is not an overhead or equal-computation savings benchmark.

- `scope_only`: publish when those common checks pass.
- `scope_and_postcondition`: additionally require the candidate's target entry (mode, object kind and blob identity) to match the independently supplied request.

The publisher receives an immutable proposed commit OID, not an executable producer callback or mutable branch name. It publishes that same checked OID. Staging creates Git objects even on refusal; refusal means no target-ref publication, not that no disk bytes were ever written.

The comparison is a research control derived from PR334's publication checks, not an unmodified production-baseline evaluation. Parent validation is common to both new arms. The semantic requirement is authored exact equality, not general understanding of task success.

## Frozen matrix and measured first outcomes

Twelve scenarios, two policies, three repetitions: 72 fresh disposable bare Git repositories. Order was fixed with seed334916. Every paired arm uses byte-identical initial/current/candidate Git objects and the same semantic request; pair identity was independently checked for all36 pairs. Same-ID scored reruns: zero.

| Scenario | Scope only | Scope + requested after-state |
|---|---|---|
| Correct candidate | Publish3/3 | Publish3/3 |
| Correct candidate after unrelated edit | Publish3/3, unrelated edit preserved | Publish3/3, unrelated edit preserved |
| Wrong bytes at permitted path | Incorrect publish3/3 | Refuse3/3 |
| Unrequested executable mode | Incorrect publish3/3 | Refuse3/3 |
| Symlink instead of regular file | Incorrect publish3/3 | Refuse3/3 |
| Delete target instead of update | Incorrect publish3/3 | Refuse3/3 |
| Extra unrelated edit | Refuse3/3 | Refuse3/3 |
| No-op candidate | Refuse3/3 | Refuse3/3 |
| Candidate drops current ancestry | Refuse3/3 | Refuse3/3 |
| Semantic read conflict | Refuse3/3 | Refuse3/3 |
| Concurrent edit of write target | Refuse3/3 | Refuse3/3 |
| Ref change after validation | Native CAS refusal3/3 | Native CAS refusal3/3 |

| Aggregate | Scope only | Scope + requested after-state |
|---|---:|---:|
| Cases |36|36|
| Task-correct decisions |24|36|
| Publications |18|6|
| Incorrect publications |12|0|
| Refusals |18|30|

The candidate's36/36 comprises SIX executed correct edits and THIRTY appropriate refusals, not36 completed edits. Across both arms, task-correct decisions are60/72; all72 have valid evidence records. Exactly12 publications produce the requested successful edit; the other12 published candidates are deliberate negative outcomes.

The `wrong_kind` fixture stores a Git blob under symlink mode120000 rather than regular mode100644. A symlink's Git object is still a blob; its filesystem entry type is encoded by the mode. No candidate symlink was checked out, followed or executed. The wrong-mode and wrong-kind controls keep the requested bytes unchanged, isolating entry attributes from content.

## Conditional reasoning, not a blanket guarantee

A current-state read/write check establishes the declared preconditions. An exact changed-path comparison establishes that all tracked leaf entries outside the permitted path are unchanged. Requiring the requested after-entry establishes this fixture's exact target effect. Requiring the inspected commit as the sole parent retains the current ancestry. Finally, old-OID CAS couples publication to that inspected ref identity; the after-validation-change control confirms refusal when the ref moves.

Each condition answers a different question. A correct CAS cannot infer the requested content, and content equality cannot protect against a ref that changed after it was inspected. This is a known design-by-contract/state-preservation pattern, not a novelty claim.

The conditions depend on a correct caller request and complete authoritative preconditions. A wrong request could still be faithfully satisfied. Uncooperative publishers, direct Git writes outside the gate, ABA/history-sensitive validity, external effects, empty-directory-only Git tree distinctions, signed-history requirements, and arbitrary state outside the inspected Git snapshot are not covered.

## Verification

Construction completed24 policy/scenario cases, excluded from the measured72. Seventeen unit/contract test methods passed before freeze, including corrupted request/receipt/ref/object/reflog, wrong return code, Boolean/reversed clock, incomplete/duplicate plan, immutable identity requirements and same-ID refusal. There were no construction or measured harness failures.

The independent auditor imports neither the experiment nor Git/Pillow/other third-party packages. It decodes retained loose objects with Python standard-library zlib, verifies SHA1/header lengths, recursively reads tree entries and full blob bytes, checks direct refs and reflog transitions, and validates all process transcripts. It does not call Git to judge the experiment, reducing a common measurement dependency relative to the prior audit.

The frozen unchanged audit passed72/72 integrity cases, independently confirming36 byte-identical pairs,3,162 command acquisition brackets and954 per-repository object checks. Object checks are counted per repository, not as954 independent observations. Git initialization itself uses a checked subprocess but is not included in the3,162 logged Git commands.

No time-performance result is claimed. Command start/end values use the same-host monotonic nanosecond clock; type and ordering are checked. SI base unit is seconds, stored unit nanoseconds. Clock resolution is not accuracy, and no calibrated combined uncertainty or coverage factor is supplied.

See VALIDATION.json for independently extracted replay, source/manifest equality, test rerun and patch-application results. The replay reads existing measured objects; test reruns create separately labelled construction fixtures and do not repeat measured IDs.

## Environment

AMD EPYC9V74 80-Core Processor, CPU affinity0-4, frequency not pinned/shared host, batch1 sequential local repositories. Git2.47.3, CPython3.13.5. Complete kernel, libc, filesystem, executable hash and clock metadata are retained in `source/ENVIRONMENT.json`. SHA1 bare repositories use empty templates, isolated Git configuration and loose refs/objects; no production hook or external effect service is involved.

No Doom/GUI/model call, network experiment, user-data edit, rate/speedup or human-tempo claim. Native Git is the tested application; this is not an end-to-end Agent Interface client run.

## H / T / D / C / U

H: scope-constrained construction errors can pass read/write/CAS guards; a request-bound after-entry condition should stop them.
T:24 excluded construction cases;17 prefreeze tests; a source/plan-frozen72-case paired native-Git allocation; independent byte-level audit.
D: scoped gate PASS:36/36 candidate task-correct, four expected wrong-effect families exposed by controls, no normal-case loss, all72 integrity checks pass. Remote publication remains separate and incomplete.
C: the previous correct constructor did not produce these errors; this work intentionally varies its output. Any advantage follows from the stronger declared contract, not improved model intelligence.
U: one host, three deterministic repeats per cell, known exact outputs and cooperative publication. No natural error-rate estimate, general semantics, automatic intent discovery, cryptographic authorization or crash-durability guarantee.

## Transfer and next boundary

Programming-language contracts: distinguish the allowed modification set from the required after-state. Database and document editing: verify requested field values as well as not touching other fields. Incremental/optimistic execution: a staged candidate can be inspected before publication, but the same approach cannot pre-prove arbitrary non-stageable GUI effects.

Next useful boundary: transfer this already-decidable request/after-state contract to one real staged application output, or stop and report that the application lacks a publish-before-effect boundary. Repeating more synthetic wrong bytes alone would add little information. No next allocation is launched here.

## Retention

All measured native repositories, requests, command transcripts, first outcomes, unchanged sources/plan, construction records and independent audit are delivered in the evidence archive. The local apply-only Git patch adds the proposed research directory and never touches shared runtime/history. No font files, installed executables or private credentials are distributed.

Implementation primary references (version-pinned behavior is measured locally):
- https://git-scm.com/docs/git-update-ref
- https://git-scm.com/docs/git-diff-tree
- https://git-scm.com/docs/git-ls-tree
