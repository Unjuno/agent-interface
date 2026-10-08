# Real Git multi-ref atomicity discovery v1

## Decision

**RETAIN multi-resource atomic effect transactions when one planned effect spans multiple versioned dependencies.** Two independent per-ref CAS operations are individually safe but can still create a partial effect when the first succeeds and the second dependency has changed. Git's native multi-ref `update-ref --stdin` transaction prevented that partial commit in the tested case.

Immutable source base: `21fb50be01e99816eb3a555e2ae131e679723f48`.

## Experiment

Real Git 2.47.3, XTerm/XTEST GUI dispatch through frozen `./go`. Plan-time state `r1=A`, `r2=A`; intended effect `r1=B`, `r2=B`. `other` is outside the dependency set.

After the adapter checks r1/r2=A and blocks, the harness does nothing, changes r2→C, or changes unrelated other→C. Then compare:

- `sequential_cas`: CAS r1 A→B, then CAS r2 A→B;
- `transaction`: one Git `update-ref --stdin` start/update/update/prepare/commit transaction with old A for both refs.

3 blocks × 3 cases × 2 modes = **18 XTerm/XTEST trials**.

| Case | sequential per-ref CAS | multi-ref transaction |
|---|---:|---:|
| stable | r1=B,r2=B 3/3 | r1=B,r2=B 3/3 |
| r2 A→C before effect | **partial: r1=B,r2=C 3/3** | **atomic reject: r1=A,r2=C 3/3** |
| unrelated ref A→C | r1=B,r2=B,other=C 3/3 | same 3/3 |

Per-resource CAS is therefore insufficient when the semantic effect itself spans multiple resources and partial prefixes are invalid.

Independent audit verifies all 18 rows, check→competitor→effect ordering, plan-time A/A, final refs, paired modes and manifest hashes.

Measured effect section:
- sequential CAS pair median **7.939 ms**, range 5.840–10.211 ms;
- multi-ref transaction median **4.143 ms**, range 2.508–7.501 ms.

Frequency is not pinned; timings are descriptive mechanism costs, not throughput claims.

### Variable table

| Name | Meaning | SI unit | Definition | Type |
|---|---|---|---|---|
| r1,r2 | refs written by one effect | 1 | both expected A, planned B | identifiers |
| other | unrelated ref | 1 | excluded from transaction | identifier |
| A/B/C | plan-time/planned/competing OIDs | 1 | distinct deterministic commits | identifiers |
| effect interval | sequential pair or transaction duration | s | monotonic end-start | scalar |
| repetitions | trials per cell | 1 | 3 | integer |

Unit check: ns endpoint differences convert to ms by division by 1,000,000; OIDs are unitless identifiers.

## H / T / D / C / U

**H:** if one effect writes multiple versioned resources, independent CAS updates can leave a partial prefix; an effect-owner multi-resource transaction prevents that failure while permitting unrelated-resource changes.

**T:** 18 frozen XTerm/XTEST trials; only dependency/write count increased from the single-ref Git rung.

**D:** PASS: r2 conflict gives partial prefix 3/3 sequentially and zero partial writes 3/3 transactionally; stable/unrelated cases complete 3/3 each arm.

**C:** Git has a native multi-ref transaction; many GUI applications do not. If partial effects are semantically acceptable/compensatable, this boundary may be stronger than required.

**U:** n=3/cell, local Git only, deterministic pre-effect conflict, no crash/remote refs/model. Counterexample/mechanism evidence, not incidence.

## ERROR CHECK

Independent audit checks all 18 rows and retained manifest.

## Next

Test **dependency completeness**: add one semantic dependency that the atomic write transaction does not name. Atomicity over an incomplete dependency set may still commit a semantically stale effect.
