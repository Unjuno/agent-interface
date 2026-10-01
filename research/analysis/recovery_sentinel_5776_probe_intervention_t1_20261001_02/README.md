# Issue #5776 — does the probe itself move the endpoint?

This successor allocation-02 isolates a concrete limitation explicitly raised in #5776: repeated disturbances can alter the system being measured. Allocation-01 stopped before candidate when `main` advanced at its start gate; it generated no scientific rows. This comparison is paired probe versus no-probe under the same authored latent schedule; its endpoint is queue backlog, not the sentinel warning. Prior Issue #5776 outcomes remain untouched.

## H / T / D / C / U

See `PREREG.md` for the frozen H/T/D/C/U, complete population, independent endpoint, eligibility requirement and decision gates.

## Reproduction

After the formal run, `RUN.json`, raw candidate output, stdout receipts, independent audit and `SHA256SUMS` bind the exact commands, image, environment and results. `runner.py` is the candidate; `audit.py` independently replays raw events without importing the candidate. `test_audit.py` is construction-only and does not consume the formal allocation.

Scope is restricted to this deterministic finite work-queue fixture; no deployment, predictive, live-agent, safety, or product claim follows.

## Pre-formal construction dose check

`CONSTRUCTION_DOSE_CHECK.json` is a reproducible host-only sensitivity check, explicitly not the formal candidate/audit. It replays the same finite fixture at 14 fixed probe magnitudes (1–40 units); the exact script and output hashes are recorded in `FREEZE.json` and `SHA256SUMS`. The target gradual-capacity-loss median advance is 0 ticks at doses 1–12, 32 at 16, and 64 at 40, while probe-created losses rise in the no-loss controls (54/54 at dose 40). This exposes an authored dose/harm tradeoff and means the 40-unit formal arm is interpreted as a high-dose intervention-harm stress test, not evidence of safe/repeated probing. Candidate and independent auditor remain unrun until the exclusive OrbStack start gate.
