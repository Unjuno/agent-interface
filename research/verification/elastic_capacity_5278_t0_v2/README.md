# Issue #5278 — elastic verifier capacity, T0 successor allocation -02

## Preservation and delta

This is an additive current-main continuation of the construction-only STOP in [#5278](https://github.com/Unjuno/agent-interface/issues/5278). The predecessor branch and its STOP are unchanged. The exact old STOP is copied to `evidence/prior-construction01-STOP.txt`. Simulator, auditor, and workload inputs are byte-for-byte copies of the predecessor. The only source correction is in `test_model.py`: import the provided auditor module as `audit`, not the nonexistent `auditor`.

Allocation: `elastic-verifier-capacity-5278-t0-20260930-02`  
Intake main: `eddcf7a47c1f3c47165288037e66f66da0c3138a`  
Branch: `research/elastic-verifier-capacity-5278-t0-20260930-r2`

## H / T / D / C / U

**H.** Under one fixed maximum of four workers, a deadline/freshness-aware elastic policy can improve usable-before-deadline results over a one-worker fixed pool during bursts while using materially fewer idle worker-ms than a four-worker fixed pool, without changing result semantics or allowing missing mandatory checks to PASS.

**T.** Run the unchanged deterministic synthetic T0 workload: seven directed regimes (steady low load, short burst, sustained burst, stale-version burst, startup-too-late, mixed mandatory/optional work, and scale-in with another worker active), 51 fixed jobs, and three policies: `FIXED_SMALL=1`, `FIXED_LARGE=4`, and `ELASTIC_DEADLINE_FRESHNESS_AWARE=1..4`. One verifier/version, startup 300 ms, teardown 150 ms, idle retirement 600 ms, 1 ms simulation tick, maximum four workers. Construction ran on Windows / CPython 3.12.10; eight named tests passed. Formal command is one invocation of `python simulator.py` with `RAW_OUT` set to the previously absent `evidence/formal01/raw.json`. Only if that exits 0, run `python audit.py` as a separate process with `RAW_PATH` pointing to that file. No retry, tuning, model, GUI, task input, GPU, package installation, or external service.

**D.** Scoped PASS requires: elastic completes more short-burst jobs before deadline than FIXED_SMALL; summed elastic idle worker-ms for short+sustained bursts is at most 75% of FIXED_LARGE; peak workers <=4; identical semantic digests across policies for completed results; no stale work completes and incomplete mandatory work never yields PASS; independent audit errors=0 and all five frozen corruptions rejected. Partial endpoints receive the corresponding HOLD/FAIL subtype. Any source/output/audit integrity failure is STOP. A T0 outcome does not authorize T1.

**C.** Directed synthetic jobs and a deterministic scheduler do not model real service-time distributions, contention, batching, RAM/VRAM, or startup variance. Fixed profiles may favor or disadvantage elasticity; a single resident worker may be simpler.

**U.** One finite synthetic T0 only. No real verifier backend, hardware/energy benchmark, production scheduler, Verification Orchestra integration, action authority, or general policy claim.

## Execution and environment

This T0 is explicitly a standard-library local simulation and does not request the shared Docker/GPU lane. Docker Desktop was checked read-only; its current empty inventory is not treated as a lease. No container was run, and no shared container was inspected or changed.

Construction: `python -m unittest discover -s . -p test_model.py -v` — 8/8 pass on CPython 3.12.10.  
Formal: `python simulator.py` with `RAW_OUT=<absolute absent evidence/formal01/raw.json>`.  
Audit, in a fresh process after runner exit 0: `python audit.py` with `RAW_PATH=<absolute evidence/formal01/raw.json>`.

`FREEZE.json` pins the source Git blob IDs and SHA-256 digests of canonical Git blob bytes, workload, commands, base main and construction result. Formal output and the independent audit will be added only after exact source readback and one-shot execution.
