# Scope-typed singleflight T0 — Issue #6501

**Purpose:** test a small deterministic scheduler model for sharing only overlapping, equivalent, read-only verifier work. This package neither changes the runtime nor grants actuation authority.

## Status

Allocation T0-01 is terminal `STOP_OUTPUT_SERIALIZATION`; scientific result `NOT_EVALUATED`. Candidate=1, independent auditor=1, retries=0. The candidate's output had a literal backslash+n suffix, and the single auditor invocation rejected it as invalid JSON. Do not repair or rerun this allocation. See `REPORT.md`, `STOP.json`, and exact `run01/` receipts. The successor attempt is isolated in the sibling T0b package.

## H / T / D / C / U

- **H:** For genuinely equivalent simultaneous read-only verification requests, scope-typed in-flight coalescing reduces verifier invocations and queue/decision latency versus independent requests without unsafe admission or false shared conclusions. Predicate-only coalescing should fail planted controls.
- **T0:** Two-caller, deterministic single-verifier queue; each service takes 5 simulated milliseconds. Compare no coalescing, unsafe predicate-only keying, and scope-typed coalescing across ten frozen cases: same scope overlap; different target; generation flip before return; separate deadlines; one cancelled waiter; owner error; UNKNOWN; contradictory evidence dependencies; app restart/ABA; and a late caller after completion. The package uses only synthetic inputs, Python standard library, and no GUI, model, network, real user data, GPU, or external effects. A separately implemented raw-only auditor replays all candidate rows and checks fixed fixture expectations plus corruption controls.
- **D:** `PASS_METHOD_SCOPED` only if all ten cases and caller denominators reconcile, scope-typed coalescing joins only matching in-flight keys, every per-caller deadline/cancellation/current-generation check remains separate, owner errors and UNKNOWN are not upgraded, predicate-only cross-target/dependency/restart controls fail, all frozen scope-field and return-time boundary controls behave as preregistered, and independent audit/mutation checks pass. Any unsafe shared conclusion is `FAIL_METHOD`; incomplete or irreconcilable evidence is `STOP`/`HOLD`, not a pass.
- **C:** A production scheduler may already serialize or cache these reads. Safe equivalence may be uncommon; fan-out can amplify a systematic verifier error; real deadlines, cancellation, and GUI observer perturbation are not represented.
- **U:** This finite scheduler model cannot estimate real request correlation, real queue costs, runtime race behavior, verifier correctness, or GUI freshness. A positive T0 is method evidence only; it does not authorize runtime sharing, cache reuse, admission, or external action. Any T1 requires a disposable fixture and separately checked ownership/resource conditions.

## Frozen provenance and invocation boundary

See `FREEZE.json` for source/base/image identity, exact execution commands, and stop rules. The formal allocation is one candidate invocation and one independent auditor invocation, no retries. Construction tests and their outcomes are explicitly separate from those counts. Raw candidate JSON, auditor JSON, stdout, stderr, and exit receipts belong in the sibling `run01/` directory; historical source and raw outcomes must not be overwritten.

## Scope of possible result

Even a pass applies only to this synthetic two-caller scheduler, 10 fixtures, and the frozen simulated service model. It cannot establish a real Agent Interface efficiency, safety, product, or memory-isolation result. No Docker-versus-native migration claim follows from this Issue.
