# Issue #59 local Docker construction allocation 01

## H / T / D / C / U

- **H:** Loading the frozen recovery-guard module with an explicit __file__ and normal module registration lets its predicate be evaluated on the four predeclared typed-evidence cases; an independent raw-only auditor rejects altered decisions, inputs, row inventory and protocol identity.
- **T:** Import the exact research/doom/recovery protocol bytes from the pinned main blob. Evaluate fresh-stable, stale-sequence, unavailable-health and health-loss cases. Also check the existing recovery-step shape, 250 ms total hold, fresh deadline and stale-source rejection. Candidate and independent auditor each run once in separate local Docker containers.
- **D:** PASS_HOST_GUARD_CONSTRUCTION only if the protocol Git blob is exactly f5caf71a743a563b7de046b82d44db7ebe49e829, all four decisions match the frozen oracle, construction invariants match, raw replay has zero errors, and all five auditor mutations reject. Preserve source/fixture/candidate/auditor hashes, raw/audit bytes and Docker execution receipts.
- **C:** Four deterministic synthetic cases carried forward from the retained host allocation's declared predicate contract; standard-library behavior, fixed image/resources, network disabled and read-only source/root filesystem. The prior allocation 04 STOP remains unchanged and is not rerun.
- **U:** Predicate-level construction only. No input, X11, game, model, live health stream, task progress, survival, cancellation timing, or integration behavior is measured. This does not grant or substitute for the still-unassigned live T1 under #59/#5085.

## Run boundary

Allocation: MAP01-RECOVERY-GUARD-DOCKER-CONSTRUCTION-20261001-01  
Base main: 8bbf3211cb10e0606c4ca13d6fb15b55f3895ad5  
Image: python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f  
Platform/resources: local Docker Desktop linux/amd64; network none; 1 CPU, 256 MiB, pids 64.  
Policy: freeze before execution; candidate once; auditor once only if candidate exits 0; no retry or result-dependent edit.

The import harness sets module.__file__, registers the module in sys.modules, and compiles the frozen bytes. This is a new harness/allocation to evaluate the predicate after allocation 04 stopped before any predicate call. It does not alter allocation 04's source, STOP, or outcome.
