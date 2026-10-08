# #6501: scope identity and in-flight lifetime over actual socket pairs

`PASS_SOCKET_SCOPE_TRANSFER_SCOPED`: the one frozen native execution retained
24 trials and 56 waiter decisions. The full-scope in-flight broker made 11
socket reads versus 14 for independent callers, with no wrong-scope descriptive
match. Predicate-only sharing made 7 reads, but four waiters received a different
scope and their descriptive match was false. Keeping completed full-scope
futures made 10 reads; its later caller reused a completed result, unlike the
in-flight contract. That cache comparison establishes a lifetime distinction,
not an unsafe or stale effect.

This is a disposable native construction transfer from Issue #6501's simulated
singleflight idea to real macOS AF_UNIX socket pairs and producer/handler
threads. It is not the separately gated GUI T1, a production broker, a latency
study, or a rerun of the cancellation experiments. No input, clipboard,
display, listener, network service, model, GPU, Engine or container was used.
Native execution was chosen for the OS socket/thread transfer under the user's
FINAL-v5 permission for independent mechanism work; it does not satisfy a
container-first GUI or formal allocation.

## H/T/D/C/U

- **H:** explicit complete request scope and removal of completed futures can
  preserve authored waiter boundaries when one actual socket read serves
  several registered waiters.
- **T:** six frozen cohorts times four mechanisms; independently reconstruct
  each cohort, wire payload, per-waiter response binding and invocation count.
  Retained-output corruption checks must reject all eight mutations.
- **D:** `fixtures.json`, `run-a01/raw.json` (280,302 bytes, 126 instrumented
  transport events), `run-a01/audit.json`, actual exit/UTC records, prospective
  source/dependency hashes and retained construction failures.
- **C:** authored scopes, explicit registration barrier, constant true answers,
  same-process socket server, fixed sequential trial order and no naturally
  arriving demand. Producer and instrumented server share this harness; the
  raw-only auditor is separate code, not an independent external wire capture.
- **U:** live observer identity/currentness, real source restart, natural demand,
  threaded broker registration, cancellation, process isolation/fairness,
  latency/task benefit, physical effects and authority are untested.

## Frozen contrast

Each mode sees the same 14 waiter requests in six cases. A fresh broker and
transport are constructed per case/mode. All registrations in a wave occur
before its owned server barrier opens; a later wave is registered only after
the earlier futures finish. Broker registration itself is sequential. Socket
workers execute concurrently.

| Case | Waiters | Independent | Predicate in flight | Full scope in flight | Full scope cache |
|---|---:|---:|---:|---:|---:|
| Four identical pending scopes | 4 | 4 | 1 | 1 | 1 |
| Different target | 2 | 2 | 1 | 2 | 2 |
| Different source-instance label (authored ABA) | 2 | 2 | 1 | 2 | 2 |
| Different dependency digest | 2 | 2 | 1 | 2 | 2 |
| Different window-start label | 2 | 2 | 1 | 2 | 2 |
| Same scope after completion, two waves | 2 | 2 | 2 | 2 | 1 |
| **Reads / wrong-scope descriptive refusals** | **14** | **14 / 0** | **7 / 4** | **11 / 0** | **10 / 0** |

All server answers are true. The four predicate-only wrong-scope waiters show
why answer agreement alone does not establish scope equivalence. These are
descriptive refusals: no response is used as permission to act. A source
instance label differs in the fixture; no actual process was restarted.

The eleven key fields are exact nonempty strings: verifier, source,
source_instance, target, generation, dependency, predicate, parameter,
window_start, window_end and role. Generation and window endpoints are
serialized authored labels, not observed generations or physical time.
Dependency is an authored SHA-shaped identity, not a computed live dependency.
Only four dimensions are varied here; this finite study does not establish
exhaustive key completeness. `monotonic_ns` is a diagnostic monotonic clock in
nanoseconds (1 ns = 10^-9 s), serialized under the event lock. No latency or
clock-accuracy claim is derived from it. Timeouts (2/3/4 s inside the harness,
30 s per primary command) are bounds, not measured service guarantees.

