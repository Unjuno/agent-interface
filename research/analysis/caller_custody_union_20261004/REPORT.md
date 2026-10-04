# Caller custody union successor

Status: HOLD for fresh exact-tree independent review and hosted Linux native CI.
This is a current-main rescue composition, not a formal, GUI, provider, or
task-effect qualification.

## Lineage and scope

- Base: `origin/main` `99f77c47b91466d49c1e9438f9518d2edec6706a`.
- Successor head at report creation: `903992f62f68b3a6e2b11db775b6053825c25e61`.
- Source PR #7494 (`rescue/caller-composed-5156-20261004`) and source PR #7330
  (`fix/caller-current-main-composition-i76`) were merged locally as separate
  parents without textual conflicts. Both source PRs and their branches remain
  unchanged and open. The union retains their frozen evidence packages.
- The composition restores the execute-return snapshot and exception custody
  protections identified as missing in #7494, while retaining #7494's typed
  refusal/dispatch and uncertain-tail handling. It does not infer that an
  absent legacy dispatch bit proves no input.

H: post-execute outer verification, clock, diagnostics, or terminal-journal
failures must not erase a valid execution receipt or understate possible input.
Failure-metadata validation must not erase finalized failed-attempt evidence.

T: compose the frozen #7494 and #7330 caller changes on current main, then run
their registered focused caller/custody/cost/metadata/diagnostic/progress suites
in ordinary and optimized Python modes; compare the complete local native
runner's failures with the current-main baseline.

D: preserve execution progress, delivery uncertainty, effect receipt references,
and failure attempt custody independently. Verify no replay or false success,
and ensure the integration catalogue selects each test module once.

C: saved browser/GUI evidence remains historical. These callback tests do not
establish live input, application effect, release behavior, or provider validity.
Full local runner status is not PASS on this macOS host.

U: no GUI/model/provider/formal allocation, production adapter, performance, or
task-success claim is made. A full Linux native run and exact-tree independent
review remain open gates.

## Validation

- Focused caller union: 74 tests PASS under Python 3.12.13, both normal and
  `-O` modes.
- Full native runner on the union: FAIL; protocol 526 tests (4 failures, 6
  errors, 5 skips), harness 205 tests (31 errors). A comparison baseline at
  `60997f0599392d1b06c638b7deb0f30c5855d152` (main's immediate integration
  tree before subsequent research-only additions; identical runtime and
  `research/live_control` test sources) failed the same exact protocol
  failure/error names (4/6) and the same exact 31 harness error names. The
  union adds 62 protocol tests over that baseline without adding a full-runner
  failure; this is not a substitute for the required Linux CI pass.
- Scoped `git diff --check` for caller code/tests and native registration: PASS.
  Applying `git diff --check` to the entire research evidence delta reports
  trailing whitespace in preserved CRLF/raw-log artifacts; those frozen source
  artifacts were not normalized or edited.
- Container execution was not available: the local Docker/OrbStack daemon
  previously failed image access with `operation not supported`; no container
  experiment is claimed here.

The next integration step is hosted Linux CI on this exact union plus a fresh
nonauthor content review. Do not merge or retire either source PR/ref before
those gates and current-tree application review pass.
