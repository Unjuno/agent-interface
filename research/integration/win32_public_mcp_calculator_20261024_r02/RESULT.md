# R02 result — physical screen observation

The public `supervised-win32` MCP route returned a fresh `screen_physical_px` observation for the visible Windows Calculator. The saved 336×541 image shows Calculator in Standard mode with the display at 0. Its window ID and target generation matched the frozen target. This distinguishes R02 from R01, whose `window_client` PrintWindow image was uniformly black.

The runner then waited on its terminal stdin for the explicit dispatch decision. The tool call that launched it did not preserve a reachable process session, so the run was stopped before validation and before any input. The runner and its exact MCP server processes were terminated. The observation and full receipts are retained; no input was dispatched, no runtime close receipt was obtained, and task success remains unclaimed.

**Disposition:** observation path passes for this target and frame; input, release, task effect, recovery, MAP01, and efficiency remain untested. R02 is an orchestration failure after successful observation, not an integrated task success.
