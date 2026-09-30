# T1 invocation ledger

- Frozen commit: `0ba178b573e7e55f60cd929454f02e90513bfa85`.
- Runtime: CPython 3.14.5, macOS arm64 host CPU.
- Frozen construction suite: `python3 -m unittest discover -s research/analysis/max_permissive_supervisor_5550_t1_observability_20261001 -p 'test_*.py' -v` — 6/6 passed.
- Candidate: `python3 research/analysis/max_permissive_supervisor_5550_t1_observability_20261001/candidate.py` — one invocation, exit 0; stdout retained at `raw/formal-01.json`.
- Independent raw-only audit: `python3 research/analysis/max_permissive_supervisor_5550_t1_observability_20261001/audit.py research/analysis/max_permissive_supervisor_5550_t1_observability_20261001/raw/formal-01.json` — one invocation, exit 0; stdout retained at `raw/audit-01.json`.
- Candidate enabled `REVALIDATE` only; audit disposition `PASS_T1_SYNTHETIC_SCOPE`, errors `[]`, corruption controls rejected 4/4.
- No candidate/audit retry; no container or shared-lane use.

## Construction chronology clarification

The same six unit tests were invoked once during pre-freeze development and
once against the frozen source. Only the frozen 6/6 invocation is counted as
the preregistered gate. No candidate output or independent audit was generated
before the frozen commit; candidate and audit each ran exactly once afterward.
