# Observed read-set dependency receipt — Git delayed delivery rung 5

Decision: **RETAIN_SCOPED_OBSERVED_READSET_RECEIPT** for this instrumented local Git fixture.

## Question
Rung 4 showed that a narrow dependency predicate becomes unsound when the declared set omits a real dependency. This rung changes only dependency provenance: planner self-report versus reads actually observed while evaluating the plan-time action predicate.

The authoritative predicate reads `declared.txt` and `hidden.txt` through `ReadTracer`. The planner declares only `declared.txt`. At delayed delivery both policies revalidate selected plan-time blob identities against the current target commit and, if valid, use Git-native current-OID CAS for the final ref write.

## Frozen experiment
Premeasurement freeze: `173252b1c848674fd22c3f3076495f81101b1935`. Publication base: `dce1ced12ab167563cf502ec62e87c4fe803afac`. Git 2.47.3 / Python 3.13.5. Forty fresh repositories: 2 policies x 4 schedules x 5 repetitions. No measured ID rerun.

| Policy / schedule | Correct | Rejects | Writes B |
|---|---:|---:|---:|
| planner_declared / stable | 5/5 | 0 | 5 |
| planner_declared / declared_changed | 5/5 | 5 | 0 |
| planner_declared / hidden_changed | **0/5** | 0 | **5 stale writes** |
| planner_declared / unrelated_changed | 5/5 | 0 | 5 |
| observed_readset / stable | 5/5 | 0 | 5 |
| observed_readset / declared_changed | 5/5 | 5 | 0 |
| observed_readset / hidden_changed | **5/5** | 5 | 0 |
| observed_readset / unrelated_changed | 5/5 | 0 | 5 |

The observed receipt records the exact Git blob OID for each path read by the predicate. Independent audit verifies that the plan predicate actually read both semantic dependencies and that the recorded blob OIDs equal the corresponding objects in plan-time commit A.

## Interpretation
This result supports a provenance split: planner-authored dependency declarations are claims; runtime-observed read receipts are evidence about accesses that actually occurred. Under this fixture, the receipt repairs the omitted hidden dependency without broadening to unrelated state.

It does **not** prove completeness of arbitrary read sets. Any dependency accessed outside the instrumented `ReadTracer`—native library state, subprocesses, environment variables, clocks, network/service state, hidden GUI state, or direct filesystem reads—can still be absent. The next discriminator is therefore an intentional instrumentation-bypass read.

## Verification
Frozen auditor passes 40/40. Independent extraction re-runs 5/5 tests and reproduces the audit exactly. Manifest verifies 2,047 files / 1,434,279 bytes with zero mismatches. Raw archive is conversation-only, 64,800 bytes, SHA-256 `479011156d40e930fe13d2dc2104ab047f43935370788cd3d4e960fd729c67f7`.

## H / T / D / C / U
**H:** observed plan-time reads can provide more complete dependency provenance than planner self-report.  
**T:** fixed 40-case Git matrix with one omitted planner dependency and one unrelated-change control.  
**D:** scoped PASS for accesses routed through the tracer; planner declaration exposes five stale writes, observed receipt zero.  
**C:** benefit could come solely from the fixture making all semantic reads instrumentable; bypass reads should defeat it.  
**U:** no automatic whole-process dependency capture, GUI/model/network/power-loss, multi-ref transaction, or performance claim.
