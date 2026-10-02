# Issue #5776 T0-v2 preregistration

## H/T/D/C/U

- **H:** Repeated fixed probes show mechanism-specific recovery-duration growth in the synthetic gradual-recovery cases and do not silently turn explicit abrupt jumps or complete prospective controls into apparent evidence. This is a falsification/ledger-integrity rung, not prediction validation.
- **T:** One episode for every 3 load × 7 mechanism × 16 ID cell. 120 ticks; fixed probes at 20/40/60/80 (4 ticks), 1-tick resolution, baseline envelope backlog ≤1, all 336 episodes retained. Candidate once; independent event replay once. No model/GUI or external system.
- **D:** Independent replay must exactly match every backlog, explicit exogenous jump, return interval, warning statistic, loss label and probe. Report the full population grouped by load/mechanism. A method result can only be `PASS_METHOD_SCOPED` for mechanical detection if gradual high-load warning precedes its loss while abrupt/no-collapse controls are not called gradual recovery. Predictive utility/false-alarm rate at deployment prevalence remains `UNKNOWN` by design.
- **C:** Queue level/boundary margin or a direct breaker may dominate; threshold and return envelope may be arbitrary. No claim of incremental warning over issue #5707 or #5671 baselines is tested.
- **U:** Synthetic deterministic values and labels; no external validity, stochastic false alarm estimate, real-world prevalence, intervention safety, observer cost, causal, runtime or product claim.

V1 remains immutable. This is a new allocation because it explicitly logs exogenous jumps and narrows the question after v1's incomplete ledger. Freeze hashes before running. Use local Docker pinned image, network none, 1 CPU/256 MiB/64 pids. No retry within this allocation.

