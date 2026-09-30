# Issue #5278 — elastic verifier capacity, T0

Allocation: \`elastic-verifier-capacity-5278-t0-20260930-01\`.
Base main: \`6cd858858f0909cab5357de054404792a0148910\`.
Scope: this additive directory only. No shared runtime, #5139 GPU lane, Docker daemon, model, GUI or external service is used. The experiment is a deterministic synthetic T0 expressly permitted by #5278; it does not consume a live CPU/Docker slot.

## H / T / D / C / U

**H.** Under one fixed maximum of four workers, a deadline/freshness-aware elastic policy can improve usable-before-deadline results over a one-worker fixed pool during bursts while using materially fewer idle worker-ms than a four-worker fixed pool, without changing result semantics or allowing missing mandatory checks to PASS.

**T.** Seven preregistered finite workloads in \`workloads.json\`: steady low load, short burst, sustained burst, stale-version burst, startup-too-late, mixed mandatory/optional work, and scale-in while another worker remains active. Every arm receives identical job bytes, version requirements, service durations, criticality and absolute deadlines. Compare \`FIXED_SMALL=1\`, \`FIXED_LARGE=4\`, and \`ELASTIC_DEADLINE_FRESHNESS_AWARE=1..4\`. One verifier/version, startup 300 ms, teardown 150 ms, idle retirement 600 ms, 1 ms discrete simulation tick; maximum worker envelope 4. All work is synthetic, with no random seeds or post-result tuning.

**D.** \`PASS_ELASTIC_CAPACITY_T0_SCOPED\` requires (1) elastic completes more short-burst jobs before deadline than FIXED_SMALL; (2) summed elastic idle worker-ms for short+sustained bursts is <=75% of FIXED_LARGE; (3) peak workers never exceeds 4; (4) completed rows have identical semantic digests across arms; (5) stale work never completes, incomplete mandatory work never yields PASS; (6) independent raw audit has zero errors and rejects all five frozen corruptions. If only some endpoints pass, report the observed HOLD/FAIL subtype; provenance/audit failure is STOP. No outcome permits a T1 live verifier run.

**C.** The workload is directed and synthetic; the deterministic priority scheduler, optimistic feasibility estimate, millisecond tick, and fixed startup/service profiles may make the result favorable or unfavorable to this policy. A batching or single resident worker may be simpler. This model does not measure contention or actual RAM/VRAM.

**U.** One synthetic finite T0 only. No real verifier backend, model, hardware benchmark, energy, contention, production scheduler, Verification Orchestra integration, action authority, or general policy claim.

## Inputs, output contract, and execution

\`workloads.json\` fixes all 51 jobs, SHA-256 payload identities, seven invalidation/deadline regimes and the capacity/timing envelope. Results contain per-job status, semantic digest, attempt trace, worker lifecycle, capacity transitions and conserved worker/busy/idle time. A missing mandatory result maps to UNCERTAIN; PASS is possible only when every mandatory case result is current and timely. Replica count never grants authority.

Candidate: \`simulator.py\`. Independent auditor: \`audit.py\`, which imports no candidate code and reconstructs status/semantic digests, lifecycle/resource accounting, deadline/freshness compliance, max concurrency, cross-policy outputs, and the fail-closed plan outcome from frozen inputs plus the retained raw trace. \`test_model.py\` is a construction suite, not an extra formal allocation.

Formal T0 command after this exact branch/source/workload freeze and a collision-free output path:
\`python simulator.py\` with \`RAW_OUT=<absent path>\`.
Then launch a separate Python process: \`python audit.py\` with \`RAW_PATH=<raw result>\`. It also executes the five frozen corruption controls. No retry or parameter adjustment is permitted after formal invocation. All commands use the host's local standard-library Python; no network access or package installation is needed.

## Freeze record

Branch: \`research/elastic-verifier-capacity-5278-t0-20260930\`.
A pre-execution Issue comment records the exact commit, source hashes, workload hash, Python version, output collision check, test results and T0 invocation count=0. Formal output and independent audit are appended additively under \`evidence/formal01/\`.

Roadmap: frozen input/source -> CPU-only construction tests -> one synthetic T0 -> separate raw audit + five corruptions -> evidence readback -> Draft PR and exact-head CI/review. This T0 cannot close #5278's T1, parent #5267, or global roadmap.