The method is related to Go's documented duplicate-call suppression for one
key; that API description supplies no proof of GUI scope equivalence
([singleflight documentation](https://pkg.go.dev/golang.org/x/sync/singleflight)).
Python documents a connected socket pair with AF_UNIX as the available default
([socketpair documentation](https://docs.python.org/3.14/library/socket.html#socket.socketpair)).
The cited rolling documentation is separate from the recorded installed Python
3.14.5 binary and stdlib hashes. No Go code or external dependency was adopted.

## First outcomes and provenance

The initial real-socket construction tests failed two of four checks: the
different target was treated as matching, and a completed result was reused.
`construction/red.*` retains that exit 1. The minimal broker correction used
the complete scope key (except the predicate-only comparator) and removed
completed entries (except the cache comparator). Green four-test and full
13-test construction results were exit 0. Construction runs are not the
primary allocation. Exact construction UTC and the initial red implementation
snapshot were not saved; those gaps remain explicit in `RETENTION.json`.

The corrected five source/input files were prospectively hashed in
`FREEZE.json` and committed at
`36dcd20bf0b84bab9ce9b5d82398f9b351342efe`. Intake main was
`f1416985d4ff9ce5bbf9f0f4be1be3d0ee669549`; immediately before execution,
`START_GATE.json` records main
`cb13a10dce358649458f5aea00947b8aa43fc5b8` and unchanged standalone dependency
scope. This study imports no repository runtime. The private launcher was
hashed in `run-a01/PRE_RUN.json` before invocation; its public copy replaces
only the absolute repository path. `RETENTION.json` binds original and public
hashes and every path-only redaction. Original logs remain private; primary
wire/exit records are unchanged. No consumed formal allocation was retried.

| Invocation | Actual exit | UTC start / end |
|---|---:|---|
| Candidate, exactly once | 0 | 2026-10-03T01:52:34.571117Z / 01:52:34.654844Z |
| Raw-only CLI auditor, exactly once | 0 | 2026-10-03T01:52:34.655263Z / 01:52:34.738185Z |

Source Git blobs, local files, Python executable and the socket/thread/pool
stdlib hashes were checked before invocation. The candidate created a new
output file exclusively. Both primary commands were bounded and their original
stdout/stderr and exits are retained. All 42 instrumented request/response/client
triples reconciled. Owned handler counts were zero after cleanup; thread-pool
shutdown returned. These are harness cleanup observations, not an external OS
thread census or process-crash recovery test.

After the primary pair, `check_retained.py` substituted the existing auditor
test fixture with retained raw and installed a guard that forbids candidate
construction. Nine checks (valid retained raw plus eight corruptions) passed
normally and under `-O`, without socket/candidate invocation. Its helper was
added after the primary; it is not part of the prospective five-file freeze.
Controls cover missing/duplicate trial, missing waiter, upgraded wrong-scope
claim, wire hash, bool-as-integer cleanup field, added authority field and
missing transport event. They do not establish rejection of every possible
forgery. `audit.py` imports neither producer nor transport code and uses explicit
exceptions, so its gates remain active under `-O`.

## Safe retained-data review

From this directory, without consuming or replaying the candidate:

```sh
sha256sum -c SHA256SUMS
python3 -B check_retained.py
python3 -B -O check_retained.py
```

The frozen primary commands are recorded in the execution JSON files. Do not
invoke them again under allocation `SOCKET-SCOPE-6501-A01-20261003-01a0ff53`.
`test_study.py` and the original `test_audit.py` setup construct new sockets;
they are construction tests, not a retained-data review command.

Evidence publication is separate from production adoption. Integration needs
an exact current-base/tree check, the fixed nonauthor committee's approvals,
actual rules/protection checks and a conditional apply mechanism. None is
implied by this scoped result. The common research deadline is unconfirmed and
was not set or reset.
