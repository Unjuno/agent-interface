# Combined descriptive timing update: R10 + R12

R12 adds two fresh counterbalanced pairs to R10. Across the four pairs (pairs 1, 2, 5, 6; four direct and four compiled arms), all eight task-effect and input-release gates passed. Each arm independently observed W down during the action, a verified release receipt with no held keys/buttons, independent W-up after return, and position change above the 0.1 threshold. One pair's compiled arm moved +127.54 map units; the other seven arms moved +122.63. No failed execution arm was repeated or pooled.

| Pair | Seed | Direct ms | Compiled ms | Compiled minus direct | Relative |
|---|---:|---:|---:|---:|---:|
| 1 | 2026102911 | 878.531 | 917.773 | +39.242 | +4.47% |
| 2 | 2026102912 | 877.522 | 901.309 | +23.787 | +2.71% |
| 5 | 2026102915 | 875.774 | 926.200 | +50.426 | +5.76% |
| 6 | 2026102916 | 881.691 | 929.319 | +47.628 | +5.40% |

Across these four matched pairs, median direct latency is 878.026 ms; median compiled latency is 921.986 ms. Median paired difference is +43.435 ms (compiled slower); mean paired difference is +40.271 ms. Median paired relative difference is +4.934%. This is a small descriptive sample and does not support a general speed, reliability, or statistical claim. Both R10 and R12 include in-path observation, the 600 ms hold, guarded dispatch, one post-release ViZDoom synchronization tick, and typed task-effect verification; startup and alias mint/preflight are excluded. There is no model/provider/MCP/token/billing accounting.

R11 is a separate four-arm launch failure: the pinned image had `python3` but not `python`. Its failed attempts did not reach ViZDoom or issue input and are preserved separately in `docker_vizdoom_x11_caller_efficiency_20261028_r11/`. R12 explicitly used `python3` and all four JSON arm results passed. The Docker wrapper still exited 2 after each passing arm because the mounted PowerShell-created shell file retained CRLF and Bash read a carriage return in `exit "$status"`; raw arm results are retained and the matrix preserves both Python gate result and Docker CLI exit. No trial was retried. This wrapper cleanup defect does not alter the already written arm result JSON but is retained as a harness packaging failure.

Scope remains Docker Desktop Linux Engine + Xvfb + ViZDoom 1.3 / FreeDoom MAP01 only. No Windows, WSLc, blocked-I/O recovery, MAP01 completion, production model usage, or product-level end-to-end efficiency result is established.


