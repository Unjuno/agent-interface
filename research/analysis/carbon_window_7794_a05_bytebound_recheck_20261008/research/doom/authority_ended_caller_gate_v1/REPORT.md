# `authority_ended` caller-gate exploratory fault injection v1

Status: **exploratory development evidence only; RETAIN the fail-closed caller contract as the next integration candidate; no formal/preregistered efficacy claim.**

## Question

The dual-lifetime MAP01 discovery block introduced a narrow status meaning: scheduled input authority can end, verified input can be empty, and one passive post-release observation can still arrive. That is not equivalent to program completion or task success.

An older permissive caller shape can move to the next semantic decision once a terminal exists. This experiment asks one question only: **does an explicit gate reject malformed/unsafe `authority_ended` receipts while accepting the actual valid quiet-hold receipts?**

The permissive comparator is intentionally simple (`terminal_status` present + scorer agreement). It abstracts the risky legacy shape; it is **not claimed to be a byte-for-byte model of the newest overlap controller**.

## Data / fault matrix

Input: the three real-MAP01 quiet-hold result rows retained in `research/doom/container_dual_lifetime_discovery_v1/quiet_hold_result.json` on main at base `06e4606aba4e6881949bd5f7487a625407d8887d`.

For each valid row, create five one-fault-at-a-time copies:

1. missing post-authority observation metadata;
2. one post-release input admission;
3. old input tail marked resumed;
4. release marked unverified;
5. final scorer agreement false.

Thus the matrix has 3 valid rows + 15 injected faults. No GUI/model/game process is rerun in this block.

Candidate gate requires:

- verified empty release;
- final scorer agreement;
- `authority_ended` rather than treating any terminal alike;
- exactly one fresh bounded post-authority observation;
- zero post-release input admissions;
- no authority regrant and zero old-tail resumption.

On success it returns `PARTIAL_EFFECT_REPLAN_READY`, deliberately not `PROGRAM_COMPLETED` or task success.

## Result

| policy | valid rows admitted | injected faults admitted |
|---|---:|---:|
| permissive terminal + score comparator | 3/3 | **12/15** |
| explicit `authority_ended` gate | **3/3** | **0/15** |

The three scorer-disagreement cases are the only injected faults the permissive comparator rejects; missing post-observation, post-release input, tail revival and unverified release remain falsely ready under that comparator.

A CPU-only Python microbenchmark on the same shared Intel Xeon Platinum 8573C host, CPython 3.13.5, unpinned clock, ran 7 repeats × 200,000 evaluations of one valid receipt. Median gate evaluation was **399.090 ns/call**, range **386.702–403.245 ns/call**. This is only local function-call cost; it is not an end-to-end planner/runtime latency claim.

## H / T / D / C / U

**H.** Explicitly separating partial post-authority replan readiness from program/task completion can close receipt-level failure modes with negligible local computation.

**T.** One exploratory fault-injection pass using three retained real-MAP01 quiet-hold rows and five single-fault mutations per row. No preregistration, no new model calls, no live actuation.

**D.** The candidate catches every injected fault and preserves every valid retained receipt. **RETAIN as a caller-integration candidate**, not as formal proof or production promotion.

**C.** The permissive comparator is deliberately simplified and may overstate weakness of a newer caller that already checks some fields. Conversely, the injected faults do not exhaust aliasing, stale sequence, duplicated receipt or application-semantic failure.

**U.** n=3 source receipts; injected faults are synthetic; microbenchmark clock/CPU are unpinned; no planner behavior; no live next-action admission was attempted.

## Next smallest experiment

Integrate this gate into exactly one existing caller/recovery path without changing control policy. Use a model-free transcript test first: valid `authority_ended` + fresh post-release observation may open a new semantic decision, but missing/stale observation, unverified release, post-release input, or tail revival must stop. Measure caller outcome classification only. Do not combine this first integration with the separate two-phase PNG-publication candidate.
