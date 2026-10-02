# T0-01 formal STOP — Issue #6501

**Disposition: `STOP_OUTPUT_SERIALIZATION`; scientific result: `NOT_EVALUATED`.** Candidate invocation 1/1; independent auditor invocation 1/1; retries 0. No method PASS or FAIL is inferred.

The candidate generated ten case rows and exited 0, but the wrapper appended literal `\n` characters after the closing JSON brace. The independent auditor then exited 1 with `JSONDecodeError: Extra data` at line 461, column 2, byte 10352. No `audit-raw.json` was produced. The saved artifact and all process receipts are preserved in `run01/`; see `STOP.json` for byte sizes, hashes, exit codes, runtimes, and resource warning.

The source/fixtures remain unchanged. The defect is in the command wrapper's newline escaping, not yet a scientific candidate failure. Per the frozen one-shot boundary, no output repair, candidate retry, auditor retry, or replacement invocation is allowed in T0-01. Any further attempt uses an additive successor allocation with a fresh freeze and different output path; T0-01 stays terminal and immutable.

The container was the cached digest-pinned CPython 3.12.14 image, network disabled, source mounted read-only, CPU request 0.25. WSLc warned swap/cgroup memory limits are unsupported; no memory-cap claim is made. The separate native integration workers were left untouched. No Docker migration or runtime behavior was evaluated.
