# Semantic publication atomicity — Issue #4299

## Retained first outcome

**HOLD_AUDIT_IDLE_WRITER_TRACE**. This is not a formal PASS.

Allocation `semantic-publication-4299-20260924-01` executed four frozen batches once: 32 fresh databases, 64 worker/writer processes. Every actor and batch child exited0. Reruns, replacements, exclusions and post-result scientific tuning: zero.

The frozen auditor executed 1,809 checks and found four errors, one per STABLE writer: c00, c01, c16, c17. It required a nonempty SQL trace even though these actors correctly received only CLOSE and executed no SQL after trace registration. The four-case construction subset covered active writers and missed this idle-actor boundary. This is an auditor coverage defect. It is neither missing actor-exit evidence nor an observed stale-publication failure by the candidate.

The frozen controls invocation exited1 with `baseline audit failed`; it performed no formal corruption trials. The preregistered errors=[] and all12-controls gates therefore did not pass. The first AUDIT.json, stderr and actual exit receipts are unchanged.

## Descriptive reconstructed outcomes

All values below are scoped to the retained directed process schedules. They are not a promoted formal success or natural race-rate estimate.

| Endpoint (16 cases per policy) | CHECK_THEN_PUBLISH | ATOMIC_VALIDATE_PUBLISH |
|---|---:|---:|
| Published proposals | 8 | 8 |
| Refused changed/unknown/context evidence | 6 | 6 |
| HOLD_BUSY without proposal | 2 | 2 |
| Stale binding at publication | 4 | 0 |
| Wrong READY value at publication | 2 | 0 |
| Authority grants | 0 | 0 |

Each schedule had two fresh repetitions per policy. Both publish STABLE and DURING_TOOLBAR. BEFORE_TARGET, BEFORE_UNKNOWN and BEFORE_CONTEXT are refused. Existing writer contention yields HOLD_BUSY without a silent retry.

DURING_TARGET weak rows publish READY after target B/gen2 committed, so both value and binding are wrong. DURING_ABA weak rows publish with generation1 after A1->B2->A3: READY happens to agree, but the binding is stale. Candidate DURING rows hold BEGIN IMMEDIATE across validation and INSERT/COMMIT. The competing writer's first attempt returns BUSY; one explicitly scheduled deferred attempt then commits the preserved mutation after proposal publication. Later state changes are not retroactively scored as a failed earlier publication.

The unrelated toolbar writer is also deferred by the candidate. Thus this coarse transaction boundary trades concurrency for correctness; no latency or resource advantage is claimed.

## Read-only diagnostic addendum

`posthoc/audit.py` imports the untouched frozen auditor and permits its empty-writer-trace error only when the trace bytes are empty AND the declared STABLE writer's exact protocol contains CLOSE alone. All other source/schema/process/wire/state/journal checks remain active. This is a same-author diagnostic addendum, not independent external review.

Diagnostic: 32 cases, 1,809 original checks, errors=[], four explicit idle-trace exceptions. It retains `first_formal_disposition=HOLD_AUDIT_IDLE_WRITER_TRACE`.

The original controls source is copied byte-for-byte into posthoc/ and binds this diagnostic auditor. All12 controls change evidence bytes and all12 are rejected, with per-mutation before/after hashes and retained changed payloads. Mutations test missing cases, identity, authority, actor exit, wire, transaction boundary, BUSY result, trigger state, proposal binding, false completion, batch denominator and missing SQL trigger. Rejections are not caused solely by stale raw-file checksums. No no-op mutation is counted. This does not substitute for the failed first formal gate.

## H / T / D / C / U

H: complete read dependencies checked outside publication can change before INSERT; a single write transaction spanning validation and publication excludes that interval in this fixture.

T: SQLite3.46.1, CPython3.13.5 standard library, provided Linux x86_64 container. DELETE journal; synchronous FULL; read_uncommitted0; busy_timeout0. Separate real worker/writer processes and connections; directed pipe barriers, SQL trace, trigger state journal, actual process exits and complete DB files. No model/provider/network experiment/GUI/task input. Four disjoint construction cases, then eight schedules x two policies x two repetitions. Timing is diagnostic order only; hardware frequency/load is uncontrolled. Docker/image identity unavailable.

D: initial integrity gate failed as described; retain HOLD. Diagnostic mechanisms match the intended table but cannot retrospectively change the original verdict.

C: dependencies and truthful generations are authored; SQLite's known single-writer mechanism serializes unrelated changes too. The intentionally weak comparator is not alleged to be production code. Triggers are a separate recording mechanism in the same cooperative DB, not cryptographic authentication or independent physical measurement.

U: hidden dependency discovery, application-effect authority, actual model usefulness, natural races, latency/energy/token benefit, power loss/crash durability, distributed commits and production adoption remain untested. No probability, calibrated physical uncertainty or human-tempo gain is inferred.

## Provenance and reproduction

Parent #4257 and all its retained outputs are unchanged. Public source-first commit: `f68e2c0ab24180896cc71bc577ca526a0047ce15`.

Source archive SHA256: `d90d4fff7b2f45c8160cadb737914639cf46d0fb38e5dc9ef5145f901468c241`.
FREEZE SHA256: `eb494ef033f94a1a22076c856704a2ebf82c72f8af30bae2823b11c131036ba2`.

The source capsule contains the full plan, field/variable table, schema, actors, runner, separate auditor, controls, schedule and environment, plus construction audit summaries. The complete evidence capsule additionally contains all construction and formal DBs, wire and SQL traces, process receipts, frozen failed audit, diagnostic code and effective mutation payloads. Restore only to a fresh trusted directory; the unpacker performs no experiment or network operation.

Read-only after evidence extraction:

```sh
python -I -S -B source/audit.py formal > /tmp/4299-first-audit.json
# Expected exit1; compare to retained AUDIT.json, do not call it PASS.
cmp AUDIT.json /tmp/4299-first-audit.json
python -I -S -B posthoc/audit.py formal > /tmp/4299-diagnostic-audit.json
cmp diagnostic_audit.json /tmp/4299-diagnostic-audit.json
python -S -B posthoc/controls.py formal /tmp/4299-controls-new
```

Never rerun consumed formal batches for publication or audit repair. An actual new scientific experiment requires a separately defined change and allocation. This HOLD and its diagnostic evidence can be reviewed without repeating any actor.

Primary mechanism references: https://sqlite.org/isolation.html ; https://sqlite.org/lang_transaction.html ; https://www.sqlite.org/lang_createtrigger.html . The repository experiment establishes only this concrete semantic-proposal boundary.
