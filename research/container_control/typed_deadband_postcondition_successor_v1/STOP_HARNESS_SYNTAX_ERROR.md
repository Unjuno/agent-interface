# Typed deadband successor v1 — construction STOP report

Status: STOP_HARNESS_SYNTAX_ERROR

## Runs

- Run 35442587962: dependency setup passed; runner stopped at line 379 with a literal escaped newline in the generated summary dictionary.
- Run 35442719440: dependency setup passed; runner stopped at line 426 with a literal escaped newline in the generated argparse declaration.

## Scientific disposition

No experiment began in either run. No Tk/X11 window was controlled, no decision was completed, no input event was emitted, and no scorer/raw result artifact exists. These are construction failures, not scientific FAIL or PASS results.

The runs are retained in PR comments and must not be overwritten or interpreted as evidence. The runner has since been corrected in commit `a7167c72982b45090fa36f9fbb13e16cd5af44bc`. A subsequent workflow trigger is pending; its first valid result must use a fresh run identity and remain subject to the preregistered no-retry rule.

## Required next gate

Before any scientific interpretation:
- Actions must reach the runner without SyntaxError;
- the runner must produce raw controller, input, scorer, summary, and manifest files;
- the required deadband-entry and stale-guard exposures must occur;
- independent audit must agree with the raw manifest.

No historical evidence or preregistration was changed.