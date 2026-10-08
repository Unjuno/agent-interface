# MAP01 adjudicator JSON boundary — host construction result

Disposition: **`PASS_HOST_JSON_BOUNDARY_AUDITED`**. This is a synthetic,
host-only construction result. It is not the separately gated Docker formal
allocation, not live MAP01 evidence, and does not close Issue #59.

## H / T / D / C / U

- **H:** The current-main paired adjudicator rejects malformed Python/JSON
  scalar types and invalid row cardinality after wire serialization. A separate
  raw-only auditor can verify the exact serialized inputs, decisions, and
  source identity without importing candidate adjudication code.
- **T:** At main `10ed6d4c43f387830765b028a520d2f127827c56`, froze the plan,
  fixture, candidate, auditor, tests, and upstream adjudicator. Ran the focused
  construction tests before freeze (2 passed). Executed the host candidate
  once on one valid six-row input and eight one-field malformed inputs; every
  input was serialized as sorted compact JSON and parsed before adjudication.
  After candidate exit 0, ran the independent raw-only auditor once.
- **D:** Candidate: exit 0, 9 rows retained. The valid fixture returned
  `PASS_INSTRUMENTATION_AND_RELEASE` with comparative `UNCERTAIN`. All eight
  malformed rows returned `STOP_INTEGRITY` with the exact expected reasons:
  `integer:pair_or_order` (pair_id bool, session_order bool), `ready_time`,
  `boolean:map_exit`, `integer:kill_count_gain`,
  `integer:audit_error_count`, `identity_format:fixture_sha256`, and
  `session_count`. The independent auditor returned exit 0, `errors=[]`,
  `source_errors=[]`; all four re-sealed raw mutation controls (omitted,
  duplicate, forged decision, altered bound identity) were rejected.
- **C:** CPython 3.14.5, standard library only. No Docker/OrbStack invocation,
  shared execution slot, game, X11, GUI, model, GPU, network call, input, or
  external effect. Candidate and auditor ran as separate processes.
- **U:** No transport parser or real MAP01 run was exercised. The positive
  fixture is instrumentation-valid only and comparative outcome remains
  `UNCERTAIN`; there is no evidence about threat exposure, safety, recovery
  efficacy, live task effect, latency, or runtime/product readiness.

## Reproduction

From this directory, with the upstream adjudicator at the frozen relative path:

```sh
python3 -B -m unittest -v test_boundary.py
python3 -B candidate.py
python3 -B audit.py
```

The test suite must run before freeze. For the retained allocation, candidate
and auditor were each invoked exactly once. Do not rerun this retained output.
Candidate stdout is retained in `results/construction-01/RUN.json`; the exact
canonical input strings, parsed rows, and candidate outputs are in `RAW.json`.
The separate audit receipt is `AUDIT.json`.

## Integrity

- Frozen upstream adjudicator SHA-256:
  `c09e2c98cbc99fbdf67b6a4be33cca07a77fd8756951b5bb539ab5dbd575ab52`
- Raw bundle SHA-256:
  `8d78e5fc8f5df2aea7aa2f7e33caf35002477d0f83ba983909d91c91c8f45c7c`
- Exact freeze, candidate, auditor, plan, fixture, and test hashes are in
  `FREEZE.json` and `SHA256SUMS`.

The earlier shared Docker T0 remains `STOP_RESOURCE_COORDINATION`; this host
successor neither adopts its conflicting freezes nor changes its disposition.
It advances only the adjudicator's deterministic JSON-boundary construction
and audit evidence. The main research question remains the bounded, live
threat-exposure experiment required by Issue #59.
