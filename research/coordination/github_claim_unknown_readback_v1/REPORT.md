# Bounded recovery after unavailable or ambiguous first claim readback

Task `COORD-GITHUB-CLAIM-UNKNOWN-READBACK-20260916-006`, Issue #381.

**Decision: `PASS_BOUNDED_UNKNOWN_READBACK_SCOPED`.** This is a fixture-level claim-registration outcome-recovery result. It does not establish GitHub availability, network-fault tolerance, authentication, production leasing, or exactly-once execution.

## Question

PR #373 retained content-bound claim readback when a fresh full GET is available after a successful commit whose acknowledgement is withheld from the classifier. This successor asks what the recovery policy should do when the first observation is unavailable or lacks enough canonical fields to decide.

The single added mechanism is a fail-closed intermediate state: unavailable or ambiguous evidence remains `UNKNOWN_READBACK`; no write is allowed. Exactly one later full GET is permitted.

## Freeze

Publication BASE: `f6822835f46f9f8f015317b0ef63a6fab6eed367`.
Freeze commit: `deea0a756d4241ce50c24ee3f605581b398380c7`.

Frozen blobs:

- `policy.py`: `3bac6dad19e03b8857766d03a3858ab494867fbf`
- `plan.json`: `ddc98324822db8e60818a7b8b87f7200aac27fc6`
- initial registers: `2c76f2a3...`, `10a07dfc...`, `2df0af14...`
- committed payloads: `ed0260a9...`, `20b1b5d2...`, `ceb3deab...`

All result files were absent at freeze. Recovery PUT budget was zero. One later full GET per case was allowed. Elapsed time was explicitly excluded as evidence of whether the original write succeeded.

## Measured first outcomes

| Case | First recovery evidence | First disposition | Initial commit | One later real GET | Final disposition |
|---|---|---|---|---|---|
| unavailable_then_self | `UNAVAILABLE` | `UNKNOWN_READBACK`; no write | `5820d4ca...` | blob `ed0260a9...`, exact frozen self payload | `ALREADY_REGISTERED_SELF` |
| ambiguous_then_other_owner | successor/question only | `UNKNOWN_READBACK`; no write | `94ca4f8e...` | blob `20b1b5d2...`, exact frozen different-owner payload | `CONFLICT_OTHER_OWNER` |
| ambiguous_then_same_owner_changed_content | owner nonce only | `UNKNOWN_READBACK`; no write | `b7da4a77...` | blob `ceb3deab...`, exact frozen same-owner changed-content payload | `CONFLICT_CONTENT_MISMATCH` |

Totals: 3 initial update attempts, 3 successful commits, 3 fixture-authored first observations, 3 `UNKNOWN_READBACK` intermediate dispositions, **0 recovery PUTs**, 3 later full GETs, 0 second later GETs.

## Interpretation

The safe recovery rule in this fixture is epistemic rather than temporal: missing or partial evidence does not mean the original claim failed. The policy neither resubmits nor infers absence. It waits for the one allowed full observation, then applies the content-bound identity rule from #368.

The same-owner changed-content case is the critical control. Knowing only `owner_nonce` is insufficient to recognize the prior write as self; task/scope/content must agree.

## Evidence boundary

The first `UNAVAILABLE`/`AMBIGUOUS` observations are authored fixture events frozen before measurement. They are **not actual injected network failures or stale-cache responses**. The later observations are real GitHub Contents API GETs. Successful `update_file` responses are retained only as evaluator evidence that each commit occurred and were not classifier inputs.

`verify.py` is retained deterministic offline checking code. This publication does not claim it was independently executed by another agent.

## H / T / D / C / U

H: unavailable or incomplete recovery evidence should remain UNKNOWN and authorize no write; one later complete readback can resolve the exact content-bound outcome.

T: three fresh registers, one commit each, frozen first observation, zero-write intermediate decision, exactly one later real GET, no retry PUT or second GET.

D: all three initial commits succeeded; first dispositions were UNKNOWN; recovery PUT count 0/3; later GET bytes exactly matched frozen payloads; final classifications matched SELF / OTHER_OWNER / CONTENT_MISMATCH. Decision PASS at scoped fixture level.

C: actual transport failure could also make the later read unavailable, stale, or inconsistent. This fixture only tests policy behavior given an authored unavailable/partial first observation followed by a valid later GET.

U: one repository/branch/connector and three sequential authored cases. No availability rate, latency, timeout, simultaneous-request ordering, permissions race, expiry, authentication, fairness, production authorization, or exactly-once claim.

## Next single question

If the **one allowed later full readback is also unavailable**, retain terminal `UNKNOWN` with zero writes versus introducing any lease-expiry/abandonment rule. Do not infer failure from time alone; if a later release/reclaim mechanism is proposed, its ownership/fencing semantics must be tested separately.
