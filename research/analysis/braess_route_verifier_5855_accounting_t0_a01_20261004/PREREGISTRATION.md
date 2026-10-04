# #5855 queue-conservation and finite-window controls — A01

Allocation: `BRAESS-QUEUE-ACCOUNTING-5855-T0-20261004-A01`
Frozen main: `9dc383a89043deb6199c847196498d867ba6bb75`
Candidate/auditor: one candidate invocation; run the independent auditor only
after candidate exit 0. No retries.

## H / T / D / C / U

- **H:** A task-ID conservation ledger at every event, plus explicit horizon
  censoring and retry-receipt identity, will reject three false-positive
  throughput/accounting patterns (dropping unfinished tasks, counting a
  duplicated completion receipt twice, and applying a steady-state queue
  identity to a transient startup window) while accepting positive complete
  and stable finite controls.
- **T:** Deterministic, local, single-process discrete-event traces. Keep the
  same four task IDs and offer times in the baseline and route-added arms.
  Include (1) complete baseline and a route-added arm whose complete-only mean
  looks faster while half its offered tasks are still queued/in service at the
  horizon; (2) one retry sequence with a duplicated terminal receipt ID; (3) a
  transient empty-start single-server window with two censored tasks; and
  (4) a stable periodic three-task fixture where finite-window
  `L = lambda * W` holds exactly. Recompute
  `initial_pending + offered = verified + rejected + skipped + queued + in_service + lost`
  after every event. The independent raw-only auditor must rebuild ledger,
  censoring, task completion times, occupancy area and both Little-law
  diagnostics from events rather than trusting candidate summaries.
- **D:** `PASS_ACCOUNTING_CONTROLS_SCOPED` only if both complete traces conserve
  all task IDs at every event; the route-added arm preserves 2/4 censored
  tasks and cannot claim denominator-complete improvement; the duplicate
  receipt is rejected and never counted as a second task completion; the
  transient window is identified as ineligible for steady-state inference;
  and the declared stable control independently recomputes equal
  time-average occupancy and `lambda * W`. Any missing, duplicated, or
  contradictory identity is `FAIL_ACCOUNTING`; incomplete event-state
  classification is `HOLD_UNRESOLVED_WORK`.
- **C:** All times, effects, releases and the finite workload are synthetic.
  The stable fixture is an exact periodic toy trace, not evidence of
  stationarity in a real service. The complete-only mean is diagnostic only;
  verified task count and censored IDs remain primary.
- **U:** This is a method/control experiment for the proposed #5855 ledger
  requirements. It does not test production routing, an actual verifier,
  GUI/task effects, runtime throughput, or a live deployment. Docker/OrbStack
  image inspection failed on a missing containerd content blob, so the
  deterministic candidate is deliberately one host-CPython process; no
  container is started and no external service is touched.

## Frozen constants and stop rule

- Horizon 10 ticks for the matched censoring pair; four fixed IDs offered at
  ticks 0, 1, 2, 3.
- Baseline serial service is 2 ticks/task; route-added serial service is
  1, 1, 10, 10 ticks/task. No task is added, removed, retried, or reweighted
  between arms.
- Retry fixture: one offered task, attempt 1 fails, attempt 2 verifies, then
  the same `receipt_id` is repeated under a distinct event ID. The expected
  auditor disposition is reject-duplicate-receipt, not a pass on throughput.
- Transient fixture: service time 2; arrivals at 0, 1, 2; observation window
  [0, 3]. Stable fixture: service time 1; arrivals at 0, 2, 4; window [0, 6].
- Stop before candidate if source/interpreter identity or output-path checks
  fail. After candidate invocation, audit once only if candidate exits 0.
  Preserve any candidate/auditor failure as the first result; no retries.
