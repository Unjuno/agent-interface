# Query/retry linearization boundary — H/T/D/C/U

Origin: closed #24; published as successor #4126. Related: #3991, #4027, #2084, #2789.

## H

A read-only negative status is not a reservation. A separate fresh precheck can still become stale before the retry effect. Exact operation identity/content checked in the same write transaction as the local effect prevents the directed duplicate/rebound cases while preserving genuinely new operations.

## T

Provided Linux x86_64 execution container, CPython 3.13.5, SQLite 3.46.1. Standard library only. No Docker/OrbStack image-attested claim; no model/provider, GUI/keyboard/mouse, external network, credentials or user files.

Three policies:
1. `CACHE_QUERY`: reuse saved read-only status.
2. `SPLIT_RECHECK`: fresh read-only precheck, then separate effect transaction.
3. `ATOMIC_DEDUP`: check exact operation identity/content inside the effect transaction.

All policies use the same atomic local effect+receipt publication.

Nine schedules:
- FRESH_ONLY
- COMPLETED_BEFORE_QUERY
- ORIGINAL_BETWEEN_QUERY_PREPARE
- ORIGINAL_BETWEEN_PREPARE_COMMIT
- RETRY_BEFORE_ORIGINAL
- CHANGED_PAYLOAD_AFTER_PREPARE
- WRONG_SESSION
- BOOLEAN_DELTA
- NEW_OPERATION

Two repetitions = 54 formal cases. Two resident worker processes per case, explicit JSON-line barriers, private SQLite DB per case. Construction 27 cases is excluded.

The exact `runtime/cli_v1/attempt.py` from intake main was vendored byte-identically; blob `bd1725a18b6aef6f45c62297cbd794c760ea0a9f`. Its retention boundary was exercised but full public CLI/API/lease/GUI admission was not.

## D

`PASS_QUERY_RETRY_LINEARIZATION_SCOPED` iff all 54 ordered cases, 108 worker exits, two outer zero exits, frozen source identity, database reconstruction and raw-only audit reconcile; expected extra same-operation effects are 8 / 6 / 0 for CACHE_QUERY / SPLIT_RECHECK / ATOMIC_DEDUP, with changed-payload effects 2 / 2 / 0; fresh and new-operation controls remain live; all query/preparation operations remain read-only; no response grants input/retry authority; all corruption controls reject.

Complete scientific contradiction is FAIL. Missing source/process/raw/audit evidence is HOLD/STOP.

## C

The weak receiver comparators are deliberate controls. Current production safeguards could refuse replay elsewhere. The candidate assumes fixed scope, retained semantic operation identity/content, all participating writers use the same receiver transaction, and the effect lives in that same transaction.

## U

No arbitrary GUI/external-effect atomicity, power-loss durability, record retirement, malicious issuer, multi-database transaction, model recovery quality, token/latency benefit, natural race probability, distributed exactly-once or production promotion claim.

## Variable table

| symbol/field | meaning | SI unit | definition | domain/assumption | type |
|---|---|---|---|---|---|
| operation_id | semantic operation identity | 1 | fixed request key in fixture scope | non-empty string | identifier |
| delta | counter increment | 1 | effect magnitude per operation | exact int 1 or 2; bool rejected | scalar integer |
| counter | application stored value | 1 | initial 0 plus committed effects | nonnegative integer | scalar integer |
| epoch | fixture generation | 1 | fixed value 7 | exact trusted integer | scalar integer |
| time_ns | diagnostic monotonic time | s (stored ns) | `time.monotonic_ns()` | same-host comparison only | scalar integer |
| N | formal case count | 1 | 3 policies × 9 schedules × 2 reps | N=54 | scalar integer |

Dimensional check: all scientific gates are dimensionless counts/identity/bytes. No timing threshold is used for PASS/FAIL.

## Publication chronology

The experiment was locally frozen and executed before GitHub write actions were available in this conversation. Issue #4126 and this PR are retrospective publication of immutable retained evidence, not a claim of public preregistration.
