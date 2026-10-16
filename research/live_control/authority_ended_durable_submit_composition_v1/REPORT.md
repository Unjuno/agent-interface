# Durable `authority_ended` token + `durable_submit_v6` composition v1

Status: **RETAIN_COMPOSITION_CANDIDATE** in offline fault-injected transport. This closes the *untracked* consume-before-submit gap by converting it into the repository's existing explicit unresolved-delivery state; it does not establish exactly-once external effects or live-GUI composition.

## Question

The retained restart-durable authority-ended token state persists `pending -> consumed` before a new physical action is submitted. A crash after durable consume but before OS submit is safe from replay but can silently lose liveness.

`durable_submit_v6` already persists a command as `pending / may_have_been_sent` **before** invoking its transport callback. This experiment tests one ordering only:

```text
durable_submit precommit pending
-> transport callback begins
-> durable authority token consume
-> actual transport
```

If caller death occurs after the token is consumed, the command must already exist in the durable-submit journal. Restart must block any new command and allow only read-only reconciliation.

## Frozen fault matrix

Input token: the retained runtime-owned authority-ended receipt fixture. Components: unchanged `durable_submit_v6` plus unchanged retained durable pending/consumed token state.

Four separate-process cases:

1. **normal** — precommit -> consume -> transport returns exact command echo + accepted + verified terminal;
2. **crash before consume** — process exits inside transport callback before token consume;
3. **crash after consume, before send** — token is durably consumed, then process exits before simulated server receipt;
4. **crash after send/server receipt, before caller response** — token consumed and exact server records are persisted, then caller exits before receiving them.

Every crash case must retain durable-submit `pending.write_state = may_have_been_sent`. While pending exists, a new command must be rejected before the transport callback is invoked.

## First outcome

**4/4 PASS. Decision: `RETAIN_COMPOSITION_CANDIDATE`.**

| Case | token state after crash | durable-submit state | new command | read-only reconciliation |
|---|---|---|---|---|
| normal | consumed | terminal resolved, pending cleared | n/a | terminal already known |
| crash before consume | pending | unresolved pending | **blocked before transport** | no evidence -> remains unresolved |
| crash after consume before send | consumed | unresolved pending | **blocked before transport** | no evidence -> remains unresolved |
| crash after simulated server receipt | consumed | unresolved pending | **blocked before transport** | exact echo+accepted+verified terminal -> resolves |

No crash path performs automatic retry/replay. The no-evidence cases remain explicitly unresolved rather than being guessed `not sent`.

## Architecture implication

The retained token ledger and durable-submit journal solve different problems and should not be collapsed:

- **token state**: has this authority-ending semantic transition already authorized/consumed one replan execution?
- **durable-submit state**: may a concrete transport request already have crossed the process boundary, and what exact server evidence resolves it?

Precommitting the second state before consuming the first turns the previous untracked crash gap into the already-defined `PENDING/UNKNOWN` delivery contract. It preserves safety but cannot guarantee liveness when no independent server evidence ever appears.

## H / T / D / C / U

**H.** Existing `durable_submit_v6` precommit can cover the authority-token consume-to-transport crash interval without a new transaction protocol.

**T.** Four frozen separate-process cases with injected crash positions; fake server evidence is exact and only present in the send-before-crash case. No GUI/model/live socket.

**D.** **RETAIN_COMPOSITION_CANDIDATE**: all crash cases remain pending, every new command is blocked before transport while pending, and only exact read-only evidence resolves the sent case.

**C.** A crash before any actual transport still leaves conservative `may_have_been_sent`, so liveness can be lost. The experiment injects transport/server evidence rather than exercising a real AF_UNIX socket.

**U.** No live GUI/server, no cross-domain authority semantics, no malicious/torn state beyond each component's existing tests.

## Next smallest experiment

Do not immediately run a cross-domain live edit. The existing Inkscape expiry-observation path uses legacy terminal `expired` and lacks the independent observation-lifecycle deadline required by the newer `authority_ended` gate. First test that semantic mismatch explicitly. If the old receipt cannot be upgraded without inventing evidence, add only the missing lifecycle evidence/status in a versioned Inkscape candidate; then compose with live durable-submit.
