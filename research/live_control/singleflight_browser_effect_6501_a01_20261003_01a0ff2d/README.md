# #6501 actual browser/effect transfer A01

Exact-scope in-flight read sharing preserved the authored application's nine
correct intended effects while reducing offered verifier requests from ten to
eight. Predicate-only sharing reduced reads to six but yielded only seven correct
effects: the same final admission gate safely rejected mismatched evidence.
This is a retained Windows headless DOM/HTTP construction result, not adoption
of a production broker or a claim that computer control is solved.

| Policy | Offered verifier calls | Separate warmup calls | Correct effects | Safe refusals |
|---|---:|---:|---:|---:|
| independent | 10 | 1 | 9 | 1 |
| predicate only | 6 | 1 | 7 | 3 |
| exact scope | 8 | 1 | 9 | 1 |

Five cases × three policies were executed in the predeclared rotated order,
with fifteen fresh sequential contexts and thirty waiter outcomes. Every waiter
has its own target/intent and final DOM/deadline admission. Effects are actual
private server state plus browser-visible feedback, scored from a separately
retained server ledger. No wrong target, reused intent, or duplicated commit was
observed in these finite conditions. All three policies share the same gate and
serialized UI action lane. A failed effect is not excused by lower read counts.

| Case | independent reads/effects | predicate reads/effects | scoped reads/effects |
|---|---|---|---|
| equivalent, cold | 2 / 2 | 1 / 2 | 1 / 2 |
| equivalent, warmed | 2 / 2 | 1 / 2 | 1 / 2 |
| mixed A/B targets | 2 / 2 | 1 / 1 | 2 / 2 |
| generation changes during flight | 2 / 1 | 1 / 0 | 2 / 1 |
| second caller after first completion | 2 / 2 | 2 / 2 | 2 / 2 |

The generation change intentionally invalidates waiter1 in every arm. Scoped
sharing lets waiter2 obtain its current generation; predicate-only sharing gives
it waiter1's stale descriptive value and the common gate refuses it. In mixed
targets, predicate sharing similarly refuses waiter2. The late-caller case proves
the settled entry is retired in this cohort; this is not an after-completion cache.
Warmup performs one additional real read per policy, counted above.

Method outcome: `PASS_BROWSER_EFFECT_METHOD_SCOPED`, raw-only audit zero errors,
twelve effective copied-data corruptions rejected. Frozen H outcome:
`H_PASS_AUTHORED_FIXTURE_ONLY`. Scoped two-effect cohort elapsed358.9415ms cold
and363.6664ms warmed; independent478.0660ms and466.3648ms. There is one measured
cohort per condition, no estimated distribution/confidence interval or general
speedup. All fifteen exact elapsed values, including slower or refused arms,
remain in `evidence/comparative-A01/audit.json`.

The service deliberately serializes read jobs and sleeps180ms. A release barrier
creates duplicate overlap. This explains potential benefit and limits transfer to
real demand. Neither180ms nor the5s waiter deadline is a measured backend latency
or a physical guarantee. UI serialization, driver overhead and unspecified other
host load are confounds. Source UI and offered demand are matched; rotating the
policy order does not make this a randomized repeated experiment. Total resources,
energy, model/token calls and background network were not instrumented. Page
traffic was routed to the owned loopback origin; browser launch flags disable GPU
and background networking but are not a host-wide isolation/enforcement proof.

Runtime: native Windows, CPython3.12.10, Node24.19.0, Playwright1.62.1, installed
Google Chrome154.0.8037.93. Bundled managed Chromium was missing, discovered before
construction; none was installed. Initial free host RAM about2.3GiB of15.7GiB,
other workload unknown. One owned headless browser and fresh disposable contexts;
no existing user profile or physical desktop input, shared live T1/R134 lane,
model worker, WSLc/container/Engine or main write. The browser's recorded process
exit code is0, fifteen contexts closed, server active reads0 and owned listener
thread terminal. This verifies the recorded child handles, not a general proof
about all operating-system descendants. No release of held physical keys/buttons
is claimed because none were used.

