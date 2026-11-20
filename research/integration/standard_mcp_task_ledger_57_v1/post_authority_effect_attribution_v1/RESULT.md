# Post-authority effect attribution — 2026-11-21

## Question

Does the current standard-MCP task ledger distinguish the same final task
postcondition when it occurs within input authority versus after authority has
expired, a release has been confirmed, and the finite neutral-input horizon has
ended?

## Frozen evidence and conditions

- Current main source: `cd4857dd3a2147d2dfa0c6109361760ba6e57518`.
- Ledger source blob: `dc358852bc9c72995f55d5f5ffb555091b479555`.
- Prior R149 evidence blob:
  `a7ea3c16a043cafe9a7164c1f6b8c6c166483236`.
- R149 raw packet manifest SHA-256:
  `c1a161054fd24e45c85c1ae57f19c927387bd5f9c6202d609688fcd3a90b3017`;
  the source README reports all 165 packet files matched.
- R149 authority expiry: `262847357442000` ns.
- Verified release receipt: `262847380075400` ns.
- End of 2 s sampled neutral horizon: `262849380883600` ns.
- Recovered terminal observed: `262849399688300` ns.
- Native queued task effect: `262850072367700` ns, 2,714.9257 ms after
  authority expiry and 691.4841 ms after the horizon ended.
- R149 public action remained `recovered`, release-confirmed, with
  `task_success=null` and `replay_allowed=false`. The independently audited
  fixture counter reached 1 after the retained native queue message was
  dispatched. This was one controlled fixture, not spontaneous late OS
  delivery or MAP01.
- No new provider call, GUI input, live session, Docker, or WSLc operation was
  made. The final-state digest in the test is reconstructed from `counter=1`;
  it is not represented as the original R149 artifact digest.

## Experiment

The regression constructs two standard ledger records with the same factual
independent task score (`true`) and terminal counter. One marks the effect
within authority; the other uses R149's actual post-horizon effect timestamp.
Both pass through the existing `ledger.summarize` implementation.

The new `effect_attribution_v1.adjudicate_effect` is a separate research
candidate. It preserves factual state success, classifies the effect relative
to authority expiry, release receipt, and horizon end, and reports a separate
`eligible_task_success`. It does not modify or replace the current ledger.

## Result

**GAP CONFIRMED; candidate seam scoped-pass.** The existing ledger returns
identical summaries for timely and late effects, including
`task_success=true`; it drops the `effect_phase` supplied by the score event.
The recovered public call itself remains unchanged at
`task_success=null` / `replay_allowed=false`. The separate candidate classifies
R149's factual effect as `after_release_horizon` and sets
`eligible_task_success=false`; an effect observed within authority is eligible,
and missing timing remains unknown.

This shows why a final-state score alone cannot support the #57 requirement of
task success after recovery. A future matched runner must retain factual score,
effect time/phase, authority expiry, release receipt and neutral-horizon end as
separate values. It must not turn a post-authority effect into a successful
authorized action or replay permission. The candidate is not yet connected to
the frozen comparison evaluator or public caller.

## Local verification

Using Windows CPython 3.11.9:

- Existing ledger tests: 13/13 normal and 13/13 under `-O`.
- New attribution tests: 6/6 normal and 6/6 under `-O`, including all four
  expiry/release/horizon timing bands.
- All four commands exited 0. Exact output logs and SHA-256 values are in this
  directory.

This is a current-main offline adjudication experiment over retained R149
summary evidence. It is not a new live experiment, provider-backed comparison,
MAP01 result, reliability estimate, or product completion certificate.
