# Bounded claim merge after a GitHub stale-SHA conflict

Issue #352. BASE `4e802fa2ec3c0c97545a38520bb18b3b126d8e4e`.
Branch `research/github-claim-merge-4e802fa`.
Additive scope `research/coordination/github_claim_merge_v1/**` only.

**Disposition: RETAIN the allocation-004 scoped result; HOLD production coordination adoption.**
`PASS_BOUNDED_CLAIM_MERGE_SCOPED` concerns three prescribed sequential MCP schedules, not concurrent HTTP, a complete lease implementation, or agent task performance.

## Why this successor

PR #350 / Issue #349 retained one-path stale-writer rejection. It did not test how an unrelated loser could recover without deleting the winning claim. PR #348 / Issue #346 supplied exact task/scope and authored semantic-successor conflict rules. This experiment combines that check with one bounded re-read/append/current-SHA retry, rather than sharding or adding a lock service.

Public API contract: GitHub's official repository-contents documentation specifies the replaced file's blob SHA on updates and lists HTTP 409 for conflicts: https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents . The outcomes below are actual MCP operations, not conclusions inferred solely from the documentation.

## Allocation chronology and retained interruption

Allocation `COORD-GITHUB-CLAIM-MERGE-20260916-003` froze at `9a060d26d3ae8e3c02abe796f9c8c877592cf224`. Writer A committed in the independent case, B received a SHA-mismatch 409, and the recovery GET returned A. Local bookkeeping then raised PermissionError: the container-created directory was root-owned while a separate Python kernel attempted to create a file. No recovery proposal/PUT ran. The entire allocation stopped, with zero complete cases and two unstarted cases. The original register, commit, freeze and `INTERRUPTION.json` remain. It is not PASS and is not pooled.

Successor allocation `COORD-GITHUB-CLAIM-MERGE-20260916-004` uses fresh `allocations/a2/**` paths. Only supervision changed: all bookkeeping runs in the container executor, with a successful write/read preflight. Policy, auditor, tests and payloads are byte-identical. Plan changes task/path provenance only, not conditions, outcomes or budgets. Core freeze is `6fa89190a1f80065a13a1f000aae3c7dd4f8d53a`; tested bookkeeping source is frozen at `367bfdd7e52da2c379aa5554f0d0af1751e6f32f`, before measured updates. Freeze notices and the interruption are recorded in #352 before successor execution.

## Actual execution

All remote writes were GitHub MCP `update_file` calls on dedicated fixture paths. A/B/C are labelled synthetic writers operated sequentially by this session through one authenticated connector; they are not independent principals or simultaneous sessions. The same initial GET is intentionally supplied to the labelled writers. The frozen Python proposer actually executes on each recovery GET in the container. Its exact payload is then submitted by this session through MCP. This is not a deployed autonomous API client.

All fixture records set `fixture_only=true`; no actual worker is granted a research lease or input authority. Exact task-ID equality, exact scope equality, or same direct successor AND same authored question key means conflict. On a valid independent proposal, append to the CURRENT complete register, preserve every existing claim and consumed identity, and increment the revision. A proposal is not registration. Only a successful update and matching readback count as fixture registration. After the sole recovery PUT, a further conflict terminates as `STOP_CONTENDED`.

| Frozen stratum | Actual sequence | Final register | B disposition |
|---|---|---|---|
| Independent | A succeeds; stale B gets 409; B re-reads A, checks and appends once | A+B, revision 2 | REGISTERED |
| Semantic duplicate | A succeeds; stale B gets 409; fresh check finds same successor/question | A, revision 1; no recovery PUT | CONFLICT |
| Second mutation | A succeeds; stale B gets 409; B reads A; C commits A+C; B's sole recovery gets 409 | A+C, revision 2 | STOP_CONTENDED |

Allocation 004 completed all three schedules once: **9 measured update attempts, 5 commits, 4 explicit GitHub SHA-mismatch 409s**. Each successful commit has a subsequent content/SHA readback. No semantic duplicate is registered, no winning claim is lost, and no B case exceeds one recovery PUT. No case was extended or replaced inside 004. Counting the separately stopped 003 gives 11 measured update attempts overall; these are not 11 successful cases.

The independent result shows sharding is not necessary merely to recover this one unrelated conflict under quiescence. The second-mutation result also exposes the cost: the bounded strategy protects existing state but leaves B unregistered. It establishes neither starvation freedom nor guaranteed eventual progress under sustained contention.

## Local execution and audit

Environment: CPython 3.13.5, Linux 6.18.44 x86_64, glibc 2.41, Git 2.47.3, guest-reported AMD EPYC 7763, CPUs 0..4 visible; frequency unpinned. Standard-library Python only. The inspected CPU frequency is a snapshot, not a pinned operating condition. No benchmark latency, throughput, model/token or gameplay result is asserted.

