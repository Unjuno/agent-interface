# WSLc owned-target private Xvfb regression A01

One predeclared exploratory WSLc 3.0.3.0 run on PR #9814 head ddf341723f37134e06bcc5104c4aaaa7cc027417. Network disabled, source read-only, no image pull. Three real private-Xvfb tests passed: identity binding and exact child retirement, explicit retirement during server stop, and MCP shutdown of a bound child. An exact-ID query found no matching container afterward. Logs, conditions, result, ID, cleanup and hashes are retained.

This exercises disposable test processes and does not include ViZDoom, display-generation fencing, MAP01 completion, general reliability or performance comparison. The loaded WSLc image ID differs from its Docker source, as documented in merged PR #9817.
