# Issue #8661 T0 A01 — reset-qualified residual learning

**Formal disposition: `HOLD_CANDIDATE_SELF_CERTIFIES_TERMINAL`.** The frozen candidate and independent auditor each ran once; the original auditor result `PASS_METHOD_SCOPED` is preserved. Across 24 held-out seeds, the retained output shows median pre-correction absolute checkpoint error of 0.6495 (fixed control) versus 0.0100 (learning), and median corrections of 1 versus 0. Post-result review found the candidate calculates `terminal_verified` itself and uses it to authorize updates; no separate independent verifier receipt enters the update path. Thus the Issue's independent-validity gate is not established. See [`POST_RESULT_ADJUDICATION.md`](POST_RESULT_ADJUDICATION.md). No candidate rerun occurred.

## H/T/D/C/U

- **H:** A low-dimensional signed-residual update can reduce repeated correction work when episodes share a verified reset and target generation; mismatch, stale data, unsafe updates, or unverified completion must discard the update.
- **T:** A deterministic one-dimensional plant with 8 training seeds (100–107) and 24 disjoint held-out seeds (200–223), fixed noise values, target 1.0, bias 0.35, gain 0.7, tolerance 0.05, actuator range [-1,1], trust radius 0.25, safe-action ceiling 0.9, reset R0, and target generation G0. Compare fixed control with ordinary within-trial correction to projected residual learning. The independent auditor recomputes each update, checkpoint, correction and terminal result from raw fixture data.
- **D:** The original auditor confirmed update arithmetic, held-out metrics, boundary gates, and mutation controls. Formal PASS additionally requires updates to consume independent terminal/effect validation. The candidate self-computes that flag, so final disposition is `HOLD_CANDIDATE_SELF_CERTIFIES_TERMINAL`.
- **C:** A fixed policy plus within-trial feedback remains suitable if correction is already cheap. Reset variability, target changes, noise, or a nonrepeatable environment can overwhelm learned residuals; in those cases baseline control is preferable.
- **U:** Noise, plant bias and reset identities are authored and deterministic. This establishes no real GUI smoothness, reset fidelity, convergence guarantee, task success, runtime safety, latency benefit, or product value.

## Observed details

After eight valid training episodes, the retained parameter was 0.649438835. On the 24 held-out episodes, the independent auditor calculated median absolute pre-correction errors of 0.0100 for learning and 0.6495 for fixed control, and median correction counts of 0 and 1, respectively. Both arms had zero forbidden effects, unsafe prefixes, stale-target actions, failed releases, and unverified terminal outcomes.

All nine boundary probes matched the frozen gates: reset mismatch, target-generation change, missing/stale residual, unverified terminal, failed release and observed forbidden effect were rejected; a projected saturation/trust-region case was limited to 0.85; an unsafe update rolled back to 0.7. The auditor rejected all five declared mutations.

## Provenance and limits

- Frozen main: `decfe816f5e3b1de34790be9d7b00a1595be86b0`.
- Freeze package commit, recorded before execution: `8b76371ff4`.
- Runtime: CPython 3.14.5 on macOS 27.0 ARM64, checked before the run; standard library only.
- Candidate and audit commands, exit codes, invocation counts and hashes are in [`FREEZE.json`](FREEZE.json), [`RUN_RECORD.json`](RUN_RECORD.json), and [`SHA256SUMS.txt`](SHA256SUMS.txt).
- Raw candidate output: [`raw/candidate.json`](raw/candidate.json). Independent result: [`audit/audit.json`](audit/audit.json).

The test did not invoke a GUI, model, network, game, OS input, or application runtime. T1 remains conditional on a disposable fixture and a separately authorized allocation; this T0 result grants no such authority.