Twelve test methods pass before 004 and after completion: ten policy tests and two auditor tests. One policy test enumerates all 90 legal permutations of one read and one PUT per three simulated clients. Its CAS is a local model; losing writers subsequently recover serially under quiescence. These 90 orders are not 90 GitHub or concurrent-process trials. The controls include task/scope conflicts, consumed IDs, malformed data, retry exhaustion and second mutation. Thirteen corruption variants are rejected by the independent-code auditor both on synthetic controls and, post-measurement, on the retained actual evidence projections.

The frozen auditor imports no policy/controller module. It checks expected payloads, stale/current SHA arithmetic, per-stage responses, required SHA-specific 409 messages, budgets, dispositions and complete final documents. SHA-256 binds source/evidence bytes; Git blob identities are recomputed locally and checked against retained GitHub objects. This is separate checking code written by the same session, not an independent human or agent review. It does not authenticate a fabricated server transcript by itself.

## H / T / D / C / U

**H:** one bounded semantic recheck/merge recovers the independent claim under quiescence, refuses a duplicate before recovery input, and preserves a newer third-party update by stopping on a second conflict.

**T:** one fresh allocation with three fixed ordered schedules and nine actual MCP update attempts, after source and supervision freeze. Each case has a separate register. Initial/current/final content, SHA, commit and error projections are retained. Unexpected setup failure stops the allocation; the initial 003 interruption demonstrates that this rule was applied.

**D:** PASS only when all exact final documents, conflict outcomes, retry bounds and source/audit checks agree. Silent overwrite or duplicate admission is FAIL. An ambiguous tool/transport rejection would be UNCERTAIN, not a GitHub CAS success. The four 004 refusals explicitly identify file/SHA mismatch and HTTP 409.

**C:** GitHub's single-file precondition provides stale-writer exclusion; semantic checks supply a different condition. Their conjunction under these ordered interleavings is not proof of every concurrent history. Naively replacing a SHA while keeping the old whole-document payload could erase A; the measured candidate instead rebuilds from the newly read document. A single register may still create contention among otherwise independent tasks.

**U:** exact authored question keys, exact rather than hierarchical scope equality, one connector/repo/branch, manual MCP orchestration, no faults between successful commit and acknowledgement, no permissions changes, network partitions, fairness, power loss or real work after claiming. Epoch/revision is not authenticated authority. Nested/alias scopes and paraphrased duplicate questions remain undetected. No calibrated combined uncertainty or coverage factor is meaningful for these deterministic fixture assertions; observed counts are not reliability estimates.

## Variable/field table and unit check

| Field | Meaning | SI unit | Definition | Domain/assumptions | Type |
|---|---|---|---|---|---|
| current | Latest read register | Not physical | Entire parsed document received in recovery GET | Validated fixture schema | Structured record |
| candidate | Proposed claim | Not physical | task_id, owner, scope, successor, question_key | All explicit, nonempty strings | Structured record |
| revision | Document update counter | 1 | Previous revision incremented on append | Nonnegative integer, not bool | Scalar integer |
| expected_sha | File update precondition | Not physical | Git blob ID of the exact read UTF-8 bytes | 40 hexadecimal characters; not branch HEAD | String identity |
| recoveries_used | Recovery PUTs already consumed | 1 | Caller-maintained count for this bounded attempt | Nonnegative integer; at one or more stop | Scalar integer |
| claims | Retained registrations | Not physical | Current list plus one accepted append | Exact-key conflict policy; synthetic only | Ordered list of records |

Counters are dimensionless; a digest is an identity rather than a duration or numeric confidence. No API response duration is substituted for end-to-end timing. There is no SI timing equation or speedup claim in this result.

## Reproduction and retention boundary

From `allocations/a2`, run:

```sh
python restore_results.py
python audit.py
python -m unittest -v test_policy test_audit
```

These commands verify/decode retained results and run offline tests; they never access GitHub or start a new allocation. `restore_results.py` refuses to overwrite differing existing result files. The complete lossless result bundle contains the MCP content/error/commit projections, audit output, summary, test logs and actual-evidence corruption checks. All source, both freezes, initial/current registers, interruption and result bundle are GitHub-retained. Original initial registers are recoverable from the immutable freeze commits and payload files.

Important boundary: `evidence.json` records exact relevant fields transcribed from MCP tool outputs. It is not a capture of HTTP headers, server access logs or two clients' network clocks. The raw output of a successful wrapper contains commit/blob identities, not a separately observed HTTP success code. No synthetic test record is relabelled as an actual API response.

## Next single question

A successful registration whose response is lost must not be confused with a rejected registration. Can a content-bound readback recognize an already committed identical claim after commit-before-response interruption, without granting another claim or silently treating a different owner as oneself? No such successor is executed here. Shared-runtime/production adoption remains HOLD.