The fixed inputs are `FREEZE.json`'s ten hashes. `environment.json` and
`PLAYWRIGHT_FILES.json` pin selected native executable/main DLL bytes and all173
Playwright files; OS/transitive browser dependencies and clock trust are outside
the measurement. Node hrtime and Python perf-counter nanoseconds are separate
clock domains and never subtracted from each other. Numeric times/counts are
typed; JSON Boolean/integer substitutions are rejected by the raw oracle.

Source freeze56ac1a105e2d73f50276b14f449c2350fd4941ef was locally committed at
03:39:32Z before the only formal candidate invocation03:41:07.808951Z. Candidate
ended03:41:20.718479Z; separate auditor03:41:20.726479Z–03:41:20.883751Z; both
exit0, invocation counts1/1 and retries0. Its parent is main332da58a9b6b825c384a142dfb59d7ed2b8b774e.
The pre-execution GitHub freeze notification failed with HTTP503 and was absent
on subsequent all-page reconciliation. The [post-execution correction](https://github.com/Unjuno/agent-interface/issues/6501#issuecomment-5965196281)
explicitly discloses this. Local pre-execution fixing is evidenced; successful
remote preregistration is not claimed. The source freeze timestamp/hash alone is
not an independent witness of honesty. No result-dependent source/threshold/order
edit, omitted row, replacement candidate, or historical allocation replay.

Before freezing, fifteen ordinary broker/gate checks passed. The first two-context
setup and its exact six source files are retained in `evidence/setup/`; explicit
case-close state telemetry was then added. A distinct six-context mini in
`evidence/setup-v2/` covered mixed/generation cases and twelve controls. These are
construction outcomes, excluded from the formal15-row outcome. Both ordinary
construction stages passed and closed their owned resources. Original private
logs/receipts remain; public text derivatives only replace personal absolute path
prefixes. `CUSTODY.json` records both byte counts and SHA256 hashes and marks exact
original files; formal client/server raw and PNG are identical originals.

Raw preservation and audit are distinct from nonauthor review: the separate oracle
and fixture were written by the same author. It checks this literal workload and
twelve specified mutations, not malicious coordinated forgery or all scope/clock/
authority failures. Unknown predicates, cancellation/owner failure, cross-context
ABA and arbitrary application scope equivalence were not added to this study.
The fixture's plain visible intent strings are own-request binding witnesses,
not secret or unforgeable security capabilities. Server commits enforce own
intent/target/current generation; no production authorization claim is implied.

For retained-data review only, run `python audit.py evidence/comparative-A01
<new-audit-output.json>` from this directory (two path arguments on one line).
The output is exclusive-create. This re-audits existing bytes and invokes no
browser/producer. Candidate A01 is consumed and must not be replayed to improve
the result. Any future execution requires a distinct scientific allocation,
prospective protocol and actual authority. `runner.py` uses `STUDY_NODE`,
`NODE_PATH` and `STUDY_CHROME` supplied by the environment. The retained outer
wrapper is a declared path-redacted text witness rather than a portable launcher.

`PUBLIC_MANIFEST.json` binds all other package files by exact Git byte identity;
its own hash is bound externally by the change/proposal descriptor. The source
freeze commit precedes the evidence commit. No production/runtime, workflow,
shared index or historical evidence is changed. Main integration remains subject
to a fixed FINAL-v5 nonauthor proposal/quorum, current-tree validation, actual
repository rules and one expected-old forward update; no author self-vote.

Established comparison: [Go singleflight](https://pkg.go.dev/golang.org/x/sync/singleflight)
suppresses duplicate in-flight calls under a key; scope, freshness and input
authority still need their own checks. Browser controls use official
[Playwright Browser API](https://playwright.dev/docs/api/class-browser) and
[Page API](https://playwright.dev/docs/api/class-page). No Go implementation was
copied. Existing repository licensing applies; dependency source is pinned, not
redistributed. H/T/D/C/U and variable units are fixed in `PROTOCOL.md`.
