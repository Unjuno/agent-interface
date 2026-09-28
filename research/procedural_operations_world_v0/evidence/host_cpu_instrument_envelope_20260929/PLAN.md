# Headless CPU instrument envelope — construction allocation

Issue: #5206  
Allocation: `opsworld-host-cpu-envelope-5206-20260929-01`  
Main freeze: `708dec9bcd2bfb3ef597acf7bc1c8a02bcb96b01`  
Branch: `research/opsworld-instrument-overhead-5206-20260929`

## H / T / D / C / U

**H.** At the documented maximum moving-object/watcher/assembly load, the
headless simulation+software-render loop and episode reset primitive may remain
within a 16.667 ms CPU budget. This is a host envelope check, not controller
latency or benchmark promotion evidence.

**T.** On the frozen main source, build with the repository Makefile and run
`make test`. Then execute each README-documented benchmark exactly once:

```text
./ops_world --seed 42 --family-key 99173 --bench-frames 10000 --set watcher_count=64 --set required_alerts=0 --set event_rate=0 --set object_count=64 --set assembly_pieces=12 --set episode_seconds=3600
./ops_world --seed 42 --family-key 99173 --bench-resets 100000 --set watcher_count=64 --set required_alerts=0 --set event_rate=0 --set object_count=64 --set assembly_pieces=12
```

The two captures go to separate immutable stdout/stderr files under this path.
No warm-up, retry, tuning, or extra seeds. Record source/image/compiler/host
identity, exact commands, wall time, throughput, exit codes, and output hashes.

**D.** `PASS_CPU_INSTRUMENT_ENVELOPE_ONLY` iff the build and 20-case validity
suite pass, both documented commands exit zero and report their exact requested
counts with finite nonnegative timing, and both measured per-frame/per-reset
costs are at most 16.667 ms. A valid timing above that bound is
`HOLD_CPU_INSTRUMENT_COST`; build, command, parse, or provenance failure is
`STOP_CONSTRUCTION_OR_PROVENANCE`. No agent/controller score is produced.

**C.** Same frozen source, compiler flags, host, seed and family key across both
commands. The stress configuration disables alert obligations/event generation
while retaining 64 object slots, 64 watcher slots and 12 assembly pieces. This
isolates a reproducible software workload, not an actual controller session.

**U.** WSL2 Arch Linux on one Windows host; no Docker due the current #5085
explicit no-invocation restriction, no GPU/CUDA/model/provider, GUI/X server,
controller, paired baseline, or external task. The built-in frame timer includes
both `ow_step` and `ow_render`; reset timing includes episode initialization.
These timings cannot isolate rendering, scheduler cost, or end-to-end interface
overhead, and cannot satisfy Issue #5206's formal promotion gates.
