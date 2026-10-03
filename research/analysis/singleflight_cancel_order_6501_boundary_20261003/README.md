# Singleflight cancellation/completion event-order boundary

See [REPORT.md](REPORT.md) for the executed result and limits,
[PREREGISTRATION.md](PREREGISTRATION.md) for H/T/D/C/U and the finite contract,
[FREEZE.json](FREEZE.json) for source hashes, and [run01/RUN.json](run01/RUN.json)
for actual invocations and exits. Parent: [Issue #6501](https://github.com/Unjuno/agent-interface/issues/6501).

The exact retained T0b helper is copied for source identity. The new test uses
new finite inputs and calls only its classification helper. No historical
allocation, scheduler, GUI/controller or main runtime is executed or changed.
The result is scoped analytical construction evidence; explicit ordering resolves
the cancellation/delivery ambiguity in this finite model.

Raw is retained through reversible gzip/base64 with a checked SHA256; recovery
and read-only re-audit commands are in the report. Never rerun `run_once.py`
against the consumed allocation/output directory.
