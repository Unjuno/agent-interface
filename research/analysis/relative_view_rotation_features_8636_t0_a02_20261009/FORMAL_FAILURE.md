# Issue #8636 T0 A02 — first formal audit failure

**Disposition: `HOLD_UNCERTAIN`.** Preserve this first outcome. Do not rerun or upgrade this allocation.

- Freeze commit: `7d92333b35e4acb09d941928413db7a50581cd2a`; current-main base: `ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385`.
- Candidate: exactly one invocation, exit 0; stdout reports 360 trials and candidate invocation 1.
- Independent auditor: exactly one invocation, exit 1. It raised `ValueError: status does not match independent decision` at `auditor.py` line 280 before writing an audit summary.
- The traceback does not identify the trial or row that first mismatched. Do not infer the cause or any scientific outcome from it.
- Exact 2,216-file candidate output is retained in `results/a02-first-outcome.tar.gz`. Its SHA-256 is `a9004e4e84dadcdd6595dd738bec77e69de84e5b51767985129f968649ddeeb9`. The archive was extracted to a temporary directory and every path/content SHA-256 matched the original expanded output before the expanded copy was removed.
- Candidate and auditor stdout, start/end timestamps, exit codes, source freeze, protocol, and construction suite are retained. Formal retries: 0.

This is a result-custody and audit-stop record only. The A02 method gate did not complete; no hypothesis disposition, feature comparison, focal-shift conclusion, or runtime/product claim is made. A01 remains independently preserved as `HOLD_UNCERTAIN`.

## Additional post-run qualification

`FREEZE.json` records Python 3.12.13 from the construction-test `python` executable, but the formal `python3` commands ran Python 3.14.5. The protocol did not pin the resolved interpreter, so the formal environment differs from frozen metadata. See `POSTRUN_REVIEW.md`; this is an additional HOLD reason, not grounds to alter or repeat the first outcome.
