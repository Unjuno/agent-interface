# Full retained MAP01 held-input occupancy posthoc — first outcome retained

Task `MAP01-HELD-OCCUPANCY-FULL-POSTHOC-20260916-001`, Issue #428.
Publication BASE `9558313ed704804031733031f9e9443ddffc54de`; source-first freeze HEAD `51255221771f35652ffe1bbb68ed20a07f36b8c7`.

## Decision

**`FAIL_INTEGRITY_ANALYZER_COVERAGE`.**

The complete retained v38/v39 computation did not produce aggregate occupancy intervals. The frozen existing analyzer fails closed on a real v39 runtime state that its construction tests did not cover: a hold step can start, admit only part of its requested key set, and be cancelled before emitting `keys_held`.

This is not a failed live run, model call, GUI task, or input allocation. It is an offline posthoc analyzer-contract failure discovered only when the already-retained full event stream was evaluated. The retained v38/v39 first outcomes remain unchanged.

## Frozen attempt

GitHub Actions run `35096754461`, job `104795892358`, commit `f2371d9a94f180f71356a3f4419ca3988a348b27` checked out the exact frozen branch. Before the full computation, the existing analyzer regression set passed **7/7**.

The full computation then stopped at:

```text
AssertionError: started hold never reached keys_held: ('cover-4', 10)
```

No `result.json` was produced; therefore the preregistered interval-width ratios and `RETAIN_FULL_OCCUPANCY_INTERVALS_SCOPED` / `SCHEMA_CENSORING_TOO_WIDE` gate were never evaluated. No aggregate occupancy number is inferred from a prefix.

## Exact retained counterexample

Read-only inspection of the SHA-bound v39 event stream shows the state is legitimate and informative rather than a missing-log artifact.

`cover-4` step 10 requests `Down + space`. The relevant ordered facts are:

| event | monotonic ns |
|---|---:|
| hold `step_started` | 55539809187659 |
| `Down` admission attempt | 55539824242850 |
| cancel command received | 55539824423539 |
| `Down` input acknowledgement | 55539824580162 |
| `cancel_requested` | 55539834799571 |
| owner verified empty, reason `cancelled` | 55539837451978 |
| final release verified empty | 55539849174411 |

No `keys_held` marker is emitted for step 10 and `space` is never admitted. Terminal status is `cancelled` with `steps_completed=10`.

Thus cancellation races the first key admission. The retained evidence proves at least one key admission occurred, but the full requested keyset was never established. For **any-key** occupancy, a conservative future rule could use lower bound `0` and upper bound from first admission attempt to the independently verified empty cancellation, **13.209128 ms**. That rule was not preregistered in #428 and is therefore not retroactively applied here.

## Workflow supervision failure retained separately

The temporary workflow used shell pipelines of the form `python ... | tee ...` without `set -o pipefail`. Consequently GitHub displayed the compute and subsequent audit steps as successful even though Python emitted tracebacks. The later output-hash step failed because `result.json` did not exist, and the artifact upload was skipped.

This is a harness/supervision defect, not scientific evidence of success. The Python traceback and absent result take precedence. The task is not rerun with a repaired workflow under the same identity.

## H / T / D / C / U

**H:** complete retained logs would be sufficient for the existing interval analyzer to reconstruct every accepted motor hold and model-wait intersection.

**T:** source-first frozen offline analysis of the exact retained v38/v39 report/event hashes; existing seven-test regression set; one GitHub-hosted compute attempt; no new live/model/input work.

**D:** **FAIL_INTEGRITY_ANALYZER_COVERAGE.** The analyzer's invariant that every started hold reaches `keys_held` is false for the complete retained v39 trace. No aggregate result is promoted.

**C:** the partial-admission state is not equivalent to zero input and must not be silently dropped. Conversely, assigning the programmed 300 ms duration would overstate occupancy. A conservative interrupted-partial interval is possible but needs a separately frozen rule and independent tests.

**U:** this result says nothing about total v38/v39 physical occupancy, useful task control, or comparative gameplay performance. It only establishes that the prior analyzer semantics are incomplete for full-trace reconstruction.

## Next single question

Under a new task identity, extend exactly one thing: interruption semantics for hold steps that terminate before `keys_held`.

The successor must distinguish at least:

1. **zero admissions before terminal** — no task-key occupancy;
2. **partial admissions before verified empty release** — any-key lower bound 0, upper bound first admission attempt to earliest verified empty release;
3. **all requested admissions but no `keys_held` marker** — conservative any-key interval, without claiming full-keyset establishment;
4. normal completed and already-supported interrupted holds — unchanged semantics.

Use this exact `cover-4:10` event sequence as a frozen regression control, then make one new complete-log posthoc attempt. Do not repair #428 in place.
