# Issue #8084 A04 — diagnostic reliability under sampling noise

**Outcome:** `HOLD_METHOD_GATE`. Fresh synthetic allocation after A03's `STOP_AUDIT_INPUT_HANDOFF_PATH_ERROR`; A04 used a distinct deterministic seed family and no A03 output. Candidate and independent auditor both ran (one each), and base reconstruction had zero errors across 6,000 rows. However, the auditor's duplicate-row mutation survived, so frozen acceptance criteria failed. The retained summary descriptively shows low-dispersion false activation 169/500 at n=20, but that is provisional, not an accepted result. See [RESULT.md](RESULT.md).

Frozen H/T/D/C/U and once-only WSLc execution rules are in [PROTOCOL.md](PROTOCOL.md). Candidate-visible input was restricted to observed counts; latent probabilities were mounted only for the independent audit.

The pre-formal PowerShell stdout-redirection setup miss is retained in [PRE-FLIGHT.md](PRE-FLIGHT.md); the generator had not started in that attempt.
