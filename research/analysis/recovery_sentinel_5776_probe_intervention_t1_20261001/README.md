# Issue #5776 — does the probe itself move the endpoint?

This successor allocation isolates a concrete limitation explicitly raised in #5776: repeated disturbances can alter the system being measured. The comparison is paired probe versus no-probe under the same authored latent schedule; its endpoint is queue backlog, not the sentinel warning. Prior Issue #5776 outcomes remain untouched.

## H / T / D / C / U

See `PREREG.md` for the frozen H/T/D/C/U, complete population, independent endpoint, eligibility requirement and decision gates.

## Reproduction

After the formal run, `RUN.json`, raw candidate output, stdout receipts, independent audit and `SHA256SUMS` bind the exact commands, image, environment and results. `runner.py` is the candidate; `audit.py` independently replays raw events without importing the candidate. `test_audit.py` is construction-only and does not consume the formal allocation.

Scope is restricted to this deterministic finite work-queue fixture; no deployment, predictive, live-agent, safety, or product claim follows.
