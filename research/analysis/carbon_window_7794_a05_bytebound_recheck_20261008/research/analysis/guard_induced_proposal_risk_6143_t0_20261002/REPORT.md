# Issue #6143 T0 — guard-induced proposal risk accounting

**Disposition: `PASS_METHOD_SCOPED` for a frozen synthetic measurement fixture only.** This is not evidence that any model or agent adapts its proposals to a guard.

## H / T / D / C / U

- **H:** Correct fixed-proposal guard efficacy does not determine system-level harm when disclosure changes the proposal mix. Complete opportunity accounting can distinguish compensation, null, and protective adaptation.
- **T:** Three fixed 1,000-opportunity worlds, six arm rows total. Candidate and independent raw-only auditor each ran once after source freeze; zero retries. Eight construction tests passed before freeze.
- **D:** `PASS_METHOD_SCOPED`: the constructed compensation contrast yields 50 versus 60 harmful admissions per 1,000 original opportunities even though the identical guard rejects 90% of unsafe proposals and falsely rejects no safe proposals; the null yields 50 versus 5 with unchanged conservative proposal count; protective adaptation yields 2 harmful admissions in its guarded arm. All six opportunity denominators remain 1,000 and the raw-only auditor reports zero errors.
- **C:** The table is authored rather than sampled. Proposal adaptation can be absent or protective; task mix, proposal coding, guard exposure, and actual guard performance can independently change the net result. A fixed-proposal efficacy test and an adaptive-policy outcome answer different questions.
- **U:** No empirical planner behavior, risk compensation, calibration, task effect, inference, GUI, runtime, model call, participant, safety, latency, or product benefit. No longitudinal habituation test; no guard or route was changed.

## Frozen source and execution

- Issue: [#6143](https://github.com/Unjuno/agent-interface/issues/6143)
- Branch: `research/guard-induced-proposal-risk-6143-t0-20261002`
- Source base: `e3a57eeef93153483d2ce40d2ef8050c89945fcc`
- Freeze: [`FREEZE.json`](FREEZE.json); protocol: [`PROTOCOL.md`](PROTOCOL.md); integer fixture: [`fixture.json`](fixture.json).
- Candidate: `python -B candidate.py fixture.json` — one invocation, exit 0.
- Independent raw-only auditor: `python -B audit.py fixture.json results/formal-01/candidate.stdout` — one invocation, exit 0, `errors=[]`.
- Construction: `python -B -m unittest -v test_t0.py` — 8/8 pass; candidate/auditor/test syntax compilation passes.
- Runtime: CPython 3.12 on Windows host. Docker Desktop and backend processes were present, but Engine API probes (`docker version`, `docker info`) did not answer within the bounded timeout; no container was run and no daemon restart was attempted.
- Raw stdout/stderr, invocation counts, exit codes, result summary and hashes: [`results/formal-01/`](results/formal-01/). Source/output checksums are in `results/formal-01/SHA256SUMS`.

## Results

| Synthetic world | No-guard arm | Guarded/adapted arm | Harm per 1,000 opportunities |
|---|---:|---:|---:|
| Compensation | 50 unsafe proposals, 50 harms | 600 unsafe proposals, 60 harms after 90% rejection | 50 → 60 |
| Null adaptation | 50 unsafe proposals, 50 harms | 50 unsafe proposals, 5 harms after 90% rejection | 50 → 5 |
| Protective adaptation | 50 unsafe proposals, 50 harms | 20 unsafe proposals, 2 harms after 90% rejection | 50 → 2 |

The unsafe rejection sensitivity is 0.9 and safe false rejection is 0.0 in guarded arms. Refusals are retained as refusals, harm is counted against the original 1,000 opportunities rather than admitted actions, and the compensation-arm 100 retries remain explicit instead of inflating the denominator. The same guard has the same conditional behavior in all three worlds; only proposal mix differs.

## Stop and next rung

The method-only finite T0 is exhausted. T1 model cards, repeated-refusal adaptation, human studies, and live disposable comparisons are not authorized by this result. Any model-facing next rung requires its own explicit allocation, frozen coding/estimand and task opportunity frame, truthful matched information conditions, and safe no-effect design. No historical PASS/FAIL/HOLD/STOP was changed.
