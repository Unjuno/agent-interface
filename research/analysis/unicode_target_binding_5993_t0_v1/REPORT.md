# Issue #5993 T0 result — synthetic target-binding method

**Disposition: `PASS_METHOD_SCOPED`** for the frozen finite resolver table only.
This is not a GUI security, exploitability, application, or product PASS.

## Question and frozen test

H: exact comparison of a fresh, independently specified intended target ID
against the application's resolved target can prevent wrong-target effects
without rejecting legitimate exact multilingual IDs. A warning based on a
Unicode skeleton is not authorization.

The source-first freeze is commit
[`00e54b5`](https://github.com/Unjuno/agent-interface/commit/00e54b54c7b14a8aa688d284ac6d45d6dcdd58e0)
on branch `research/unicode-target-binding-5993-t0-20261001-task-01a0b97b`,
based on main `e12e4e2939890d735cb1b11df3a8d8b6a1cf4b9a`. It fixes 15 synthetic
cases and three policies (45 expected rows): literal requested/displayed
label matching, label matching plus a non-blocking skeleton warning, and
fresh exact-ID binding. Every case carries separate requested label, displayed
label, intended ID, resolved ID, resolver rule, freshness, and effect target.
Six rows declare label-to-distinct-ID resolver aliases; five of those pairs
have equal Unicode 18 internal skeletons, while one unrelated mismatch is a
negative warning control.

The first unformalized preparation did not separate requested and displayed
labels. A boundary probe caught that it failed to exercise the bidi alias
path. That preparation was never formally run. The corrected source and
independent auditor were construction-tested before the source-first freeze;
the full construction history is retained in `CONSTRUCTION_REVIEW.md`.

## Execution and result

- Candidate: one frozen host-CPU invocation, CPython 3.12.14, exit 0; 15 cases,
  45 rows. No GUI, model, provider, or network calls. No retries.
- Independent auditor: one raw-only invocation, exit 0; reconstructed 45/45
  expected case/policy keys, 0 errors; disposition `PASS_METHOD_SCOPED`.
- String-only policy: 6 wrong-target effects across the 6 declared aliases.
- Skeleton-warning-only: 5 warnings on skeleton-colliding aliases, but still 6
  wrong-target effects (including the unrelated mismatch, which correctly did
  not warn). A warning alone therefore did not prevent the simulated effect.
- Exact-fresh binding: 0 wrong-target effects; accepted 7 fresh exact
  multilingual/ASCII IDs; denied 6 mismatches; returned UNKNOWN for the stale
  exact row and missing resolved target.

Candidate stdout:

```text
{"cases": 15, "output": "candidate.jsonl", "python_ucd": "15.0.0", "rows": 45, "unicode_data": "18.0.0"}
```

The exact independent auditor stdout is retained in `AUDITOR_STDOUT.txt`; the
raw candidate table is `candidate.jsonl`.

## Environment boundary

Docker Desktop's UI showed Engine running and no running containers, but also
showed 39 existing containers and 67.06% CPU. `docker ps` and `docker info`
did not return within 10 seconds. No container was started, stopped, removed,
or otherwise touched. Given that state, this tiny pure-CPU table ran in the
available isolated Python process instead of Docker. This is explicitly
host-only evidence, not container reproduction.

Official Unicode 18.0.0 inputs were hash-checked before execution. Python
3.12.14 ships UCD 15.0.0; the mixed Unicode data/normalization version is a
limitation. Skeleton equality is only a suspicion signal and never grants
action authority.

## Limits and next rung

`displayed_label` and `fixture_label_resolver` are authored synthetic values;
they are not produced by a renderer. The T0 does not establish glyph collision,
real app normalization/resolution, accessibility text fidelity, focus freshness,
wrong-recipient/file prevalence, or production safety. It only validates the
finite representation/oracle logic described by Issue #5993. A GUI T1 would
need a separate disposable fixture, fresh source/branch/resource coordination,
independent resolver/effect logs, and a preregistered paired decision threshold.
