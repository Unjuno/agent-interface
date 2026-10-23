# R30 preparation and custody

R30 is a new attempt after merged R29, based on current main. Its preflight validates the exact R29 raw/audit hashes and semantic boundary, current runtime and packet hashes, read-only registry absence, source commit, native Windows, and a SHA-256 of `conditions.json`. The trace wrapper is test-only; a child-process fake-Process self-test exercised `is_alive`, `terminate`, `join`, and `kill` without GUI or native input.

Four input-free preflight executions are preserved: two stopped because the instrumentation import environment was incomplete, a third verified wrapper installation, and the fourth also exercised every wrapper method on a fake process and passed. No fixture or MCP session existed before the formal run.

The one-shot trial used one fixture, one public dispatch, one cancel, and only exact-call result polling. The wrapper records process-method start/return timestamps in a private JSONL file. It does not change return values or issue input. No WSLc, Docker, registry update, retry, replay, or second cancel occurred.
