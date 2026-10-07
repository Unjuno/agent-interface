# Issue #7709 T0 pre-generation freeze

- Frozen repository `main`: `c837ad535eed085d95744ad0a9680535a5bb7143` (observed from GitHub MCP immediately before this freeze).
- Additive branch: `research/7709-t0-segment-coverage-20261005`, based on that main; remote research path: `research/analysis/latency_coverage_7709_t0_20261005/`.
- Protocol: `README.md`; fixed design: `CONFIG.json`; generator, candidate and independent raw-only audit source identities below.
- Execution: Ubuntu on WSL2, Linux `6.18.40.1-microsoft-standard-WSL2`, CPython `3.12.3`, CPU only. T0 in Issue #7709 explicitly does not require WSLc/Docker; WSL host execution avoids contending with two separately retained, still-live WSLc requests from #7707. No model/GPU/GUI/app/input/network is used.
- Host snapshot before freeze: `/proc/self/cgroup` was `0::/non-systemd`; cgroup v2 `memory.max=max`, `memory.current=4959395840`, `cpu.max=max 100000`, `pids.max=max`; `free -h` reported 5.8 GiB total, 4.2 GiB available, and 2 GiB swap with 15 MiB used. These are host observations, not a memory/CPU limit or enforcement claim.
- Construction-only checks: see `CONSTRUCTION.md`. No held-out data was generated at freeze. Formal invocation counts: generator 0, candidate 0, auditor 0; retries 0.
- Once, after freeze, the generator will write held-out input, then candidate CLI runs once, followed by independent auditor CLI once. A terminal failure is retained without retry.

## Frozen source SHA-256

| File | SHA-256 |
|---|---|
| `README.md` | `c653718f545667d423d22796fdbd83b6d094295535eda860210e3660c8d703a2` |
| `CONFIG.json` | `bd992d69c90032ca5e52800a2d0b8c79ead1bd9965b17acc7729fafc790ded4` |
| `generate.py` | `27be7066a7373ddcbb25797173ad26a010284d1031ea856519e53993775bdd8` |
| `candidate.py` | `084541ab3faef78d02ac659a7394c303e01690259da37e6e175fb06498eba541` |
| `audit.py` | `6184d6547bda5ba5dbaf6f6de30cc22dfeb5f7ac64531c3ecb84d31bdf98af7d` |

`CONSTRUCTION.md` and this freeze receipt are provenance records written after source hashing; they are not executable inputs to the frozen method.
