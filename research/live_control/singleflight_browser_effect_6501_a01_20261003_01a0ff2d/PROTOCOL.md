# #6501 browser/effect A01 — prospective protocol

Worker01a0ff2d-be6f-78d3-ad7c-497514c9079f; FINAL-v5. One new owned Windows
headless browser/loopback form transfer. Scheduler T0/T0b, socket, coroutine,
executor and waiter-deadline records are immutable and never replayed.

H: sharing only exactly equivalent in-flight read-only verification suppresses
actual fixture verifier calls, preserving independently scored intended effects
relative to independent reads. Predicate-only sharing should induce safe false
refusals for mixed targets or a generation change under the SAME consumer gate.
Any timing benefit is conditional on the authored fixture, not natural demand.

T: five literal cases x three policies in fixtures.json's exact rotated order,
15 fresh sequential browser contexts /30 waiters. Independent, predicate-only,
and exact-scope brokers share one common fresh/deadline admission check and one
serialized per-request action lane. Cases: cold equivalent, warmed equivalent,
mixed A/B targets, generation1->2 during flight, and a caller after completion.
Warming performs exactly one separate read per policy; include it in total calls.
Every offered cohort has exactly two intents and two requested verifications.
Source UI, observation cadence, offered demand, target/content and consumer gates
are otherwise matched. Native DOM reads bind source/target/generation/digest;
the costly read-only HTTP service serializes jobs with an authored180ms sleep.
An explicit external service-release barrier establishes overlap. The generation
case changes PUBLIC DOM while the first job is held, then registers waiter2.
This orchestrator barrier is not truth passed to the consumer. Each consumer
uses only its observed scope, descriptive result and fresh public DOM. Each
submit uses its own real form/intent capability, never a shared approval receipt.

Independent Python server logs request arrivals/service boundaries, current
generation, atomic target/intention checks, and actual per-case effect state.
Node controls only its private page and writes a separate client trace. The
raw-only Python auditor imports neither broker/candidate nor fixture and applies
literal expected cases, typed JSON identity, independent effect snapshots and
12 effective corruptions. Client and server clocks remain separate domains.

D: PASS_BROWSER_EFFECT_METHOD_SCOPED iff exact source/runtime/input pins match,
candidate/auditor each run once (exit0, no retry), all15/30 conditions match the
literal oracle, every result is tied to its actual server read, read counts are
correct, every wrong-scope/stale result refuses, exactly intended commits exist,
own intents are preserved, timing is coherent and cleanup is verified. Expected
offered reads INDEPENDENT10/PREDICATE6/SCOPED8, warmup1 each. Expected correct
effects9/7/9, refusals1/3/1. No wrong-target effect or borrowed intent is permitted.
H_PASS_AUTHORED_FIXTURE_ONLY additionally requires fewer offered reads for both
equivalent cases at two correct effects per arm, unchanged total correct effect
count against independent, and actual scoped cohort elapsed<independent in BOTH
cold and warm rows. Otherwise keep method outcome separate and H_HOLD; do not
retune the180ms service or5s waiter deadline, rerun, or drop slower/error rows.
Any incomplete child/provenance/cleanup record is STOP/HOLD, not inferred success.

Caps: candidate invocation1, raw-only auditor1 only after candidate exit0,
retries/substitutions0. Browser/contexts are sequential, one owned headless
process, loopback-only page requests, no existing user profile. Node's135s browser
watchdog precedes the180s parent observation bound. A timeout is a LIVE/UNKNOWN
handle to diagnose, not restart authority. Planned public raw/log/PNG <=3MiB;
exceeding that is a retained output-bound STOP. No hard host memory/CPU limit
enforcement claim. Initial host free RAM was about2.3GiB of15.7GiB; other load is
unidentified. This Windows installed-browser protocol is native; it does not
start WSLc/Docker/OrbStack or a shared display/game lane. No model/GPU computation,
physical desktop input, external effect or new worker. Browser args disable GPU,
extensions, component updates and background networking; each context routes
only its private loopback origin. Source/runtime/source-freeze hashes must stay
unchanged through execution; all first errors and setup outcomes are retained.

C: common final admission keeps predicate-only sharing safe but can discard a
valid caller because its shared evidence belongs elsewhere. Verifier workload
is deliberately serialized/delayed; an actual app without duplicate expensive
reads can show no benefit. GUI action serialization and driver overhead can erase
read savings. Strong ordinary cache/transaction rules may already suffice.

U: authored finite demand, ready predicates and service delays, one sequential
cohort per condition, rotating arm order, unmeasured background load. No natural
latency distribution, statistical safety/reliability rate, causal general speed,
model/token/human-tempo benefit, physical release/currentness/clock-trust result,
runtime adoption or broad computer-control completion. Broker lifetime is one
fresh cohort; cross-context ABA/owner failure/unknown predicates/cancellation and
general scope equivalence are not newly measured. Effects are actual disposable
server state and DOM feedback, not durable outside-world effects. Same-author
separate oracle is not a nonauthor review or proof against a malicious fixture.

Construction before freeze: 15 broker/gate checks passed; a first two-context
browser setup completed and closed before adding explicit independent state-close
telemetry. Exact initial sources/data/receipts remain private. A separately labeled
six-context mini checked mixed-target and generation behavior plus all12 raw
corruptions. It has no comparative H result and is excluded from the15-row outcome.

| 記号 | 日本語の意味・定義 | SI単位 | 範囲・前提 | 型 |
|---|---|---|---|---|
| generation | 公開画面とserverが持つ対象の世代 | 1 | このfixtureでは1または2 | 整数 |
| client ns | Nodeの同一process内の単調時刻 | ns | server時刻とは比較しない | 10進文字列で保存した整数 |
| server ns | Pythonの同一process内の単調時刻 | ns | client時刻とは比較しない | 整数 |
| elapsed | 同じ時計での終了時刻−開始時刻 | ns | 有限の実行条件内、非負 | 整数 |
| service delay | 作成した読取りserviceの待機指定 | ms | 180固定、backend自然遅延の測定値ではない | 整数 |
| waiter deadline | 各待機者の開始からの期限幅 | ms | 5000固定、物理期限の保証ではない | 整数 |

Established mechanism: [Go singleflight](https://pkg.go.dev/golang.org/x/sync/singleflight)
suppresses concurrent duplicate calls for a key. It supplies no GUI scope,
freshness, actuation authority or independent effect proof. Node Playwright APIs
are used only against an owned test application, not an existing user browser.
