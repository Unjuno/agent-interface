# Issue #5776 — matched perturbation / margin contrast T0

Fresh synthetic allocation `recovery-sentinel-5776-contrast-t0-20261001-01`. This package tests whether the recovery-duration ratio adds held-out early warning beyond a pointwise operating-envelope margin. It does not reuse, repair, or pool Issue #5776 v1/v2 rows; the prior merged v2 audit bundle has a separately retained fixture/source hash-integrity failure.

## H / T / D / C / U

- **H:** Under a deterministic queue-event fixture with repeated fixed-size probes, the final/first recovery-duration ratio achieves at least 0.75 held-out sensitivity on gradual-recovery future-loss episodes, improves sensitivity by at least 0.25 over pointwise margin at the frozen threshold, and has ≤0.10 false alarms on all held-out no-loss episodes.
- **T:** Full prospective finite population: three load strata × seven mechanisms × 32 episodes, each with 100 integer-tick event rows. Four probe opportunities are fixed in `fixture.json`; episodes 0–15 form a reference partition and 16–31 the held-out partition. No parameter or threshold is fitted from either partition. The complete source, fixture, raw event ledger and independent replay auditor are hash-bound. Formal candidate and auditor each run once in separate network-disabled containers using one pinned Python image.
- **D:** The raw-only auditor must reconstruct every queue transition, probe, service event, return interval, margin, warning and future-loss label with zero mismatch. Only then can `PASS_METHOD_SCOPED` be reported if all three numerical H gates pass. A complete replay failing any gate is `FAIL_METHOD_SCOPED`; any source, fixture, raw or replay mismatch is `FAIL_INTEGRITY`. Censored/unknown returns are retained and excluded from scored denominators.
- **C:** Demand drift can mimic slowing; a direct margin can be sufficient; abrupt/spontaneous loss may not have a gradual precursor. The fixture intentionally contains all of these negative/competing mechanisms.
- **U:** Deterministic analyst-authored mechanisms and prevalence, not a sampled deployment population. Episode rates are fixture counts only. No Agent Interface measurements, calibrated predictive utility, live causal claim, safety guarantee, or product claim.

## Provenance / execution

See `PREREG.md` and `FREEZE.json` for the pre-execution gates, exact source identities, pinned platform image and commands. `test_audit.py` is construction-only and does not consume the formal allocation. Formal invocation receipts, raw output, independent audit output and final disposition are appended only after an authorized isolated OrbStack slot and a one-shot execution. A resource or integrity STOP remains distinct from scientific failure.
