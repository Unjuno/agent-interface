# Issue #5776 — does the probe itself move the endpoint?

This successor allocation-02 isolates a concrete limitation explicitly raised in #5776: repeated disturbances can alter the system being measured. Allocation-01 stopped before candidate when `main` advanced at its start gate; it generated no scientific rows. This comparison is paired probe versus no-probe under the same authored latent schedule; its endpoint is queue backlog, not the sentinel warning. Prior Issue #5776 outcomes remain untouched.

## H / T / D / C / U

See `PREREG.md` for the frozen H/T/D/C/U, complete population, independent endpoint, eligibility requirement and decision gates.

## Reproduction

After the formal run, `RUN.json`, raw candidate output, stdout receipts, independent audit and `SHA256SUMS` bind the exact commands, image, environment and results. `runner.py` is the candidate; `audit.py` independently replays raw events without importing the candidate. `test_audit.py` is construction-only and does not consume the formal allocation.

Scope is restricted to this deterministic finite work-queue fixture; no deployment, predictive, live-agent, safety, or product claim follows.

## Pre-formal construction dose check

The first saved `CONSTRUCTION_DOSE_CHECK.json` was independently found invalid: the construction script changed the in-memory dose, but `runner.build()` read the canonical fixture through a module-global path, so all fourteen rows replayed 40 units. The invalid output is preserved as `CONSTRUCTION_DOSE_CHECK_INVALID.json` and not used as evidence. After binding the intended fixture for each build, an independent event reconstruction passed all 14 rows: median target advance is 0 ticks at 1–8 units, 0 with 6/54 control-created losses at 12, 32 with 19/54 at 16, 48 with 36/54 at 20, 60 with 49/54 at 24, and 64 with 54/54 at 28–40. This exposes severe intervention harm: 40 units is only an authored high-dose stress test and cannot support safe/repeated-probing claims. This is host-only, non-formal construction evidence; candidate and formal auditor remain unrun.
