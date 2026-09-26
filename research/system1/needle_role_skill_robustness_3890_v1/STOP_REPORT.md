# Formal allocation STOP — Issue #4479

The sole preregistered formal orchestration was invoked once on 2026-09-26 against the frozen local Docker image (`sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`). Construction checks had passed 8/8 and the frozen sources matched their SHA-256 manifest. The run stopped at phase `builder-100000`; Docker exited 125 before creating or starting a container because the PowerShell argument list called `docker --rm ...` rather than `docker run --rm ...`.

No model training, data generation, loader execution, or scientific measurement occurred. This is an orchestration STOP, not a model FAIL and not evidence about role-skill robustness. The one-shot allocation is consumed; no retry, tuning, replacement seed, or result exclusion is permitted under the preregistration. `STOP.json` and `seed-100000/builder.stdout.log` preserve the exact captured failure evidence.

Evidence SHA-256:

- `STOP.json`: `fd1cf56829b663d018de2cf28863281792cca3c02b9c6773bba6b2379a521746` (308 bytes)
- `seed-100000/builder.stdout.log`: `12bdcf916ade656d8940d40bc2efc62f8ed0a543cc19916b2585f81ba6176dda` (109 bytes)

The formal launcher defect and the prior Windows-path preflight defect are both retained as construction history. Any future execution requires a new successor issue, a new frozen allocation, and a new one-shot contract; it must not rewrite this STOP.
