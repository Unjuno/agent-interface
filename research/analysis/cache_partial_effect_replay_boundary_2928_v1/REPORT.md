# #2928 partial-effect replay boundary — exploratory decision-order check

Status: **MODEL_CHECK_ONLY / NOT_A_CACHE_LIFECYCLE_RESULT**

This additive note records a small exploratory Docker Desktop check prompted by the preserved `FAIL_CACHE_ADAPTER_CONTRACT_CANDIDATE` on [Issue #2928](https://github.com/Unjuno/agent-interface/issues/2928). It does not alter or retry any earlier allocation.

## H / T / D / C / U

- **H (exploratory):** If automatic reacquisition is permitted only when the previous operation is known to have had no effect, currentness is established, and the receipt is exact, then exhaustive enumeration of this finite abstraction will not recommend reacquisition after a confirmed partial or uncertain effect.
- **T:** Enumerate effect outcome × freshness × receipt: 3 × 3 × 3 = 27 states. Apply `REACQUIRE` only to `(no_effect, current, exact)`; use `YIELD` for all other states. Then run a second assertion-only enumeration with the same stated rule; this is a consistency cross-check, not an independent oracle. This rule was selected for this exploratory check; it was **not** a preregistered #2928 decision gate.
- **D:** The Docker enumeration reported 27 rows and zero partial/uncertain reacquisition recommendations. The separate assertion-only enumeration reported 27 states, one permitted reacquisition, zero partial/uncertain non-YIELD rows, and zero rule violations. This confirms only that the implementation matches the chosen rule.
- **C:** The rule is an explicit modeling choice, not a result inferred from observed GUI behavior. Another contract could classify a confirmed partial effect as a safe recovery path only if it proves the next operation is non-replaying and bound to fresh state. An exact receipt alone is not enough to establish that here.
- **U:** No caller code was executed; no cache was populated, invalidated, or reacquired; no GUI/application effect, costs, or cross-surface behavior was measured. This does not answer #2928's lifecycle matrix or satisfy its PASS gate.

## Provenance and commands

- Intake main: `34e42f84d56590fdda65c28c2b0692e42cc5a7f3`.
- Read-only source reviewed: `research/live_control/adaptive_acquisition_caller_v3.py`, GitHub blob `7faf042304728ce91a3e4f89d465b251ea0bf70d`.
- Local Docker Desktop context: `desktop-linux`, Engine `28.5.1`, linux/x86_64.
- Image: `python:3.12-slim`, exact local ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
- Both containers were ephemeral, offline and read-only, with CPU, memory and PID limits; neither invoked repository code.

Primary enumeration command (the first attempt with literal escaped newlines failed in Python before enumeration; zero rows were produced). Corrected command:

```powershell
docker run --rm --pull=never --network none --read-only --cpus=0.25 --memory=128m --pids-limit=16 python:3.12-slim python -c "from itertools import product; states=['no_effect','confirmed_partial','uncertain']; freshness=['current','stale','missing']; receipts=['exact','contradictory','missing']; rows=[(e,f,r,('REACQUIRE' if e=='no_effect' and f=='current' and r=='exact' else 'YIELD')) for e,f,r in product(states,freshness,receipts)]; unsafe=[x for x in rows if x[3]=='REACQUIRE' and x[0]!='no_effect']; print('rows',len(rows),'unsafe_retries',len(unsafe)); [print('|'.join(x)) for x in rows]"
```

Primary output: `rows 27 unsafe_retries 0`, followed by all 27 state/decision rows. Exactly one row was `REACQUIRE`; all other rows were `YIELD`.

Separate consistency cross-check command:

```powershell
docker run --rm --pull=never --network none --read-only --cpus=0.25 --memory=128m --pids-limit=16 python:3.12-slim python -c "from itertools import product; E=['no_effect','confirmed_partial','uncertain']; F=['current','stale','missing']; R=['exact','contradictory','missing']; rows=list(product(E,F,R)); expect=lambda e,f,r: 'REACQUIRE' if (e,f,r)==('no_effect','current','exact') else 'YIELD'; violations=[(e,f,r) for e,f,r in rows if ((expect(e,f,r)=='REACQUIRE') != ((e=='no_effect') and (f=='current') and (r=='exact')))]; partial=[x for x in rows if x[0] in ('confirmed_partial','uncertain') and expect(*x)!='YIELD']; print({'cartesian_rows':len(rows),'expected_reacquire':sum(expect(*x)=='REACQUIRE' for x in rows),'partial_uncertain_not_yield':len(partial),'rule_violations':len(violations)}); assert len(rows)==27 and sum(expect(*x)=='REACQUIRE' for x in rows)==1 and not partial and not violations"
```

Output: `{'cartesian_rows': 27, 'expected_reacquire': 1, 'partial_uncertain_not_yield': 0, 'rule_violations': 0}`; exit 0.

## Interpretation

This check makes the decision-order assumption executable and reviewable, but because the decision rule is encoded into the model, its agreement is not empirical evidence that the rule is correct or that the current caller implements it. The prior #2928 candidate FAIL remains unchanged. Required next evidence still includes a prospectively frozen independent oracle over actual cache/caller outcomes, effect/receipt lineage, and policy cost trade-offs.
