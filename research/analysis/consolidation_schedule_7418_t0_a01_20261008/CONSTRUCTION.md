# Pre-freeze construction record

The first eight-test construction run passed seven cases and failed the valid-schedule case: mutation tests modified the shared in-memory model through an aliased candidate input. A separate read-only diagnostic confirmed the expected schedule output. The candidate now copies the input episode ledger before constructing output, and tests pass a fresh model copy to each check.

The final construction test run passed 8/8, including valid four-arm output and rejection of missing exception retention, dropped provenance, silently resolved conflict, changed episode, misaligned checkpoint, held-out conjunction inference, and altered query budget. `py_compile` and `git diff --check` also passed. No candidate CLI or auditor CLI was invoked during construction; formal counts before freeze are 0/0 and retries 0.
