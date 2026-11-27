# Docker/Xvfb MAP01 direct-versus-compiled comparison: R10 + R12 + R14

Six counterbalanced matched pairs (12 live arms) across fresh seeds. All 12 raw arm records passed all six preregistered gates: caller route completed; independent X11 sampling observed W down during dispatch; terminal native release receipt was verified empty; independent X11 sampling saw W up after return; MAP01 position changed by at least 0.1; and typed effect verification succeeded. Each arm's raw record is retained in its packet folder. Each completed arm performed one W-forward action and no model/provider/MCP request.

| Pair | Seed | Direct ms | Compiled ms | Compiled minus direct | Relative |
|---|---:|---:|---:|---:|---:|
| 1 | 2026102911 | 878.531 | 917.773 | +39.242 | +4.47% |
| 2 | 2026102912 | 877.522 | 901.309 | +23.787 | +2.71% |
| 5 | 2026102915 | 875.774 | 926.2 | +50.426 | +5.76% |
| 6 | 2026102916 | 881.691 | 929.319 | +47.628 | +5.4% |
| 9 | 2026102919 | 878.062 | 930.878 | +52.816 | +6.02% |
| 10 | 2026102920 | 873.656 | 925.926 | +52.27 | +5.98% |

Across these six pairs, median direct route latency is **877.792 ms** and median compiled route latency is **926.063 ms**. Median paired difference is **+49.027 ms**, mean paired difference is **+44.362 ms**, and median relative paired difference is **+5.58%**. Compiled was slower in all six pairs.

Timing covers fresh in-path observation through typed task-effect verification, including the 600 ms W hold, guarded dispatch, one post-release ViZDoom synchronization tick, and position/effect readback. It excludes startup and alias mint/preflight. Seeds 2026102911/12 are R10; 2026102915/16 are R12; 2026102919/20 are R14. R14's Docker commands returned exit 0 for all four arms. R12's four arm JSON results passed but Docker returned exit 2 because its shell wrapper had CRLF; R11 and R13 are separate pre-input launch failures and are not included as timing observations. No successful arm was repeated and no failed arm was replayed.

This is a small, one-action, local descriptive comparison. It is not a robust speed or reliability estimate, general product efficiency result, model/token-cost comparison, blocked-I/O recovery test, MAP01-completion result, or Windows/WSLc evidence. Runtime is Docker Desktop Linux Engine, Xvfb, ViZDoom 1.3 and FreeDoom MAP01 only.

Raw evidence: docker_vizdoom_x11_caller_efficiency_20261028_r10/, ..._r12/, ..._r14/. Failed harness packets: ..._r11/ (missing python executable) and ..._r13/ (stdout-directory collision). All are retained without replay.
