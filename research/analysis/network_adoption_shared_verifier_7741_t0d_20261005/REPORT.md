# Issue #7741 T0d result — scoped synthetic spillover sensitivity

## Disposition

`PASS_METHOD_SCOPED`. The frozen protocol's exact gate passed: the candidate and independent raw-only auditor each ran once and exited 0; all 256 condition groups replayed with zero audit/accounting errors; all 32 of 32 fresh topology × imitation × seed cells met the seed-level criterion; and both exact-null controls had zero p95 differences in every cell. This result remains a deterministic synthetic mechanism study and has no empirical or production interpretation.

## Preregistered question and contrast

T0c was retained as `METHOD_FAIL_OR_INCONCLUSIVE`: although its shared-one-server peer-vs-frozen p95 reversed in 16/16 cells, its per-principal comparator also had 11/16 positive differences. T0d therefore compares the matched peer-minus-frozen p95 change under one shared server with the same change under per-principal queues. A seed qualifies only when the shared-server change is positive, the difference-in-differences is at least 3 ticks (the modeled service duration), and unfinished obligations increase. The gate requires at least 6/8 qualifying fresh seeds in each of two topologies and two imitation values. No parameter or threshold was added after the formal run.

## Results

Across the 32 fresh cells, shared-one-server peer-minus-frozen p95 change (`d_shared`) ranged from 97 to 129 ticks (mean 117.47); the per-principal local change (`d_local`) ranged from -4 to +4 ticks (mean 1.06). The preregistered difference-in-differences ranged from 94 to 128 ticks (median 119, mean 116.41), well above the 3-tick threshold in all cells. Shared-server unfinished obligations increased by 469 to 768 tasks (mean 639.88) against the matched frozen condition in the same cells.

All cells passed independently: ring/imitation .08, 8/8; ring/.20, 8/8; star/.08, 8/8; star/.20, 8/8. No-imitation peer-vs-frozen p95 differences were exactly zero in all 32 cells; shared-24-server peer-vs-frozen p95 differences were also exactly zero in all 32 cells. The per-principal comparator was not required to be zero; its paired changes were reported and subtracted in the primary contrast.

## Execution and evidence

The allocation was preregistered on Issue #7741 in comment [#5993585154](https://github.com/Unjuno/agent-interface/issues/7741#issuecomment-5993585154) before the candidate run. Frozen protocol/source hashes and the no-retry rule are in `FREEZE.json` and `SHA256SUMS`. Construction checks passed before execution. `formal_01/RUN.json` records exactly one candidate and one auditor invocation, both exit 0. The raw candidate stream is retained as `formal_01/RAW.json.gz` (51,588,204 compressed bytes); its uncompressed SHA-256 matches the candidate stdout receipt. Candidate and auditor stderr were captured separately and are empty. Independent audit summary and per-cell differences are in `formal_01/AUDIT.json`; detailed output and invocation receipts are retained in the same directory.

The independent auditor replays adoption transitions, every principal-tick opportunity, arrivals, service starts, completions and unfinished work without importing candidate code. The pre-run construction suite also rejects five frozen event-log mutations. T0/T0b/T0c packages and dispositions were not modified.

## Scope and limitations

All entities, peer relations, adoption draws, task-start probabilities, costs and capacities are synthetic and uncalibrated. The threshold is in model ticks. The result demonstrates that this specific deterministic mechanism produces a large incremental shared-queue effect over its per-principal local comparator under the frozen grid. It does not establish real adoption cascades, empirical queue effects, workload elasticity, suitable production capacity, runtime performance, user impact, safety, or generality beyond this model. No host timing, container isolation, or resource enforcement was tested or inferred.
