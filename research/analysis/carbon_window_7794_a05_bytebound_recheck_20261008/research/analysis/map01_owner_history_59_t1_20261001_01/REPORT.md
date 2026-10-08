# Result: workflow-owner history T1 (method-scoped)

Disposition: **`PASS_METHOD_SCOPED`**. This is a host-local offline synthetic
test, not a live GitHub/API/Actions result and not a MAP01 control result.

## H / T / D / C / U

- **H:** An all-events, paginated workflow-path history collector can expose
  the prior cross-event owner, while refusing ambiguous or incomplete views.
- **T:** On frozen main `73235730af05375fddf3a9d102d30632e7d43af5`, the candidate
  consumed the two frozen synthetic pages once. The separate raw-only audit
  read the fixture and candidate JSON and independently reconstructed expected
  rows/owner without importing candidate or production selector code.
- **D:** Candidate exit 0; 4 fixture rows across 2 pages; earliest matching
  workflow-path run `91001` (`push`, run 41) owned the synthetic allocation;
  later current run `91002` (`workflow_dispatch`, run 42) was denied with
  `FAIL_ALLOCATION_ALREADY_OWNED`; no event query parameter was built. Auditor
  exit 0, `PASS_METHOD_SCOPED`, zero candidate discrepancies. All 5/5 raw
  corruption controls were rejected. Construction suite: 7/7; Python compile
  and `git diff --check`: pass. Candidate/auditor/retry counts: 1/1/0.
- **C:** Fixture pages are deterministic and supplied locally. The run did not
  call GitHub, so it cannot validate endpoint ordering, pagination stability,
  concurrent insertion behavior, API response shape, or Actions concurrency.
  The workflow source still contains its event filter; this package does not
  patch or authorize a live workflow.
- **U:** The live allocation-global gate remains open. No real run overlap,
  duplicate formal execution, MAP01 effect, safety, efficacy, or gameplay
  conclusion is claimed. Any workflow integration requires a separately
  reviewed, non-dispatching change and a new live-allocation decision.

## Execution record

Candidate command:

```text
python -B research/analysis/map01_owner_history_59_t1_20261001_01/candidate.py research/analysis/map01_owner_history_59_t1_20261001_01/fixtures/full-history.json --out research/analysis/map01_owner_history_59_t1_20261001_01/results/t1-01/candidate.json
```

Independent audit command:

```text
python -B research/analysis/map01_owner_history_59_t1_20261001_01/audit.py research/analysis/map01_owner_history_59_t1_20261001_01/fixtures/full-history.json research/analysis/map01_owner_history_59_t1_20261001_01/results/t1-01/candidate.json --out research/analysis/map01_owner_history_59_t1_20261001_01/results/t1-01/audit.json
```

Host: Windows, CPython 3.11.9. No network/API, workflow dispatch, container,
WSL, CUDA/GPU, model, game, GUI, or input operation. The main source pins and
all package artifact hashes are in `FREEZE.json` and `SHA256SUMS`.
