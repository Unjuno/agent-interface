# Issue #5776 T0-v2 result — 2026-10-01

**Disposition: `FAIL_METHOD_SCOPED` for the preregistered recovery-sentinel statistic in this synthetic mechanism family.** Independent event-ledger audit passed; the proposed sentinel did not detect the gradual-recovery mechanism and instead warned on demand drift. This is not an Agent Interface deployment result.

## Frozen question and run

The allocation was frozen from main `4bf4cb04eade179be9f5a25b130ebe53ea3a71b7`. The candidate and independent auditor each ran once in separate local Docker containers using `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, Docker 29.8.0 linux/amd64, `--network none`, 1 CPU, 256 MiB, pids 64. Both exited 0. No GUI, model, external service, or shared runtime was used; containers were removed after exit.

The full deterministic prospective population contained 336 episodes (3 loads × 7 mechanisms × 16 IDs), 120 ticks per episode, and 40,320 event rows. Four fixed 4-tick probes were scheduled at ticks 20/40/60/80. Raw is 6,672,040 bytes. The independent replay reconstructed every backlog transition, explicit exogenous jump, envelope return, recovery interval, warning, loss label and probe schedule with 0 mismatches (`PASS_EVENT_REPLAY_SCOPED`). Raw and candidate stdout SHA-256: `C9297630B0AFC81D34F5F226D88F4C58411399E46D3B80A7EBC7268446A36048`; audit stdout SHA-256: `480CCD883A901049B681F6C5E1D65ADC46611A324AC4177FA1FB119758A8A38F`.

## First outcome

The preregistered statistic is last/first probe-to-envelope-return duration, threshold 1.5. Group counts (each n=16):

| Load / mechanism | Warnings | Episodes with loss label |
|---|---:|---:|
| high / gradual recovery | 0 | 0 |
| high / abrupt breaker | 0 | 16 |
| high / spontaneous failure | 0 | 16 |
| high / demand drift | 16 | 0 |
| all other load/mechanism cells | 0 | 0 |

Thus it failed to warn on either high-load gradual recovery or abrupt/spontaneous loss, while every high-load demand-drift episode warned without a loss label. The mechanism distinction required by the hypothesis was not achieved. These counts are deterministic fixture descriptions, not probabilities or population estimates.

## H/T/D/C/U interpretation

- **H:** Not supported in this frozen fixture; the predeclared sentinel did not identify gradual recovery.
- **T:** Synthetic fixed-event simulation; one candidate and one independent audit run.
- **D:** Audit gate passed; scientific discrimination gate failed. Preserve as `FAIL_METHOD_SCOPED`; no tuning or retry in this allocation.
- **C:** Queue level, demand drift, or static capacity may explain changes more directly. Current recovery statistic confounds those with response duration.
- **U:** All state, ranges, episode mix, labels and prevalence are analyst-authored. No calibrated false-alarm rate, low-base-rate predictive utility, source-bound event, real-world causal or product claim.

## Prior failed construction retained

Allocation 01 remains at `../issue5776-recovery-sentinel-t0-20261001/`. Its candidate succeeded but auditor exited 1 because abrupt/spontaneous exogenous backlog jumps were not represented in the event schema. It is classified `FAIL_CONSTRUCTION_EVENT_LEDGER_INCOMPLETE`, not pooled or overwritten by v2.

