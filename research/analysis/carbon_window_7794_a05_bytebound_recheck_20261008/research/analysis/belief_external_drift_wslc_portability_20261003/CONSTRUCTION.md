# Construction and preregistration checks

This record is frozen before invoking either WSLc workload container. The WSLc candidate and auditor have not yet been run at the time of this record.

## Wrapper construction

- `run_wslc.py` verifies fixed SHA-256 values for every staged parent source file, copies those files into a disposable container-local temporary directory, invokes the parent runner/auditor once, preserves child stdout/stderr and return code, and copies produced artifacts to an exclusive output mount without overwriting existing files.
- Candidate and audit modes each require a new empty output mount. The audit mode copies the three retained candidate JSONL files from a read-only input mount before running the unchanged independent auditor.
- The wrapper neither installs packages nor accesses the network; it uses only Python standard-library modules.

## Host construction tests

Command, from this directory:

```text
python -B -m unittest -v test_wslc_wrapper.py
```

Observed before formal WSLc execution: 4 tests passed in 0.034 seconds. Tests cover source-hash agreement with the merged parent package, modified-source rejection, byte-preserving exclusive copy, and refusal to overwrite an existing result. These are wrapper construction tests, not candidate scientific evidence.

## Stop rules

The first candidate and auditor container invocation are each single-shot. A non-zero return, wrapper exception, missing artifact, source hash mismatch, or later byte/audit mismatch is retained as observed; there is no retry or replacement allocation. The auditor is invoked only if the candidate container exits zero and all three outputs were retained. A preregistration/gate failure before starting the candidate is reported as STOP and does not count as an experimental result.
