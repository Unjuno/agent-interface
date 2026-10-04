# Issue #7161 — event-centric object memory T0

## H / T / D / C / U

**H:** An append-only typed event sequence distinguishes action histories that share the same final visual state, without converting a prediction into an observed effect or granting input authority.

**T:** Frozen at `main` `8ff7afed76c1d81eabac9d0c37d4191b352045a4`. Generate five deterministic histories ending at the same `dialog_closed` visual state: not run, dispatched/pending, observed success, observed success then reversion, and observed failure. Run the candidate once and an independent raw-only auditor once; test three isolated output mutations.

**D:** `PASS_METHOD_SCOPED` only if all five typed dispositions match the event receipts, predicted and observed values remain separate, every observation has a receipt source, input authority remains false in every case, and all three mutations are rejected.

**C:** The hand-authored finite traces are deliberately simple. The candidate uses a fixed projection, not a learned retrieval or event-memory system; this does not establish improved task continuation or recovery over a capable resumption packet.

**U:** Synthetic records only. No GUI, model, user, real action/effect, runtime integration, memory/latency benefit, or product claim. A final visual state alone cannot identify the preceding causal history.

## Result

Candidate and independent audit returned `PASS_METHOD_SCOPED`: five cases verified; three of three tamper controls rejected; zero cases carry input authority. Exact outputs, commands, and hashes are retained in this directory.

Execution used Ubuntu WSL (`Python 3.12.3`) on the Windows host CPU. `wslc info` responded and reported WSLc 3.0.1, but both `wslc list` and an isolated `wslc run` remained unanswered after 30 seconds. Only those agent-started CLI requests were interrupted; no other process or container was stopped. Consequently this run is not represented as a WSLc/container run. Docker CLI was absent from the active PowerShell PATH. This is a bounded construction T0 and claims no container equivalence or resource measurement.

T1 requires history-dependent GUI tasks, matched against final-state-only and ordinary typed resumption, with independent effect verification and no duplicate irreversible actions.
