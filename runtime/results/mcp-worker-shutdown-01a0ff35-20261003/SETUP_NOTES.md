# Ordinary setup diagnostics

The first shell-only dependency query had a PowerShell quoting SyntaxError before any test. A corrected import query found that the global CPython3.11.9 environment had no MCP SDK. These tool outputs are not formal experiment outcomes.

The new worktree was created with --no-checkout. sparse-checkout set alone did not populate its initial index: two file reads failed and the unstaged index observation showed all original paths absent. Only this newly created owned index was initialized with read-tree -mu HEAD. No branch reset, existing worktree source or other worker was touched.

The first affected103-method regression retained102 passes and one missing runtime.distribution_v2 setup error. Necessary distribution_v2/host_v1 source was added. Its support contract declares Python>=3.12 and MCP1.30.0; subsequent decisive checks used bundled native CPython3.12.14 in a separate owned venv with the actual pinned SDK. The earlier3.11.9/MCP1.29.0 checks remain historical compatibility/diagnosis only.

All first ordinary failures remain. No old5539/5542/thread/asyncio/pipe producer or formal allocation was invoked. PATH queries and bundled-runtime discovery did not start WSLc, Docker, GUI or a model.
