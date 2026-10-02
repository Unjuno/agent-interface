# Issue #6061 T0 result — prediction-error-triggered motor chunks

**Disposition: `PASS_METHOD_SCOPED`; finite-fixture directional pattern favors the predictive arm over fixed-period observation.** The container request was not met: this was executed on host CPython 3.12.10 after Docker Desktop's Windows service was observed stopped and `docker version` produced no server response. No Docker service start or container launch was attempted because #5085 records unresolved shared-container ownership. See the tool-launch attempt and exact invocation ledger in `RUN.json`.

## H / T / D / C / U

- **H:** On this declared nine-case finite family, prediction-error-triggered chunks preserve or improve the independent task-effect endpoint and invalidation safety versus fixed-period control while reducing full captures. The comparator against a bounded nonpredictive hold tests whether the trigger contributes beyond chunking.
- **T:** Four arms, 40 ticks each, identical initial position, action authority, 8-tick maximum chunk and 40-tick total occupancy ceiling. Fixed observation period is 4 ticks; predictive threshold is 2 coordinate units with an 8-tick maximum; inexpensive tracker probes are supplied each tick. The nine frozen scenarios are steady drift, abrupt reversal, disappearance, misleading animation, semantic identity switch with continuous kinematics, focus loss, lease expiry, a perfect-tracker positive control and stale-tracker negative control. Candidate saw `input_fixture.json` only; `truth_oracle.json` was read only by the independent auditor.
- **D:** Candidate emitted 36 case×policy rows once. The separately authored raw-only auditor independently reconstructed 36/36 action traces, counts and positions with zero errors. All arms issued zero nonzero commands at/after every frozen identity, focus, lease or target-disappearance invalidation. The perfect-tracker control reduced predictive captures (6 vs fixed 10); stale tracking raised predictive captures to 23. The method gate passed. No live efficacy gate was attempted.
- **C:** Windows host, CPython 3.12.10, standard library, deterministic one-dimensional 40-tick plant. The cheap probe and event channels are idealized, the clock is discrete, and capture count is a cost proxy rather than measured wall time or CPU work. Host networking was not disabled at the OS layer; the scripts made no network calls.
- **U:** This says nothing about a real visual predictor, actual held-key duration, OS release latency, safety under scheduler delay, a real task-effect scorer, human tempo, cross-domain value or MAP01 completion. No historical #59 result is reclassified.

## Results

| Policy | Useful-effect cases | Full captures | Commanded occupancy ticks | Invalid-continuation ticks |
|---|---:|---:|---:|---:|
| Fixed period | 5/9 | 71 | 284 | 0 |
| Prediction-triggered | 6/9 | 62 | 284 | 0 |
| Bounded hold | 5/9 | 37 | 284 | 0 |
| No continuation | 2/9 | 9 | 9 | 0 |

The predictive arm used 9 fewer full captures than fixed-period control (12.7%) and reached the scorer's proximity endpoint in one additional case. The most diagnostic contrast was `misleading_animation`: predictive control reached the hidden target endpoint while bounded hold and fixed-period control did not. The fixture deliberately provides a per-tick cheap probe, so this is a trigger-versus-period comparison under that sensor assumption—not a claim that a GUI can supply the probe cheaply.

The predictive arm did **not** dominate the bounded-hold arm on cost: it used 62 rather than 37 full captures for one additional useful-effect case. With a stale tracker its capture count rose to 23 for the same effect as the fixed arm (10) and bounded hold (5). Thus prediction quality is a first-order condition, not a safe default. Identity/focus/lease/disappearance checks were modeled as a separate immediate current-state gate; those gates, not low kinematic error, caused release on the semantic identity-switch control.

`cpu_proxy = 10 × full captures + 40 probe ticks` is a declared deterministic accounting proxy only. No actual CPU time, wall-clock latency, or physical key occupancy was measured. “Occupancy ticks” above are commanded nonzero ticks in the synthetic plant.

## Reproducibility and retained evidence

- Freeze: `FREEZE.json`; source/fixture commit: `5f86ac10b061acfdfeaf1a5ba5deff9f1c21dd01`; frozen bundle commit: `92e213146`.
- Candidate raw: `runs/formal-01/raw.jsonl`, SHA-256 `90F29E6BB888531A155A491E1228ABC5C9F7EB53F916A70E4652AEA19121074E` (232,607 bytes).
- Independent raw-only audit: `runs/formal-01/audit.json`, SHA-256 `606DD171B4822DB32D6C92BB3F2369B435EBB88C5CD431AD8A6D1D37A61BC1BE` (20,687 bytes); `PASS_METHOD_SCOPED`, 36 rows, errors empty.
- Pre-freeze construction tests: `python -B -m unittest -v test_t0.py` — 5/5 passed. These did not read formal raw output.
- Candidate and auditor each ran exactly once; retries 0. A preceding outer process-launch attempt was rejected before candidate startup due to an invalid working directory; it produced no scientific rows and is disclosed in `RUN.json`.

The outcome supports only an idealized T0 mechanism/cost pattern. Issue #6061's T1 eligibility audit and separately authorized live dynamic task remain open; no T1 allocation or runtime change follows from this result.
