# #6613 successor A01: deadline scheduling under eligible multi-principal load

**Status:** preregistered CPU-only synthetic method experiment. This is a new
successor hypothesis, not the conditional T1 from the original issue. The
original service-debt A01 remains `FAIL_HYPOTHESIS`; its files, seed range,
allocation and report are not reused or edited. This successor evaluates a
different policy (EDF), on newly generated traces, with a separately frozen
decision rule.

## H / T / D / C / U

- **H:** On fresh finite two-principal single-server traces with mixed soft
  completion deadlines and longer hard eligibility horizons, earliest-deadline
  first (EDF) will produce at least 0.5 more on-time optional completions per
  trace on average than both FIFO and shortest-service-first in the
  `asymmetric_deadlines` stratum, without decreasing the aggregate on-time
  completion mean by more than 0.5 versus FIFO in either other stratum. It will
  never dispatch a task that cannot finish before its hard eligibility expiry,
  and will service an arrived mandatory system task at the first available
  dispatch boundary. Fairness/wait outcomes are descriptive, not an optimized
  endpoint.
- **T:** Deterministic single-server simulator; 40 fresh seeds (20000–20039) ×
  three predeclared strata (`asymmetric_deadlines`, `burst_recovery`,
  `revocation_mandatory`) × three policies (FIFO, shortest-service-first,
  EDF) = 360 trace-policy rows. Each trace has twelve optional A/B tasks; the
  third stratum adds one mandatory system task. Integer ticks, nonpreemptive
  service. `prepare.py` creates the immutable formal fixture before the
  candidate is frozen. Construction tests use only inline authored traces.
  Candidate and independent raw-only auditor each run once; no GPU, CUDA,
  model, GUI, network, container, WSL, retry or tuning.
- **D:** Auditor must independently replay all 360 rows exactly and reject all
  five planted raw-record mutations. Any unauthorized dispatch, service past
  hard eligibility expiry, omitted/late-priority mandatory task, or accounting
  mismatch is `FAIL_METHOD`. If integrity/safety gates pass but the on-time
  threshold is missed, disposition is `FAIL_HYPOTHESIS`. `PASS_METHOD_SCOPED`
  requires all gates and thresholds. Every disposition is limited to these
  authored synthetic traces; it is not a human fairness or product claim.
- **C:** EDF may improve due-date completion by sacrificing long-deadline work;
  nonpreemptive service, arrival pattern, eligibility horizon and authored
  distributions strongly determine the outcome. FIFO or shortest work may
  remain preferable for other objectives.
- **U:** The fixture does not represent people, authorization, actual GUI cost,
  real-world deadlines, or workload frequency. A finite seed set provides no
  deployment, population-fairness, safety or product-effect evidence.

## Distinction from adjacent work

The original #6613 A01 compared FIFO, shortest-service and service-debt under
deadlines and failed its wait-improvement hypothesis; no debt tuning follows.
#6347's retained work studies delay swaps and bounded arrival-window batching
for near-simultaneous conflicting intents, repeated-window allocation and
boundary gaming. This successor uses already-arrived independent jobs, variable
nonpreemptive service, soft completion deadlines and hard eligibility expiry;
it makes no claim about conflict arbitration, arrival batching, or speed-delay
fairness. Both remain finite simulations.

## Frozen execution contract

Input: `fixture.json`. Formal raw output: `candidate_raw.json` (must be absent
before the single candidate invocation). Audit output: `audit.json` (must be
absent before the single auditor invocation). Both files are create-only; never
overwrite. The auditor reads the raw result and fixture, does not import the
candidate, and independently reconstructs every scheduling decision. All
wait/expiry and per-principal metrics are retained separately; expired tasks
are not counted as starving or as completed.

The candidate must not be invoked until this protocol, fixture, source hashes,
empty output paths, current-main base, and Issue/branch/PR collision checks are
committed and reported on #6613. After the first formal result, no retry,
threshold adjustment, seed substitution, or policy tuning is permitted.
