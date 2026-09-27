# Caller wait budget and source-time outcome — Issue #4067

## Current delivery status / chronology

This directory publishes the already executed conversation-local 18-case study.
It is **retrospective publication, not GitHub preregistration or a new formal run**.
The original REPORT.md and all 163 archived files are unchanged, including their
historically true BLOCKED_GITHUB_WRITE and no-remote-Issue statements. This dated
2026-09-22 delivery note supersedes those statements only for publication status.
No temporal source/threshold/result is repaired and its allocation is not repeated.
The subsequent unintended legacy GTK CI invocations are separately retained in
ci_incident/; they are not part of, or evidence for, the temporal study.

Parent #1764 remains its scoped finite-monitor result; #22/#2789's broader
application/model acceptance is not established. The supplied Linux x86_64
container has no Docker/OrbStack engine/image identity; no such replication
or production claim is made. No model, GUI or input work occurred in this study.

## Retained result

**PASS_CALLER_BUDGET_EVENT_TIME_BOUNDARY_SCOPED**. Six conditions, three repeats,
18 source/consumer pairs, 36 actual child exits 0. One formal orchestration.
The deliberately unsafe timer comparator has **6 false expirations** and
**3 separate unsupported silence classifications**. Candidate outputs are
SATISFIED 3, EXPIRED 6, TIMEOUT_UNRESOLVED 6, UNKNOWN_INCOMPLETE_PREFIX 3.
Raw-only audit errors 0; 12 corruption controls rejected; 8 unit methods pass.
Independent means separate implementation/process by the same author, not
external human review. Counts are directed coverage, not natural error rates.

| Condition | Cases | Candidate |
|---|---:|---|
| Timely B | 3 | SATISFIED |
| Silence | 3 | TIMEOUT_UNRESOLVED |
| Timely B delivered after the waiting budget | 3 | TIMEOUT_UNRESOLVED, not rewritten |
| B generated late | 3 | EXPIRED |
| Complete source prefix advances beyond deadline | 3 | EXPIRED |
| Source time advances after a missing sequence | 3 | UNKNOWN_INCOMPLETE_PREFIX |

The source allowance is 80 ms; caller budget is 160 ms after A reception.
Those durations have different endpoints. Source completeness is a trusted
fixture contract, not a property promised by arbitrary application notifications.
All outcomes are authority-neutral and historical; no action retry follows.

## Evidence and read-only reproduction

CAPSULE.json binds seven ordered binary parts, 39,312 compressed bytes,
404,311 decoded JSON bytes, 163 files and 373,563 original member bytes.
Every original source, raw pipe/clock/process record, construction record,
freeze, first result, auditor, test, and historical publication note is retained.
Readable policy.py, monitor.py, PLAN.md, REPORT.md, FREEZE.json and AUDIT.json
are exact original copies; the complete runner/auditor sources are in the capsule.
The SHA-256 commitments check integrity, not authentication.

From this directory, choose a new existing-parent destination:

```sh
python -I -S -B restore.py /tmp/temporal-4067-review
cd /tmp/temporal-4067-review
python -B verify_retention.py
python -B audit.py formal-01 --formal --mutations
python -B -m unittest -v test_policy
```

Do not invoke launch.py/study.py for the consumed allocation. The restorer does
not import or run any retained experiment. Local restoration/re-audit results
are in PUBLICATION_VALIDATION.json; repository CI/review is a separate gate.

## H / T / D / C / U and integration decision

H: a caller timeout is not a source-time failure certificate. T: actual separate
processes and pipes with six fixed delay/gap conditions. D: complete 18-case,
source/clock/exit/authority accounting, exact expected outcomes and independent
raw audit. C: deliberate relay faults and a trusted single complete source;
absence of a record alone cannot prove absence of the event. U: no real-producer
completeness, task/model usefulness, token/latency savings, cross-clock migration,
authentication, hard real-time or production guarantee. No calibrated combined
uncertainty or coverage factor is invented.

Return a distinct waiting-budget outcome when source completeness is unknown.
Late success may be retained as later evidence but must not rewrite an already
returned one-shot outcome. Source monitor state, caller wait state, physical
input state, task result and replay permission are separate contracts.

The one remaining integration question is whether the selected real producer
can supply a verifiable complete event prefix in a declared time domain. Do not
add another timer wrapper or rerun this fixture to substitute for that endpoint.

The original evidence publication changed only this new research namespace.
A subsequent CI incident required an additional engineering repair: three legacy
GTK allocation workflows are now manual-dispatch-only, with unchanged job bodies
and a new source-only regression. See CI_DELIVERY_INCIDENT.md. No runtime,
predecessor science or broad roadmap status is modified. The earlier 40-case
property study remains separately re-audited locally, not pooled and not claimed
fully published by this capsule.
