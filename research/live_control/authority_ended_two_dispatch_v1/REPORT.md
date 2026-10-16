# `authority_ended` two-dispatch session gate v1

Status: **PASS_TWO_DISPATCH_GATE** for frozen model-free session transcripts. No live GUI/model/input allocation and no production promotion.

## Question

The first integration established that a valid scheduled `authority_ended` receipt plus mandatory post-release observation can become `EXECUTION_INCOMPLETE / authority_unavailable` in the byte-exact adaptive caller v3 without task-success inference.

This block asks the next session question: **can a second semantic dispatch be impossible before that post-release evidence, then use only a one-use replan token and ordinary current revalidation/input admission after the evidence arrives?**

## Mechanism under test

One new model-free session gate only:

- bridge-valid `authority_ended` + post-authority observation creates a one-use `ReplanToken` bound to the post-authority observation sequence;
- no token exists when post-authority evidence is missing/stale;
- the next current observation must have a strictly later sequence;
- ordinary exact caller v3 `reuse_revalidate` and `final_revalidate` remain required;
- `execute` consumes the token exactly once;
- association changes and stale current observations stop before execute;
- replay of a consumed token fails closed.

No authority, task-completion state or effect success is inherited from the expired first program.

Caller Git blob remains `7faf042304728ce91a3e4f89d465b251ea0bf70d`.

## Frozen block

Three retained real-MAP01 quiet-hold receipts, six conditions each = **18 sessions**:

1. valid;
2. scorer privacy control;
3. missing post-authority observation;
4. stale/non-advanced post-authority observation;
5. stale next-current observation;
6. association changed before second dispatch.

For valid sessions the same token is then deliberately replayed once after the successful second dispatch.

## First outcome

Decision: **PASS_TWO_DISPATCH_GATE**.

- valid: **3/3** second dispatch reaches `TASK_SUCCEEDED`, but only after call order `reuse_revalidate → final_revalidate → execute → verify_effect`;
- scorer privacy controls: **3/3** same result;
- missing/stale post-authority evidence: **6/6** blocked before second caller invocation;
- stale-current / association-changed: **6/6** `SAFE_STOP` before execute;
- consumed-token replay: **3/3** blocked before execute;
- hard failures: **0**.

Formal local first-result SHA-256: `a2c505f793f2f9a9d258c4160512b6eee1397c084320911046fe1511d1b55a07`.

## Interpretation

The two lifetimes are now separated across **two caller dispatches**, not just inside an executor receipt:

- first program authority ends and cannot carry authority/completion into the future;
- the post-release observation opens only a one-use opportunity to reconsider;
- a later observation and ordinary target/freshness revalidation remain mandatory;
- only the new second execution can reach effect verification and task success.

This is consistent with capability-security semantics: the first action's capability expires; the post-release observation is evidence, not renewed authority; the next input authority must be freshly admitted.

## H / T / D / C / U

**H.** A sequence-bound one-use replan token can prevent semantic/action carryover across `authority_ended` while permitting normal caller progression after fresh evidence.

**T.** Exact caller v3, exact prior bridge, three retained real-MAP01 receipt rows, 18 frozen model-free session cases, no GUI/model/input call.

**D.** PASS if pre-observation cases never invoke second caller, stale/current-change cases never execute, valid cases use full ordinary revalidation path, and replay is rejected. All gates passed.

**C.** The one-use token is an experiment-local session primitive, not a proposed public ABI. Generic caller failure for replay/invalid gate may be operationally coarse. Live delivery races are not represented by transcript assembly.

**U.** No live concurrency, no real second X11/MAP01 action, no model. Next gate should use one live model-free session: produce actual `authority_ended` + post-release observation from an input owner, then attempt a second physical action only through the same sequence-bound gate and ordinary fresh admission. Include a deliberately stale second-observation control.
