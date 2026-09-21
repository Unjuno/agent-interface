# Issue #3946: process start-claim boundary

Governing allocation: `staggered-start-claim-3946-20260922-01`.
Base main: `b2457b746a6df06f6536585dfe2ab937aff639f4`.
Branch: `research/staggered-start-claim-20260922`.
Additive namespace: `research/coordination/staggered_start_claim_v1/`.

## H / T / D / C / U

**H.** A cached READY condition is insufficient at a later worker admission.
A current-condition check and durable request/resource claim in one transaction
prevent the declared stale, cancelled, expired, conflicting and replayed starts.

**T.** One formal invocation, 54 fresh private SQLite databases: two protocols
(`PRECHECK_ONLY`, `ATOMIC_CLAIM`) x nine scenarios x three repetitions.
Scenario order: ready, generation_changed, predecessor_failed, cancelled,
expired, competing_requests, independent_resources, completed_request_restart,
claimed_process_crash. Repetition order 0,1,2. Arm order is baseline/candidate for
0 and 2, candidate/baseline for 1. No randomization or random seed is used.
One second initial lease in expired cases; 60 seconds in others. Expired cases
wait beyond the actual monotonic deadline by 1 ms. This is not a recommended
production lease. Process response timeout 5 s; SQLite busy timeout 2 s.

Worker preparation is read-only and captures session/generation/deadline.
Admission is START, not task completion. Both arms write admission records in
SQLite transactions. Only ATOMIC_CLAIM revalidates and makes durable exclusive
resource claims. Work occurs at a later command, inserting a private effect row
and finishing the admission. An unresolved claim survives an injected SIGKILL;
a fresh worker must refuse the same request without inventing work completion.
Completed-request replacement must refuse duplication. Independent resources
must both be ACTIVE while both worker processes remain alive, before either
work command. This is logical interval overlap, not a CPU parallelism measure.

Separate subprocesses use isolated Python mode and a minimal environment.
A distinct observer database connection records state before and after every
command. Retain exact pipe frames, process identities/status/stderr, monotonic
times, event journals, database bytes (losslessly gzip/base64 encoded per row),
SHA-256s, execution result and source freeze. No network API, model, shell,
GUI, real task action or shared runtime is invoked. Provided Linux execution
container only; Docker CLI/image identity unavailable. No network namespace or
Docker-equivalence claim is made. External source publication uses GitHub MCP,
not experiment execution. No credential/environment-variable dumping.

**D.** Boundary PASS requires all54 cases plus source/database/process/raw audit
and twelve corruption controls. Per repetition, baseline must expose seven
unsafe starts (four changed conditions, resource competition, completed replay,
unresolved replay); candidate must have zero. Required baseline totals for three
repetitions:39 starts,21 unsafe,0 refused,36 private effects,39 worker processes.
Candidate:18 starts,0 unsafe,21 refused,15 private effects,39 worker processes.
Each candidate crash case retains one unresolved claim and zero effects; all
other candidate cases release completed claims. Independent-resource cases have
two ACTIVE records before work; candidate competing cases have one. Each phase
and exact order must reconcile with independent snapshots and final database.

Scoped PASS: `PASS_PROCESS_START_CLAIM_BOUNDARY_SCOPED`. Baseline policy rejection
is separately `FAIL_PRECHECK_ADMISSION_POLICY`. Candidate unsafe launch is FAIL;
source, timeout, schema, ownership or incomplete evidence is STOP/HOLD, never
scientific PASS. Construction paths are excluded. No formal rerun/replacement
or post-result code/gate change. Timings are diagnostic, not a speedup gate.

**C.** SQLite single-writer admission is the declared mechanism. The tested
residual is actual process/IPC/lifecycle composition. This is not a database
vulnerability claim. Claims constrain only participating workers. A crash can
permanently sacrifice liveness; safe takeover is not implemented or implied.
Mutation after successful admission and external effect exactly-once semantics
are untested. Workers are deterministic processes, not LLM sub-agents.

**U.** No held-out natural trace, model utility/tokens, cross-platform, GUI,
production, network safety or race-frequency result. #3158/#3199/#3209 and the
repository roadmap remain open. Independent means a different implementation
and process, not a different person.

## Roadmap and disposition boundaries

1. Read original sources, current goal, roadmap, open/closed Issues, PRs and
   branches; distinguish scope and avoid #3929/#3930/#2692 and model work.
2. Excluded construction (18 cases) and independently reconstructed audit.
3. Freeze exact source/environment and byte identities before formal.
4. Run one fresh54-case allocation locally; retain first outcome and partials.
5. Audit raw data/database bytes in a separate process; mutation controls.
6. Publish report/evidence via additive PR; verify source and main integration.
7. Clean only own merged branch when dependency-safe and supported. Do not
   delete others' retained evidence branches.

## Scientific references and source scope

- SQLite transaction documentation: https://www.sqlite.org/lang_transaction.html
  (read 2026-09-22 JST): one writer; BEGIN IMMEDIATE starts a write transaction.
- CPython subprocess documentation: https://docs.python.org/3.13/library/subprocess.html
  (read 2026-09-22 JST): subprocess pipes, statuses and explicit bounded cleanup.
- Predecessor current-main run.py Git blob:
  `b4143ac8a5b75aebd6baf3852fc4d4f56766e572`.
- Predecessor current-main audit.py Git blob:
  `81f271edfea952563d120dc8c9d251a63680212a`.
  They validate a finite generated table. Their sources/results are unchanged;
  this successor tests real private worker admission and replacement instead.
