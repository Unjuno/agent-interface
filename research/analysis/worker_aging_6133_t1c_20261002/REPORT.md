# Issue #6133 T1c — WSLc worker-aging measurement-gate successor

## Disposition

`PASS_METHOD_SCOPED`. The frozen synthetic construction detected the stipulated joint leak in all three policies, rejected aging classifications for no-aging, cache-plateau, thermal-only, and hidden-state controls, and flagged exactly one stale-output mismatch in each hidden-state policy cell. The independent raw-only auditor reconstructed all 600 job records across 15 cells with zero errors. The prior T1b `METHOD_FAIL_AUDIT` is preserved unchanged; T1c is a fresh successor, not a retry or repaired verdict.

## Results

| Scenario | NEVER | FIXED_AGE_10 | RESOURCE_THRESHOLD_112 | Output mismatch per cell |
|---|---:|---:|---:|---:|
| no aging | not detected | not detected | not detected | 0 |
| monotone leak | detected | detected | detected | 0 |
| cache plateau | not detected | not detected | not detected | 0 |
| thermal only | not detected | not detected | not detected | 0 |
| hidden state | not detected | not detected | not detected | 1 |

Fixed-age restart due events overlapping jobs 10–12 were deferred with the obligation retained; no restart crossed a pending obligation. Every committed restart carried a rejected receipt for the old generation. Cells with no committed restart had no old-generation receipt requirement, and the independent auditor accepted them. Age and RSS/latency measurements were bound to the same pre-transition job state; post-transition generation and age were stored separately. Cache-only RSS growth triggered some resource-policy restarts but did not satisfy the joint aging detector.

The frozen suite passed 4/4. Candidate ran once and wrote [`raw.json`](results/t1c-one-shot-01/raw.json); a separately authored raw-only auditor ran once and returned `PASS_METHOD_SCOPED`, errors `[]`. The raw SHA-256 is `32db0f79a9d2f9baaf242a85c2a0e523b04017ebced71797f3a971bbbd8b9526`; the combined container log SHA-256 is `99fb041c4cf8186a5d4333e85b29802e3a4967cff48005f0987fa9fba972c571`. Exact execution details are in [`RUN.md`](RUN.md); frozen source hashes and runtime configuration are in [`FREEZE.json`](FREEZE.json).

## H / T / D / C / U

- **H:** A finite gate can separate the planted joint RSS/latency aging signature from cache-only and thermal-only controls; retain coherent per-job measurement times; defer restart across unresolved obligations; and enforce old-generation rejection exactly when a generation transition occurred.
- **T:** Five deterministic synthetic traces × three lifecycle policies × 40 jobs. One construction suite, one candidate, and one separate raw-only audit ran sequentially in a single cached digest-pinned WSLc Python container with no network. The package source was read-only and candidate output used a distinct writable mount.
- **D:** `PASS_METHOD_SCOPED` under the declared fixture and criteria: 600/600 records reconstructed; leak 3/3 policies; other aging controls 0 false positives; hidden-state mismatch 1/1 per policy; pending obligations preserved; all committed restarts fenced; no-restart cells accepted without phantom receipt requirements; audit errors 0.
- **C:** Deterministic synthetic worker and stipulated thresholds/schedules. RSS, latency and temperature are authored fixture values; modeled restarts have no OS/process semantics. A WSLc swap/cgroup warning means memory/swap enforcement is not established.
- **U:** No real process aging/leak, real thermal confounding, actual X11 MCP worker measurement, real restart, user effect, safety, latency benefit, or product policy is shown. T0's `HOLD_RESTART_PATH_NOT_QUALIFIED` remains: no generation-fenced, obligation-aware, effect-safe restart path for the actual persistent-X11 owner has been qualified.

## Relation to T1b and next gate

T1b's mixed-timepoint measurement and incorrectly unconditional receipt gate remain as originally reported in Issue #6133; its raw outcome is not rewritten or re-audited here. T1c changes only the measurement/lineage method in a new frozen synthetic package and uses WSLc instead of the unavailable shared Docker/OrbStack slot reported for T1b. A later empirical aging cohort is still held until an authorized, owned resident process, long-run observable workload, independent correctness oracle, complete resource telemetry, and safe quiescent lifecycle are established. This method PASS does not authorize or justify restarting the actual runtime.
