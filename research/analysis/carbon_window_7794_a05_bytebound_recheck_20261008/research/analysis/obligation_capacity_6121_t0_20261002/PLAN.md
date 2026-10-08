# Issue #6121 T0 — finite obligation-capacity method test

Status: preregistration only until `FREEZE.json` is committed and read back.

## H / T / D / C / U

**H.** Under the same finite offered task mix and two one-slot service resources, a class-aware gate can cap soft obligation backlog while retaining more independently verified read-only work than global wait. A transfer or timeout must never reduce system-wide outstanding obligations; missing effect evidence is not discharge.

**T.** Run `python candidate.py fixture.json candidate.jsonl` once on the frozen finite fixture, then (only after candidate exit 0) `python audit.py fixture.json candidate.jsonl audit.json` once in a separate process. This is T0 only: no model, GPU, GUI, application, external input, or live effect. Four admission arms: LEDGER_ONLY, GLOBAL_WAIT, FIXED_CAP, CLASS_AWARE. Two service resources: owner-side release and independent effect oracle, one slot each per tick. Cases include below-capacity, burst/near-capacity and held-out arrivals, overload with a mandatory held-input release, an unavailable oracle, a failed compensation that creates a child, transferred ownership with a stale receipt and timeout, and an unknown service footprint.

**D.** `METHOD_PASS_SCOPED` only if the independent audit reproduces every finite ledger/accounting summary; five corruptions are rejected; transfer and timeout preserve the global outstanding count; stale-generation evidence cannot discharge; mandatory release is serviced ahead of discretionary work; unresolved/oracle-gap cases are never labeled feasible; and on the three preregistered congested-but-drainable paths (`near_burst`, `burst_then_drain`, `heldout_alternating`) CLASS_AWARE has strictly higher `utility = useful_completions - backlog_area/2 - max_open_age/4` than both LEDGER_ONLY and GLOBAL_WAIT, while also reducing max backlog and backlog area versus LEDGER_ONLY. Below-capacity equality is an acceptable null. Otherwise retain `FAIL_METHOD` or `HOLD` exactly; no repair/retry.

**C.** Same finite arrivals, two fixed service slots, one obligation schema, four policies, exact useful-completion predicate, and no outcome-dependent changes. LEDGER_ONLY is the conservation baseline; GLOBAL_WAIT is the safety-conservative baseline; FIXED_CAP is a count-only control. Read-only work has no effect/release obligation and is explicitly distinguishable from effectful task completion.

**U.** This cannot estimate real arrival/service rates, rare tails, production stability, severity-weighted obligations, human escalation quality, or GUI/model outcomes. A synthetic method PASS is not an operational policy recommendation.

## Execution boundary

Source anchor: README `f8cf85390eda4c6d26ceaf8e7df995e8132e504c`; CURRENT_GOAL `dd6d691331bd602f97d9aa0e3f52fc6202b06525` (r133); ROADMAP `c322beb5fc2a9f6217dd3cc6205b9cbf05e84c19`; current main at preparation freeze `981ba1ee20259ff36465d25aceef62fd3554a7e9`. Issue #6121 is open and its sole refinement requires transfer-as-false-discharge corruption coverage. No #6121 branch or PR was found; no active parallel research thread claimed this Issue.

Docker Desktop service is Stopped/Manual and its read-only container inventory timed out after 6 s. Starting `archlinux` WSL returned `Wsl/Service/CreateInstance/E_FAIL`. Therefore this T0 uses host CPython 3.11.9 only, with no container/WSL isolation claim. It does not touch shared Docker/OrbStack containers or consume a GPU/Docker lease. Candidate and auditor each run once; retries 0. All files are local/synthetic; network disabled by omission.

