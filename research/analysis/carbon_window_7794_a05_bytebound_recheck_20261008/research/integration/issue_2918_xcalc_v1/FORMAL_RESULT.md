# Formal-01 result

## Disposition

`PASS_XCALC_LIVE_CERTIFICATE_TRANSFER_SCOPED`. The preregistered OrbStack allocation completed once (exit 0). The independent, read-only audit passed and the three preregistered auditor corruption controls were rejected; original raw inputs were unchanged.

## Results

- 13 cases; 12 public `runtime.cli_v1.observe` calls; 3 `FORWARD`, 2 `SUPPRESS`, 8 `YIELD`; zero unsafe suppressions.
- The candidate's two suppressions exceeded the global-support control by 2 and phase-support control by 1. The PREPARE E-only transition was suppressed by both candidate and phase-support control; it is not incremental benefit over that baseline.
- The D-only EFFECT_PENDING transition was suppressed while semantic outcome remained COMPLETE. The D+E transition was forwarded and changed semantics to CONTINUE.
- All eight uncertainty controls yielded, including same-XID replacement distinguished using XRes client PID/resource base and caller generation.
- Observed API capture time and capture-to-certificate totals are retained per transition in `formal_01_audit/independent_audit.json`; these fixture timings do not establish end-to-end benefit.
- The wrong-disposition, missing-row, and mutated-capture controls each failed the independent auditor assertion as preregistered; `source_raw_unchanged=true`.

## Scope and limits

This is one private Xvfb/XCalc surface with exact display templates, synthetic XTEST-driven state changes, and frozen #1904 semantics. It demonstrates scoped live observation/certificate transfer and uncertainty refusal in that fixture only. It does not establish external desktop operation, user-task effects, broad GUI compatibility, model behavior, product readiness, or a general efficiency claim. XTEST drove only the isolated fixture; observe reported no dispatched input or side-effect authority.

## Provenance

Pre-registration and source freeze are in `PREREGISTRATION.md` and `SOURCE_FREEZE.json`. Raw runner output is in `formal_01_raw/`; the separate auditor report is in `formal_01_audit/`; mutation controls are in `formal_01_corruption_controls/`. Construction rehearsals and earlier STOP/HOLD artifacts are retained unchanged in `construction/` and are not formal evidence.
