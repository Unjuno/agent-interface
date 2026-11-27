# Docker stability validator smoke on current main — R02

## Scope

One network-disabled Docker run of the synthetic Issue #57 reuse-horizon/lifecycle validator against exact current-main commit `c0ebed2bd78fbe09284beb879acc341ef8c48dbe`. Source was bind-mounted read-only. Container bounds were 2 CPUs, 4 GiB memory and swap, and 256 PIDs. No provider call or GUI input occurred.

## Result

The 17 tests passed in normal Python and under `python -O` (exit 0 in both modes). Docker returned exit 0 and auto-removed the container. A post-run Docker info query succeeded; the engine remained at 8 CPUs, 33,658,945,536 bytes reported memory, version 29.8.1, with no containers left running.

The active `.wslconfig` recorded for this run is 32 GiB memory, 8 processors, 8 GiB swap, and gradual memory reclaim. Docker's server reported 31.36 GiB. This is a single brief resource-bounded smoke. It supports that this one workload completed under the recorded limits and that the engine answered immediately after; it does not demonstrate long-term Docker stability, crash prevention, WSLc, agent real-time performance, live computer control, or reliability.

## Reproduction and custody

`command.txt` records the invocation. `run.sh` runs the same 17-test module twice. `conditions.json`, `runtime-after.json`, and `source-files.json` capture the environment and source. `normal.log`, `optimized.log`, `combined.txt`, and `exit-status.json` retain raw output/status. `SHA256SUMS.txt` hashes each packet file other than itself.