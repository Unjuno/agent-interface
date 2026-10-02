# Issue #5375 T0-a2 — post-trigger cascade capacity gate

## H / T / D / C / U

- **H:** In the stipulated feedback-on model, retry debt can maintain impaired safety service after a finite fault. Retry-debt shedding plus a reserved safety unit may recover service without authority admission.
- **T:** Three policies × three 30-tick scenarios; 270 raw rows. Cases: underload/no trigger, finite outage/debt with feedback off, and the same outage/debt with feedback on.
- **D:** `PASS_METHOD_AND_HYPOTHESIS_SCOPED`. Candidate exit 0; independent raw-only auditor exit 0; 9 groups / 270 rows reconstructed; all 270 joint-capacity checks pass; errors=[]. In the final eight feedback-on ticks, legacy shared retry provides safety service `[0,0,0,0,0,0,0,0]`, ending with retry queue 9 and safety queue 27. Debt-shed/reserved and no-retry controls each provide safety service `[1,1,1,1,1,1,1,1]` and end with primary/retry/safety queues 0/0/0. All policies recover in underload and feedback-off controls. Authority admissions=0 throughout.
- **C:** Values, outage, and retry-feedback law are hand-authored synthetic assumptions. The retry rule may create an artificial sustained state; this is sensitivity evidence about the specified model, not calibration or causal evidence about Agent Interface.
- **U:** No real verifier, concurrent runtime, production failure, stochastic workload, user task, GUI, latency, safety, or product behavior was tested. No production policy or live allocation follows.

## Joint capacity invariant

Every raw row was independently checked for primary/retry/safety queue conservation and chronology. Resource occupancy is the single sum of ordinary-primary service + retry service + safety service + failed-attempt resource, constrained to `<= 4` on every tick. This explicitly closes the missing joint-capacity gate from T0-a1; the old T0-a1 source, output, and failure remain unchanged.

## Execution boundary and stop

The formal candidate and auditor each ran once on bounded host CPython 3.14.5 / macOS arm64, retries=0. No container was launched: #5085's shared OrbStack lane remained occupied by unrelated `unjuno-native-ci-6092`, and its queue rules prohibit another container until explicit release. This is not a container result. T0-a2 finite replay is exhausted; runtime concurrency, calibration, and real workload testing remain unestablished.
