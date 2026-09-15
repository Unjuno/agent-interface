# `authority_ended` receipt replay / remint discovery v1

Status: **baseline replay failure reproduced; RETAIN_LEDGER_CANDIDATE offline.** No live actuation, model, gameplay-efficacy, restart-durability or production-promotion claim.

## Discovery trigger

The live delivery-race work established that a valid first terminal can mint a one-use replan token only after post-authority evidence arrives. The token itself is one-use.

A direct replay of that exact retained terminal exposed a different failure: after the first token was consumed, passing the **identical terminal receipt** to the current stateless `open_replan_token` minted a second unused token. With current sequence 4, that second token revalidated. The existing one-use property therefore applies to a token object, not to the authority-ending receipt that creates tokens.

This failure is retained in `baseline-failure.json`. It is an offline caller-semantics failure using an actual retained live receipt; no GUI/input was rerun.

## Smallest repair

Add one runtime-owned identity to the caller receipt:

```text
authority_end_id = interruption.intent_token
```

and one session-scoped `issued_ids` ledger. The candidate validates the normal `authority_ended` receipt first, requires a nonempty runtime-owned identity, then atomically checks/marks that identity when a replan token is minted. A marked identity cannot mint a second token, whether or not the first token has been consumed.

This mirrors the project's existing one-reply-per-yield continuation-ticket discipline rather than adding a new policy concept.

The identity is never planner/model-authored.

## Frozen matrix

The preregistration fixed eight cases before running the candidate:

1. valid first issue;
2. duplicate receipt before token consume rejected;
3. duplicate after consume rejected;
4. same identity with altered post sequence rejected;
5. missing authority-end identity rejected;
6. early incomplete receipt remains rejected by the existing post-observation bridge;
7. the consumed token itself still reports `token_replay`;
8. one distinct runtime authority-end identity with a newer post sequence can issue normally.

Input fixture: the exact first terminal receipt retained from the live delivery-race seed 994200.

## First outcome

**8/8 PASS. Decision: `RETAIN_LEDGER_CANDIDATE`.**

The duplicate cases all fail with `authority_end_id already issued`. Missing identity fails with `runtime authority_end_id required`. The earlier delivery-race contract remains intact: no post-authority observation still fails with `post-authority observation required`. A different identity issues one token and revalidates on a later sequence.

### Local CPU cost

CPython 3.13.5, shared Intel Xeon Platinum 8573C, unpinned frequency, 7 repeats × 200,000 operations:

- duplicate-reject median: **1,109.98 ns/call**;
- first-issue harness median: **9,033.37 ns/call**.

The first-issue benchmark includes a `deepcopy` and constructing a fresh ledger on every iteration, so it is **not** a pure ledger overhead estimate. These are local function/harness costs, not end-to-end agent latency.

## H / T / D / C / U

**H.** Binding token minting to a runtime-owned authority-end identity prevents delayed/duplicate terminal receipts from reminting new replan authority while preserving a later genuinely distinct authority epoch.

**T.** One frozen eight-case offline matrix over the actual retained live receipt; no live input and no model calls. One preregistered local-cost block.

**D.** **RETAIN_LEDGER_CANDIDATE** because all eight cases match the frozen disposition and the baseline remint failure is closed in-process.

**C.** A process restart loses the in-memory `issued_ids` set. A caller that incorrectly lets the model supply `authority_end_id` could forge identities. Mark-on-issue is fail-closed but may reduce liveness if the caller loses the issued token without retaining its state.

**U.** Single retained source receipt plus synthetic mutations/distinct-ID control; no transport duplicate, no process restart, no live second action under the ledger candidate yet.

## Next smallest experiment

Integrate this ledger into the existing live two-dispatch caller only. In one fresh ViZDoom session, mint the token from the first terminal, then inject the exact same terminal receipt once **before** the valid later observation and once **after** the token has been consumed/second action completed. Both duplicate deliveries must be rejected and must create zero extra submits/input. A different live authority epoch is out of scope for that first integration.
