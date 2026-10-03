# Queue-report fault boundary (#5372)

The finite comparison found no need for telemetry-based admission on top of an
atomic authoritative pending cap: `SUBSUMED_BY_AUTHORITATIVE_CAP_SCOPED`.
This is an analytical construction result, not a runtime or task-performance claim.

See [REPORT.md](REPORT.md) for counts, assumptions and the next integration
decision; [PLAN.md](PLAN.md) and [FREEZE.json](FREEZE.json) retain the prospective
decision and source identity. [run_01/RUN.json](run_01/RUN.json) records one
candidate, one separate auditor, zero retries and both actual exit codes.

Raw archive: [run_01/raw.jsonl.gz](run_01/raw.jsonl.gz), losslessly preserving
26,762,476 raw bytes. [ARCHIVE.json](run_01/ARCHIVE.json) binds both byte forms;
[audit.json](run_01/audit.json) contains separate reference counts and three
complete counterexample/throughput traces. No retained predecessor was rerun.

To inspect retained evidence without executing a producer:

```sh
python verify_saved.py
```

To run only hand-derived construction controls:

```sh
PYTHONDONTWRITEBYTECODE=1 python check_construction.py
```

The consumed `run_once.py` path refuses an existing output directory. Do not
delete it to repeat this ID. Any new experiment needs a prospective change in
question/input/conditions, fresh ID and applicable authority. A separately
authorized raw-only audit may decompress the archive to a new path and run
`audit.py` against it without invoking `candidate.py`; that is an additional
audit, not the originally recorded invocation.
