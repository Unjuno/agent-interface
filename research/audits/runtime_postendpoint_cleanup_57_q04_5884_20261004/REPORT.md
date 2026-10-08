# Q04 ordinary startup failure-path construction

Published PR7196 client SHA f73556d3fafdc3125caac396b20d648cd5bb83e64e0f37834e3f06e58750f938 accepts a real inert child endpoint, then a deliberately failed initial-observation transport raises ConnectionError. Immediately after start raises, direct child47136 remains alive, stdout/stderr open and temporary directory present. Explicit existing close subsequently terminates/reaps child (-15) and removes temp. This proves a scoped handling gap, not a native GUI failure or descendants leak.

Private candidate moves initial request/ready extraction/journal initialization into existing startup cleanup guard. Same ordinary construction with child47545 retains the primary ConnectionError and observes child reaped, both streams closed and temp removed before start returns its error. These are RED/GREEN failure-path observations, not full regression/integration qualification. Constructor/Popen/temp acquisition and descendant handling remain unqualified. No task/model/input or VM execution; consumed Q02/Q03 were not replayed.

PR7196 fixed head unchanged; current MCP state open draft, mergeable false, no reviews or additional comments in fetched100-row pages. Current origin/main b76c365140 (full SHA in repository) has no diff on the three candidate paths relative to original publication base; the overall conflict cause remains uninvestigated. No main writes or approval votes. Next: meaningful regression cases for each post-endpoint stage and conflict analysis before publishing a new fixed proposal. Archive includes source/probes/results; candidate hash corrected explicitly after run without rerunning it.

## Follow-up regression qualification

Three full-module real-inert-child failure cases (request, ready extraction, journal initialization) fail the published baseline and pass the private candidate in normal and -O execution. Existing nine endpoint/cleanup regression methods also pass in both modes. Total12 distinct methods; no native GUI/model/input. Each fixture explicitly closes its own child in finally. Source and stdout/stderr retained.

Git merge-tree --write-tree on fetched main b76c365140a1f0ac9a1f859a4204d3de96b0e113 and exact PR7196 head exits0, producing tree488365ec17db3a6218aed6a354d3edb20442cb75. This contradicts the earlier GitHub mergeable=false display at base55d570; it is a local combination observation, not current-main nonauthor approval or a merge permission. No remote source mutation. Next: qualify candidate on dedicated Linux and publish distinct fixed content proposal if required; preserve Q01 votes/history.

## Dedicated Linux qualification

Ordinary construction (not a consumed native experiment) ran once on Debian12 ARM64 Python3.11.2 in own VM01M40Y31JTWPEWW8G408FRMRZN. Source bundle hashes verified before unit execution. Existing9 plus new3 methods passed normally and with -O. Host unit PID49568 ran19:19:24.740277–19:19:32.306232UTC, exit0. Effective cpu.max25000 100000, memory.max134217728, pids.max32 sampled inside unit. Configured runtime40s, control-group kill; no timeout fault exercised. Full four unittest stderr streams and resource sample preserved. VM stopped and read back19:19:32.503725UTC. GUI/model/input0. Constructor/temp-allocation and descendant handling remain outside qualification. Candidate private; no remote head/main change.
