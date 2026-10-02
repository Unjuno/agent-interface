# Full-trace held-input occupancy reconstruction v4 — freeze

Allocation: `MAP01-HELD-OCCUPANCY-FULLTRACE-V4-20261002-01`
Base commit: `c81e3d8ffebc7cbc2af971dfb7fb2d9b1ba1f7fe`
Type: deterministic posthoc reconstruction, CPU-only; zero model/GUI/game/input.

## H / T / D / C / U

**H.** Every started hold in both complete retained traces can be safely
represented by interval-censored any-key occupancy. If one or more input calls
were admitted before cancellation but their acknowledgements arrived after the
cancel receipt, the conservative result is lower bound zero and upper bound
from the earliest admission timestamp to the earliest verified empty release.
The actual acknowledged key set and requested-but-unadmitted keys remain
separate. Exact ordinary key-up time is still unknown.

**T.** Run this candidate once on v38 and once on v39. Only if both exit 0, run
the separate raw-only auditor once on both outputs. Freeze source and input
hashes below. Construction suites: v1 7/7, v2 4/4, v3 5/5 and v4 4/4;
compile and `git diff --check` must pass. No tuning, retry, or mutation of raw
events.

**D.** `PASS_FULL_TRACE_INTERVALS_SCOPED` only if each started hold is covered
exactly once, normal holds retain the v1 raw-event bounds, no-admission cancel
is `[0,0]`, partial/in-flight admission gets lower `0` and the release-bounded
upper, post-cancel admission and unsupported observation/order cases fail
closed, and the independent auditor exactly reconstructs all rows and model-
wait intersections with zero errors.

**C.** An admission timestamp is not itself an acknowledgement or proof of a
positive held interval. Acknowledgement recorded after cancel does not prove
which side of the cancel boundary the OS event reached. The in-flight case
therefore earns no positive lower bound and is never called “no input”.

**U.** Two retained stochastic episodes; structural key-up censoring remains.
This is posthoc mechanism measurement only, not a new live run, semantic
success/effect, safety-rate, gameplay, efficiency, or human-tempo claim.

## Predecessors and construction

Keep the v1, v2 and v3 freezes, run records and outputs unchanged. V3 passed
v38 (11 holds) but stopped on v39 because `input_ack_ns` followed cancel by
156,623 ns even though `admitted_ns` preceded cancel. V4 changes only this
in-flight admission classification. Its first construction test run failed
one expected-value assertion (`20.5 ms`); raw timestamps show earliest
admission `104 ms`, release `125 ms`, so the bound is `21 ms`. The assertion
was corrected before freeze; this is a construction-test correction, not a
candidate rerun.

## Environment / isolation

Docker inventory showed the other active container `unjuno-native-ci-6092` and
no exclusive CPU-container allocation. It was not inspected, stopped or used;
no new container was launched. Run on local macOS arm64 / Python 3.14.5 CPU.
No container microbenchmark or isolation claim.

## Frozen code hashes

| File | SHA-256 |
|---|---|
| candidate `research/doom/analyze_map01_held_input_occupancy_fulltrace_v4.py` | `d01d2bdf53037db803627cc3ed2035e44118d66bcf364064a79c13d6f22c566c` |
| independent auditor `research/doom/audit_map01_held_input_occupancy_fulltrace_v4.py` | `f85b0463874d8a405636aae044967d16483ef65d18725903a24f602f90de3e0f` |
| tests `research/doom/test_map01_held_input_occupancy_fulltrace_v4.py` | `cd0914fbc31c77d2d3dc3509c63fa82445b1c4081895ee1f47be5edf5052f67d` |
| imported v3 candidate | `3e95222ac367cd0db85f8a5fd98ba0582623f252da0d5f98067377da3731b6e9` |
| imported v1 analyzer | `ea1f71939cd2dd963cde00e8b3d8f5c726de37f75e92096e7057d805387f3ebf` |

## Frozen input hashes

| Input | SHA-256 |
|---|---|
| v38 report | `7fa222f9b273ee10ad1ed3e24b8f7f234f46cc137265a90d70c6073981602f58` |
| v38 events | `80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3` |
| v39 report | `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687` |
| v39 events | `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381` |

Candidate outputs: `v38.json`, `v39.json`. Auditor output: `audit.json`.
