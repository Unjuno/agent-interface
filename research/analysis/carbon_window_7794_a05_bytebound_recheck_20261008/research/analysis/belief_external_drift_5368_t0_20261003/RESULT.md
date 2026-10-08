# Result — external-transition prediction T0

**Disposition: `PASS_METHOD_SCOPED`.** This is a finite synthetic result for the declared state/transition oracle only; it is not live GUI or safety evidence.

- Issue: [#5368](https://github.com/Unjuno/agent-interface/issues/5368), specifically its proposed external-disturbance prediction test.
- Allocation: `belief-external-transition-5368-t0-hostcpu-20261003-a01`.
- Frozen main: `3729d6825e67b7276b58d40ef6c125e4a3b441bf`.
- Frozen source commit: `537e673240169a0703aaad273ae7ac37949e8766`.
- Candidate and independent raw-only auditor: each invoked once; both exit 0. The auditor imports neither candidate nor runner.

The auditor independently reconstructed all **9/9** reachable-state sets and decisions with zero errors. The candidate made two admissions, both safe in the declared actual traces; **unsafe admissions: 0**. It yielded when a hidden redirect left both A and unsafe B possible, ignored a stale-generation observation, and returned `UNKNOWN_MODEL` for an unverified event alphabet, a possible out-of-support state, and a current observation contradicting the model's completeness claim. The two-step case expanded to `{A,B,C}` and yielded. A complete no-disturbance control and a fresh source-bound observation narrowing to safe A were admitted.

On the same fixture, the sticky last-observation baseline admitted all nine cases, including **7 false admissions**; the age-only timeout yielded on all nine and refused the **2 safe controls**. All **4/4** predeclared corrupted-output controls were detected by the same independent row verifier used on formal output.

The candidate emits only decisions; no authority, input, or effect was emitted. Construction checks passed 6/6 twice before the formal run. The frozen source and all outputs are hashed in `SHA256SUMS` and detailed in `RUN.json`.

## H / T / D / C / U interpretation

- **H:** Supported within the finite fixture: reachability prediction plus current-generation evidence avoided the planted false admissions while retaining both safe controls.
- **T:** The nine preregistered deterministic traces, the two baselines, and the independent auditor ran as frozen.
- **D:** All scoped gates passed: complete row reconstruction, zero unsafe admissions, safe-control retention, fail-closed unknown/model-conflict cases, sticky-baseline counterexample, age-baseline false refusal, and four mutation detections.
- **C:** Fresh generation invalidation may be simpler than maintaining a reachable set. A trusted current observation can collapse the set. Completeness of a real transition alphabet may be difficult to establish.
- **U:** Synthetic only; no measured event rates, source trust, GUI semantics, real external actors, model behavior, action effects, latency, or operational safety.

## Execution scope and limitations

This run used Windows host CPU and Python 3.12.10, not WSLc. Current #5085 coordination and the latest related PR #6775 retain a WSLc attribution/allocation hold; an empty container list is not authorization. WSLc 3.0.1.0 and the cached Python 3.12 slim image were inspected, not run. Windows showed 1.49 GB free physical memory during preflight, so this stayed a tiny finite local calculation. No WSLc cgroup/swap enforcement claim applies.

The runner and auditor use only local file I/O and standard-library computation. Network access was not disabled at the OS level; GitHub was used to fetch the source before the frozen run. No network request was made by the candidate or auditor. This distinction is recorded rather than implying a network-isolated container.
