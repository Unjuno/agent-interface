# T8 run record

Docker Desktop engine remained unavailable; T8 used private WSL2 Xvfb. The source-bound Tk app reached focus-ready. The separate observer failed to emit readiness within five seconds; runner stopped before X RECORD setup or XTest input. Raw STOP: `run/run.raw.json` and `run/driver.jsonl`; Shift was never dispatched, so no cleanup release was required.

The auditor was invoked once but STOPped with `AttributeError` because it dereferenced the absent observer-ready payload rather than adjudicating a pre-input STOP. This is preserved as an audit-construction STOP, not silently retried. Candidate invocation and auditor invocation each spent once; T9 is a new path/hypothesis.
