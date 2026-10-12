# A01 STOP and A02 construction correction

A01's recorded attempt failed before the Python candidate process started: the shell could not open stdout/stderr and start-receipt paths under `results/`, which did not exist. Candidate process count and auditor process count were both zero; A01 is not rerun.

A02's wrappers resolve their own package directory, create `results/` before opening any redirected files, write a start receipt, and refuse a second invocation. The auditor wrapper requires candidate exit 0 and an existing raw file. Construction tests exercise both wrappers in disposable temporary directories with stub role programs and verify fresh-directory startup, captured output, exit receipts, and retry refusal. Those stub checks do not consume the A02 formal allocation.

During the A02 audit review, a second construction-only gap was found in A01's checker: it verified the complete expected ID set and balanced payload factors separately but did not verify that each ID encoded the same factors and endpoint as that row's payload. A02 now reconstructs the identity string from every row and binds the top-level allocation to the frozen spec. A new mutation changes a factor but preserves the old identity; the auditor must reject it. This correction was made before A02 freeze and formal execution. A01's checker and result remain untouched.
