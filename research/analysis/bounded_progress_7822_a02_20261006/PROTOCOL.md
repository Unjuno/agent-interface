# Issue #7822 A02 — bounded-progress supervisor synthesis

## Frozen question and scope

This successor tests whether an executable finite-horizon supervisor can be
synthesized from a public task contract and transition graph, rather than
hand-authoring the witness traces as in A01. It does not replace A01's result.
The finite cases have no GUI, model, user data, network, input, or external
effect. The implementation uses Python's standard library on macOS; no
container-isolation or runtime claim is made because the experiment is a small
trusted finite graph computation with no host-facing payload.

**H:** For the frozen fully observed finite event graphs, a bounded-horizon
reachability-game algorithm can return a safe controllable policy whose every
permitted run reaches an independently evidenced task marker within the
reported event bound, when such a policy exists. It must yield without a
completion claim when an adversarial uncontrollable cycle prevents a bound,
when marker evidence is absent, or when the public task contract conflicts
with the independent oracle. Ordinary safe nonblocking must still admit the
declared safe livelock.

**T:** Candidate input, independent oracle, case table, horizon cap, algorithm,
independent audit, and mutations are frozen in this package before the one-shot
formal candidate/auditor pair. Candidate and auditor are separate programs and
processes; candidate receives only `public_cases.json`, while auditor receives
the hidden oracle and the preserved candidate raw output. The auditor
independently reconstructs finite-horizon winning sets, enabled edges, safety,
marker reachability, all-path bounds, cycle behavior, and contract agreement.

**D:** `PASS_METHOD_SCOPED` requires exact agreement with the independently
recomputed minimal horizon on every eligible case; all permitted outcomes safe;
all paths reach an oracle marker within the reported bound; A01-style safe
nonblocking still admits the WAIT cycle; and no-progress, missing-evidence,
and contract-conflict cases produce no completion claim and a zero-effect
`YIELD`. Every declared corruption mutation must be rejected. Any unsafe
permitted edge, false completion claim, oracle mismatch treated as PASS, or
unbounded run treated as bounded is `FAIL_METHOD`; missing inputs or malformed
artifacts are `HOLD`.

**C:** A small explicit safe-yield/no-progress handler may be sufficient; a
general bounded supervisor can suppress useful exploration or optional work.
The candidate's finite graph and contract may still encode the answer.

**U:** The result covers only the frozen finite fully observed graphs. It does
not establish real GUI progress markers, partial-observation correctness,
wall-clock deadlines, fairness, live task completion, user benefit, or runtime
safety. An independent oracle detects contract mismatch in this finite model;
it does not establish that a real application effect source is trustworthy.

## Formal invocation and provenance gates

Allocation: `BP-7822-MAC-A02-20261006`. Freeze base main:
`4670a6fb5bc152087054ad84ff15cc8148f7683c`. Candidate exactly once; only if it
exits zero, independent auditor exactly once; retries zero. Construction tests
run before the source/output freeze and are not formal invocations. Preserve
all raw outputs and hashes. Do not rerun either formal role after any outcome.

No resource, shared-runtime, or GUI allocation is required. If local standard
library execution fails, preserve STOP and do not switch runtimes after the
formal freeze.
