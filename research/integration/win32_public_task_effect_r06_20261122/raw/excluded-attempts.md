R06 local harness setup exclusions:
- First two invocations pointed to a parent output directory and failed before MCP initialization because `raw/window.json` was not found. No input was sent.
- Third invocation selected the wrong repository cwd and failed to import `runtime`; no input was sent.
- Corrected invocation used the repository root and experiment directory absolute paths; it completed exactly one dispatch.
- Initial regression invocation used dotted module names for standalone tests and errored before running tests. Corrected invocation ran from the test directory with repository `PYTHONPATH`; 67 tests passed normally and under `-O`.
