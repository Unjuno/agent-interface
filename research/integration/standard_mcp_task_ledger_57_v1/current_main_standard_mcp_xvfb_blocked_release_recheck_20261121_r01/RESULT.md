# Standard-caller Xvfb trial R01

Status: `HOLD_RUNNER_METADATA_DEVIATION`; retained as exploratory raw evidence.

The standard MCP cancellation test ran in the isolated Docker Xvfb container and exited 0. The test runner exported the Xvfb PID under the wrong variable name (`AGENT_INTERFACE_MCP_XVFB_PID`); the test expected `AGENT_INTERFACE_XVFB_PID`, so the report's Xvfb provenance is `unavailable` and this attempt cannot qualify a clean reproduction.

The raw result still records a separate-parent release readback with A/B up, an old-task effect count increase from 1 to 4, and an independent old-task oracle failure. A fresh-session task oracle passed while the original generation remained UNKNOWN and replay was denied. Preserve these observations without upgrading them to a passing product result.
