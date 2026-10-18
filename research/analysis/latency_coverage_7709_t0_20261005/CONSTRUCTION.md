# Construction-only checks

Before the freeze, WSL CPython 3.12.3 parsed all three Python sources with `ast.parse`. An in-memory 16-session / 24-window fixture with a planted boundary at 12 detected exactly `[12]`; no-boundary and deliberately extra-boundary weighted integrated estimates/intervals agreed within `1e-9`.

These checks did not call `generate.py`, create held-out rows, run the candidate CLI, or run the auditor CLI. Formal held-out invocation counts at freeze: generator 0, candidate 0, auditor 0; retries 0.
